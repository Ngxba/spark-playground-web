from fastapi import APIRouter, HTTPException
from typing import List
from app.models import Puzzle, PuzzleMetadata, RunRequest, RunResult
from app.services import Judge, PuzzleLoader

router = APIRouter()

# Initialize services
puzzle_loader = PuzzleLoader()
judge = Judge()

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

@router.post("/puzzles/{puzzle_id}/run", response_model=RunResult)
async def run_puzzle(puzzle_id: str, request: RunRequest):
    """
    Execute user code for a puzzle and return evaluation results
    """
    # Get the puzzle
    puzzle = puzzle_loader.get_puzzle(puzzle_id)
    if not puzzle:
        raise HTTPException(status_code=404, detail=f"Puzzle '{puzzle_id}' not found")

    # Evaluate the code
    try:
        result = judge.evaluate(
            puzzle_id=puzzle_id,
            code=request.code,
            input_data=puzzle.initial_data,
            expected_output=puzzle.expected_output
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating code: {str(e)}"
        )
