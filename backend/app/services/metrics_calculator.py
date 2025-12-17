from typing import Dict
from app.models import MetricsResult

class MetricsCalculator:
    """Simulates Spark metrics based on detected operations"""

    @staticmethod
    def calculate(analysis: Dict, execution_time: float = 0.0) -> MetricsResult:
        """
        Calculate simulated metrics based on operation analysis

        Args:
            analysis: Result from OperationDetector.analyze()
            execution_time: Actual execution time (used as base)

        Returns:
            MetricsResult with simulated metrics
        """
        operations = analysis['operations']

        # Calculate shuffles
        shuffles = 0
        if analysis['has_groupby']:
            shuffles += 1
        if analysis['has_join'] and not analysis['has_broadcast']:
            shuffles += 1
        if 'sort' in operations:
            shuffles += 1

        # Calculate stages (roughly: 1 base + 1 per shuffle + extra for complex operations)
        stages = 1 + shuffles
        if analysis['has_aggregation']:
            stages += 1

        # Simulate execution time
        base_time = 1.0  # Base time in seconds
        time_simulated = base_time

        # Add time for each operation type
        if analysis['has_groupby']:
            time_simulated += 2.0
        if analysis['has_join']:
            if analysis['has_broadcast']:
                time_simulated += 1.0  # Broadcast join is faster
            else:
                time_simulated += 3.0  # Shuffle join is slower
        if 'sort' in operations:
            time_simulated += 2.0
        if analysis['filter_after_join']:
            time_simulated += 1.5  # Penalty for inefficient filter placement
        if analysis['has_reuse_without_cache']:
            time_simulated *= 1.8  # Penalty for recomputation
        if analysis['has_cache']:
            time_simulated *= 0.7  # Benefit from caching

        # Detect skew (simplified - based on groupby without salting)
        skew_detected = analysis['has_groupby'] and len(operations) > 2
        if skew_detected:
            time_simulated *= 1.3

        return MetricsResult(
            time_simulated=round(time_simulated, 2),
            shuffles=shuffles,
            stages=stages,
            skew_detected=skew_detected,
            cache_used=analysis['has_cache'],
            broadcast_used=analysis['has_broadcast']
        )
