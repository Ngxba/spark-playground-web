from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from ..models.db_models import PuzzleRun, RunMetrics, ExecutionData, ExecutionPlan, RunOutput
from ..models.puzzle import RunResult


class RunRepository:
    @staticmethod
    def save_run(db: Session, puzzle_id: str, user_code: str, result: RunResult) -> PuzzleRun:
        """Save a complete run with all related data"""
        # Create main run record
        run = PuzzleRun(
            puzzle_id=puzzle_id,
            user_code=user_code,
            is_correct=result.correct,
            stars=result.stars,
            error_message=result.error,
            execution_log=result.execution_log,
            hint=result.hint
        )
        db.add(run)
        db.flush()  # Get run.id

        # Save metrics
        if result.metrics:
            metrics = RunMetrics(
                run_id=run.id,
                time_simulated=result.metrics.time_simulated,
                shuffles=result.metrics.shuffles,
                stages=result.metrics.stages,
                skew_detected=result.metrics.skew_detected,
                cache_used=result.metrics.cache_used,
                broadcast_used=result.metrics.broadcast_used
            )
            db.add(metrics)

        # Save execution data
        execution_data = ExecutionData(
            run_id=run.id,
            execution_simulation_json=result.execution_simulation.dict() if result.execution_simulation else None,
            stage_flow_json=result.stage_flow,
            cluster_config_json=result.cluster_config,
            dag_structure_json=result.dag_structure,
            executors_info_json=[executor.dict() for executor in result.executors_info] if result.executors_info else None
        )
        db.add(execution_data)

        # Save execution plan
        execution_plan = ExecutionPlan(
            run_id=run.id,
            physical_plan=result.physical_plan,
            logical_plan=result.logical_plan,
            spark_ui_url=result.spark_ui_url
        )
        db.add(execution_plan)

        # Save output data
        output_data = RunOutput(
            run_id=run.id,
            output_data_json=result.output,
            expected_output_json=result.expected_output
        )
        db.add(output_data)

        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def get_run_by_id(db: Session, run_id: UUID) -> Optional[PuzzleRun]:
        """Get a single run with all related data"""
        return db.query(PuzzleRun).filter(PuzzleRun.id == run_id).first()

    @staticmethod
    def get_runs_by_puzzle(db: Session, puzzle_id: str, limit: int = 50, offset: int = 0) -> List[PuzzleRun]:
        """Get all runs for a specific puzzle"""
        return (
            db.query(PuzzleRun)
            .filter(PuzzleRun.puzzle_id == puzzle_id)
            .order_by(PuzzleRun.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def get_all_runs(db: Session, limit: int = 50, offset: int = 0) -> List[PuzzleRun]:
        """Get all runs with pagination"""
        return (
            db.query(PuzzleRun)
            .order_by(PuzzleRun.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
