from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from app.models import Puzzle, PuzzleMetadata, RunRequest, RunResult
from app.services import Judge, PuzzleLoader
from app.services.judge_v2 import JudgeV2
from app.database import get_db
from app.repositories.run_repository import RunRepository

router = APIRouter()

# Initialize services
puzzle_loader = PuzzleLoader()
judge_v1 = Judge()  # V1 - legacy script-based (deprecated)
judge = JudgeV2()  # V2 - function-based with real event tracking (default)

@router.get("/puzzles", response_model=List[PuzzleMetadata])
async def list_puzzles():
    """Get list of all available puzzles with metadata"""
    return puzzle_loader.get_all_metadata()

@router.get("/puzzles/{puzzle_id}")
async def get_puzzle(puzzle_id: str):
    """Get detailed information about a specific puzzle (truncated for preview)."""
    puzzle = puzzle_loader.get_puzzle(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"Puzzle '{puzzle_id}' not found")

    PREVIEW_LIMIT = 20
    data = puzzle.dict()

    # Truncate initial_data arrays for frontend preview
    initial_data_totals = {}
    for key, value in data.get("initial_data", {}).items():
        if isinstance(value, list) and len(value) > PREVIEW_LIMIT:
            initial_data_totals[key] = len(value)
            data["initial_data"][key] = value[:PREVIEW_LIMIT]
    if initial_data_totals:
        data["initial_data_totals"] = initial_data_totals

    # Truncate expected_output
    if isinstance(data.get("expected_output"), list) and len(data["expected_output"]) > PREVIEW_LIMIT:
        data["expected_output_total"] = len(data["expected_output"])
        data["expected_output"] = data["expected_output"][:PREVIEW_LIMIT]

    return data

@router.post("/puzzles/{puzzle_id}/run")
async def run_puzzle(puzzle_id: str, request: RunRequest, db: Session = Depends(get_db)):
    """
    Execute user code for a puzzle and return evaluation results.

    V2: Function-based submission with real Spark event tracking.

    Usage: Submit code with `def solve(...) -> DataFrame` format.
    Example:
        def solve(fruits):
            return fruits.orderBy('type')
    """
    # Get the puzzle
    puzzle = puzzle_loader.get_puzzle(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"Puzzle '{puzzle_id}' not found")

    # Evaluate the code with V2 judge
    try:
        result = judge.evaluate(
            puzzle_id=puzzle_id,
            code=request.code,
            input_data=puzzle.initial_data,
            expected_output=puzzle.expected_output,
            spark_config=request.spark_config
        )

        # Save to database
        try:
            saved_run = RunRepository.save_run(db, puzzle_id, request.code, result)
            # Add run_id to response
            result_dict = result.dict()
            result_dict["run_id"] = str(saved_run.id)
        except Exception as db_error:
            # Log error but don't fail the request
            print(f"Error saving run to database: {db_error}")
            result_dict = result.dict()

        # Truncate output and expected_output for the response payload
        PREVIEW_LIMIT = 20
        output = result_dict.get("output")
        if isinstance(output, list) and len(output) > PREVIEW_LIMIT:
            result_dict["output_total"] = len(output)
            result_dict["output"] = output[:PREVIEW_LIMIT]

        expected_output = result_dict.get("expected_output")
        if isinstance(expected_output, list) and len(expected_output) > PREVIEW_LIMIT:
            result_dict["expected_output_total"] = len(expected_output)
            result_dict["expected_output"] = expected_output[:PREVIEW_LIMIT]

        return result_dict
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating code: {str(e)}"
        )


@router.post("/puzzles/{puzzle_id}/run-v1", deprecated=True)
async def run_puzzle_v1(puzzle_id: str, request: RunRequest, db: Session = Depends(get_db)):
    """
    [DEPRECATED] Execute user code for a puzzle (V1 - legacy script-based).

    This endpoint is deprecated. Use /run instead with function-based submission.
    """
    # Get the puzzle
    puzzle = puzzle_loader.get_puzzle(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"Puzzle '{puzzle_id}' not found")

    # Evaluate the code with V1 judge (legacy)
    try:
        result = judge_v1.evaluate(
            puzzle_id=puzzle_id,
            code=request.code,
            input_data=puzzle.initial_data,
            expected_output=puzzle.expected_output
        )

        # Save to database
        try:
            saved_run = RunRepository.save_run(db, puzzle_id, request.code, result)
            # Add run_id and version to response
            result_dict = result.dict()
            result_dict["run_id"] = str(saved_run.id)
            result_dict["version"] = "v1"
        except Exception as db_error:
            # Log error but don't fail the request
            print(f"Error saving run to database: {db_error}")
            result_dict = result.dict()
            result_dict["version"] = "v1"

        # Truncate output and expected_output for the response payload
        PREVIEW_LIMIT = 20
        output = result_dict.get("output")
        if isinstance(output, list) and len(output) > PREVIEW_LIMIT:
            result_dict["output_total"] = len(output)
            result_dict["output"] = output[:PREVIEW_LIMIT]

        expected_output = result_dict.get("expected_output")
        if isinstance(expected_output, list) and len(expected_output) > PREVIEW_LIMIT:
            result_dict["expected_output_total"] = len(expected_output)
            result_dict["expected_output"] = expected_output[:PREVIEW_LIMIT]

        return result_dict
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating code (V1): {str(e)}"
        )
