from typing import Dict, Optional

class HintGenerator:
    """Generates hints based on code analysis and puzzle context"""

    @staticmethod
    def generate_hint(
        puzzle_id: str,
        analysis: Dict,
        is_correct: bool,
        stars: int
    ) -> Optional[str]:
        """
        Generate a hint based on the analysis and result

        Args:
            puzzle_id: ID of the puzzle
            analysis: Result from OperationDetector.analyze()
            is_correct: Whether the solution is correct
            stars: Star rating achieved

        Returns:
            Hint string or None if no hint needed
        """
        # No hint needed for 3-star optimal solutions
        if stars == 3:
            return None

        # If incorrect, provide basic correctness hints
        if not is_correct:
            return "The output doesn't match the expected result. Check your transformation logic."

        # Generate hints based on detected inefficiencies
        hints = []

        # Hint for broadcast join opportunity
        if puzzle_id == "fast_join" and analysis['has_join'] and not analysis['has_broadcast']:
            return "You joined a small and a large dataset without a broadcast. Spark had to shuffle the big dataset. Try using a broadcast pattern - process the small dataset first, or use merge strategies that leverage the size difference."

        # Hint for filter placement
        if analysis['filter_after_join']:
            return "You filtered after the join. Try filtering out unnecessary items before joining to reduce the data processed. This avoids shuffling data that will be discarded anyway."

        # Hint for caching
        if analysis['has_reuse_without_cache']:
            return "You processed the same data twice. Consider caching the dataset after the first use to speed up subsequent operations and avoid recomputation."

        # Hint for groupby operations
        if puzzle_id == "group_fruits" and analysis['has_groupby'] and stars < 3:
            return "Your solution works but could be optimized. Make sure you're grouping efficiently. Consider using aggregation functions if needed."

        # Hint for aggregation
        if puzzle_id == "total_output" and analysis['has_aggregation'] and stars < 3:
            return "Your aggregation is correct but could be more efficient. Ensure you're using the most direct aggregation method for summing values."

        # Generic optimization hint
        if stars == 2:
            return "Your solution is correct but not optimal. Review the number of shuffles and stages - fewer is usually better."

        if stars == 1:
            return "Your solution works but is quite inefficient. Consider: Are you using the right operations? Can you reduce shuffles? Is data filtered early?"

        return None
