from typing import List, Optional
from app.models import Puzzle, PuzzleMetadata
from app.puzzles.puzzle_definitions import ALL_PUZZLES

class PuzzleLoader:
    """Loads and manages puzzle definitions"""

    def __init__(self):
        self.puzzles = {puzzle.id: puzzle for puzzle in ALL_PUZZLES}

    def get_all_metadata(self) -> List[PuzzleMetadata]:
        """Get metadata for all puzzles"""
        return [
            PuzzleMetadata(
                id=puzzle.id,
                title=puzzle.title,
                description=puzzle.description,
                difficulty=puzzle.difficulty,
                tags=puzzle.tags
            )
            for puzzle in self.puzzles.values()
        ]

    def get_puzzle(self, puzzle_id: str) -> Optional[Puzzle]:
        """Get a specific puzzle by ID"""
        return self.puzzles.get(puzzle_id)

    def puzzle_exists(self, puzzle_id: str) -> bool:
        """Check if a puzzle exists"""
        return puzzle_id in self.puzzles
