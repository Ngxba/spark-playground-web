from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.repositories.run_repository import RunRepository
from pydantic import BaseModel, ConfigDict

router = APIRouter()


class RunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    puzzle_id: str
    is_correct: bool
    stars: int
    created_at: str
    error_message: str | None


@router.get("/runs")
async def get_all_runs(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> List[RunSummary]:
    """Get all runs with pagination"""
    runs = RunRepository.get_all_runs(db, limit, offset)
    return [
        RunSummary(
            id=str(run.id),
            puzzle_id=run.puzzle_id,
            is_correct=run.is_correct,
            stars=run.stars or 0,
            created_at=run.created_at.isoformat(),
            error_message=run.error_message
        )
        for run in runs
    ]


@router.get("/puzzles/{puzzle_id}/runs")
async def get_puzzle_runs(
    puzzle_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> List[RunSummary]:
    """Get all runs for a specific puzzle"""
    runs = RunRepository.get_runs_by_puzzle(db, puzzle_id, limit, offset)
    return [
        RunSummary(
            id=str(run.id),
            puzzle_id=run.puzzle_id,
            is_correct=run.is_correct,
            stars=run.stars or 0,
            created_at=run.created_at.isoformat(),
            error_message=run.error_message
        )
        for run in runs
    ]


@router.get("/runs/{run_id}")
async def get_run_detail(
    run_id: UUID,
    db: Session = Depends(get_db)
):
    """Get full details for a specific run"""
    run = RunRepository.get_run_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Truncate output and expected_output for response payload
    PREVIEW_LIMIT = 20
    output = run.output_data.output_data_json if run.output_data else None
    expected_output = run.output_data.expected_output_json if run.output_data else None

    output_total = None
    if isinstance(output, list) and len(output) > PREVIEW_LIMIT:
        output_total = len(output)
        output = output[:PREVIEW_LIMIT]

    expected_output_total = None
    if isinstance(expected_output, list) and len(expected_output) > PREVIEW_LIMIT:
        expected_output_total = len(expected_output)
        expected_output = expected_output[:PREVIEW_LIMIT]

    # Reconstruct RunResult from database
    result = {
        "id": str(run.id),
        "puzzle_id": run.puzzle_id,
        "user_code": run.user_code,
        "correct": run.is_correct,
        "stars": run.stars,
        "error": run.error_message,
        "execution_log": run.execution_log,
        "hint": run.hint,
        "metrics": {
            "time_simulated": run.metrics.time_simulated,
            "shuffles": run.metrics.shuffles,
            "stages": run.metrics.stages,
            "skew_detected": run.metrics.skew_detected,
            "cache_used": run.metrics.cache_used,
            "broadcast_used": run.metrics.broadcast_used
        } if run.metrics else None,
        "execution_simulation": run.execution_data.execution_simulation_json if run.execution_data else None,
        "stage_flow": run.execution_data.stage_flow_json if run.execution_data else None,
        "cluster_config": run.execution_data.cluster_config_json if run.execution_data else None,
        "dag_structure": run.execution_data.dag_structure_json if run.execution_data else None,
        "executors_info": run.execution_data.executors_info_json if run.execution_data else None,
        "physical_plan": run.execution_plan.physical_plan if run.execution_plan else None,
        "logical_plan": run.execution_plan.logical_plan if run.execution_plan else None,
        "spark_ui_url": run.execution_plan.spark_ui_url if run.execution_plan else None,
        "output": output,
        "expected_output": expected_output,
        "created_at": run.created_at.isoformat()
    }

    # Add totals if truncation occurred
    if output_total is not None:
        result["output_total"] = output_total
    if expected_output_total is not None:
        result["expected_output_total"] = expected_output_total

    return result
