"""
Recommendation engine for Sankey spec analysis.

Analyzes a SankeySpec and produces optimization recommendations based on:
  - Partition skew detection
  - Broadcast join candidates
  - Partition count tuning
  - Shuffle volume warnings
"""

from typing import List, Dict, Optional

from app.models.sankey import SankeySpec, SankeyStage, SankeyNode, Recommendation


def _format_bytes(b: int) -> str:
    """Format bytes to human-readable string."""
    if b >= 1_073_741_824:
        return f"{b / 1_073_741_824:.1f} GB"
    if b >= 1_048_576:
        return f"{b / 1_048_576:.1f} MB"
    if b >= 1024:
        return f"{b / 1024:.1f} KB"
    return f"{b} B"


class RecommendationEngine:

    def analyze(
        self,
        spec: SankeySpec,
        cluster_info: Optional[Dict] = None,
    ) -> List[Recommendation]:
        """
        Analyze a SankeySpec and return optimization recommendations.

        Args:
            spec: The generated SankeySpec
            cluster_info: Optional dict with num_executors, cores_per_executor, total_cores

        Returns:
            List of Recommendation objects
        """
        results: List[Recommendation] = []

        for stage in spec.stages:
            stage_nodes = [n for n in spec.nodes if n.stageId == stage.id]
            results.extend(self._check_skew(stage, stage_nodes))
            results.extend(self._check_broadcast_candidate(stage))
            results.extend(self._check_partition_count(stage, cluster_info))
            results.extend(self._check_shuffle_volume(stage))

        return results

    def _check_skew(
        self,
        stage: SankeyStage,
        stage_nodes: List[SankeyNode],
    ) -> List[Recommendation]:
        """Check for partition skew in bucket groups."""
        recs = []
        skewed_nodes = [n for n in stage_nodes if n.isSkewed and n.type == 'bucketGroup']

        for node in skewed_nodes:
            ratio = node.metrics.get('skew_ratio', 0)
            recs.append(Recommendation(
                rule="skew_detected",
                severity="warning",
                stageId=stage.id,
                message=f"Partition skew detected in {stage.label}: bucket {node.label} has disproportionate data",
                suggestion="Consider salting the join key or using adaptive query execution (AQE) to handle skew.",
            ))

        return recs

    def _check_broadcast_candidate(
        self,
        stage: SankeyStage,
    ) -> List[Recommendation]:
        """Check if a SortMergeJoin could use broadcast instead."""
        recs = []
        if 'SortMergeJoin' not in stage.joinType:
            return recs

        shuffle_read = stage.metrics.get('shuffleReadBytes', 0)
        # If the total shuffle is small (< 10MB), broadcast might be better
        if 0 < shuffle_read < 10 * 1024 * 1024:
            recs.append(Recommendation(
                rule="broadcast_candidate",
                severity="info",
                stageId=stage.id,
                message=f"Stage '{stage.label}' uses SortMergeJoin but shuffle volume is only {_format_bytes(shuffle_read)}",
                suggestion="Consider using broadcast join (df.hint('broadcast')) for the smaller table to eliminate the shuffle.",
            ))

        return recs

    def _check_partition_count(
        self,
        stage: SankeyStage,
        cluster_info: Optional[Dict],
    ) -> List[Recommendation]:
        """Check if partition count is appropriate for the cluster."""
        recs = []
        if not cluster_info:
            return recs

        num_executors = cluster_info.get('num_executors', 1)
        cores_per_executor = cluster_info.get('cores_per_executor', 1)
        total_cores = num_executors * cores_per_executor

        parts = stage.shufflePartitions
        if parts <= 0:
            return recs

        # Too many partitions
        if parts > 10 * total_cores:
            recs.append(Recommendation(
                rule="excessive_partitions",
                severity="info",
                stageId=stage.id,
                message=f"Shuffle partitions ({parts}) may be excessive for cluster size ({total_cores} cores)",
                suggestion=f"Consider reducing spark.sql.shuffle.partitions to {2 * total_cores}-{4 * total_cores}.",
            ))

        # Too few partitions
        if parts < num_executors:
            recs.append(Recommendation(
                rule="too_few_partitions",
                severity="warning",
                stageId=stage.id,
                message=f"Only {parts} partitions for {num_executors} executors — potential underutilization",
                suggestion=f"Increase spark.sql.shuffle.partitions to at least {2 * total_cores} for better parallelism.",
            ))

        return recs

    def _check_shuffle_volume(
        self,
        stage: SankeyStage,
    ) -> List[Recommendation]:
        """Check for large shuffle volumes."""
        recs = []
        shuffle_read = stage.metrics.get('shuffleReadBytes', 0)

        # Large shuffle > 1GB
        if shuffle_read > 1_073_741_824:
            recs.append(Recommendation(
                rule="large_shuffle",
                severity="info",
                stageId=stage.id,
                message=f"Large shuffle volume ({_format_bytes(shuffle_read)}) in {stage.label}",
                suggestion="Check if pre-filtering data before the join or using partition pruning can reduce shuffle volume.",
            ))

        return recs
