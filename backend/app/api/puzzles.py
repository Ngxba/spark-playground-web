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
judge = Judge()  # V1 - keep for reference
judge_v2 = JudgeV2()  # V2 - function-based with real event tracking

@router.get("/puzzles", response_model=List[PuzzleMetadata])
async def list_puzzles():
    """Get list of all available puzzles with metadata"""
    return puzzle_loader.get_all_metadata()

@router.get("/puzzles/{puzzle_id}", response_model=Puzzle)
async def get_puzzle(puzzle_id: str):
    """Get detailed information about a specific puzzle"""
    puzzle = puzzle_loader.get_puzzle(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"Puzzle '{puzzle_id}' not found")
    return puzzle

@router.post("/puzzles/{puzzle_id}/run")
async def run_puzzle(puzzle_id: str, request: RunRequest, db: Session = Depends(get_db)):
    """
    Execute user code for a puzzle and return evaluation results

    V1: Original script-based submission
    """
    # Get the puzzle
    puzzle = puzzle_loader.get_puzzle(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"Puzzle '{puzzle_id}' not found")

    # Evaluate the code with V1
    try:
        result = judge.evaluate(
            puzzle_id=puzzle_id,
            code=request.code,
            input_data=puzzle.initial_data,
            expected_output=puzzle.expected_output
        )

        # Save to database
        try:
            saved_run = RunRepository.save_run(db, puzzle_id, request.code, result)
            # Add run_id to response
            result_dict = result.dict()
            result_dict["run_id"] = str(saved_run.id)
            return result_dict
        except Exception as db_error:
            # Log error but don't fail the request
            print(f"Error saving run to database: {db_error}")
            return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating code: {str(e)}"
        )

@router.post("/puzzles/{puzzle_id}/run-v2")
async def run_puzzle_v2(puzzle_id: str, request: RunRequest, db: Session = Depends(get_db)):
    """
    Execute user code for a puzzle and return evaluation results (V2 TESTING)

    V2: Function-based submission with real Spark event tracking

    Usage: Submit code with def solve(...) -> DataFrame format
    Example:
        def solve(fruits):
            return fruits.orderBy('type')

    This endpoint is for testing V2 implementation before full migration.
    """
    # Get the puzzle
    puzzle = puzzle_loader.get_puzzle(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"Puzzle '{puzzle_id}' not found")

    # Evaluate the code with V2
    try:
        result = judge_v2.evaluate(
            puzzle_id=puzzle_id,
            code=request.code,
            input_data=puzzle.initial_data,
            expected_output=puzzle.expected_output
        )

        # Save to database with v2 marker
        try:
            saved_run = RunRepository.save_run(db, puzzle_id, request.code, result)
            # Add run_id and v2 flag to response
            result_dict = result.dict()
            result_dict["run_id"] = str(saved_run.id)
            result_dict["version"] = "v2"
            return result_dict
        except Exception as db_error:
            # Log error but don't fail the request
            print(f"Error saving run to database: {db_error}")
            result_dict = result.dict()
            result_dict["version"] = "v2"
            return result_dict
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating code (V2): {str(e)}"
        )
