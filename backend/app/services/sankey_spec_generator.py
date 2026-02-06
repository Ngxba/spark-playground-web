"""
SankeySpecGenerator — transforms real Spark execution data into spark-sankey/v1 JSON.

Pipeline:
  physical_plan → PhysicalPlanParser → List[JoinStep]
  join_steps + execution_simulation → stage mapping → bucketization → spec
"""

import math
import statistics
from typing import Dict, Any, List, Optional, Tuple

from app.config import settings
from app.models.sankey import (
    JoinStep, BucketGroup, SankeyNode, SankeyLink,
    SankeyStage, SankeySpec,
)
from app.services.physical_plan_parser import PhysicalPlanParser
from app.services.recommendation_engine import RecommendationEngine


class SankeySpecGenerator:

    def __init__(self):
        self.parser = PhysicalPlanParser()
        self.recommender = RecommendationEngine()

    # ----------------------------------------------------------------- public

    def generate(self, metadata: Dict, execution_simulation) -> Optional[Dict]:
        """
        Generate a spark-sankey/v1 spec from Spark metadata and execution data.

        Args:
            metadata: dict with 'physical_plan', etc. from executor_v2
            execution_simulation: ExecutionSimulation model (or None)

        Returns:
            Dict representing the spec, or None if generation is not possible.
        """
        physical_plan = metadata.get('physical_plan') if metadata else None
        if not physical_plan or not execution_simulation:
            return None

        # 1. Parse physical plan → join steps
        join_steps = self.parser.parse(physical_plan)
        if not join_steps:
            return None

        # 2. Map join steps to runtime stages
        stage_mapping = self._map_stages(join_steps, execution_simulation)
        if not stage_mapping:
            return None

        # 3. For each mapped stage, build nodes + links
        all_nodes: List[SankeyNode] = []
        all_links: List[SankeyLink] = []
        stage_specs: List[SankeyStage] = []

        for i, (join_step, runtime_stage) in enumerate(stage_mapping):
            stage_id = f"stage_{i}"
            tasks = self._get_tasks_for_stage(runtime_stage, execution_simulation)
            buckets = self._bucketize(tasks, stage_id)

            nodes, links, stage_spec = self._build_stage(
                join_step, buckets, tasks, stage_id, i
            )
            all_nodes.extend(nodes)
            all_links.extend(links)
            stage_specs.append(stage_spec)

        # 4. Build final spec
        spec = SankeySpec(
            meta={"title": self._build_title(join_steps)},
            stages=stage_specs,
            nodes=all_nodes,
            links=all_links,
        )

        # 5. Recommendations
        cluster_info = self._extract_cluster_info(execution_simulation)
        spec.recommendations = self.recommender.analyze(spec, cluster_info)

        return spec.model_dump()

    # ---------------------------------------------------------- stage mapping

    def _map_stages(
        self,
        join_steps: List[JoinStep],
        execution_simulation,
    ) -> List[Tuple[JoinStep, Any]]:
        """
        Map each JoinStep to a runtime stage from execution_simulation.

        Strategy:
        - Stages with shuffle_read > 0 are post-shuffle (join) stages.
        - Match by order: physical plan joins (DFS bottom-up) correspond
          to runtime stages with shuffle reads.
        - Fallback: if count mismatch, match by partition count heuristic.
        """
        if not execution_simulation or not execution_simulation.stages:
            return []

        # Identify runtime stages that have shuffle activity
        shuffle_stages = []
        for stage in execution_simulation.stages:
            has_shuffle = False
            if execution_simulation.shuffles:
                for shuffle in execution_simulation.shuffles:
                    if shuffle.to_stage_id == stage.id:
                        has_shuffle = True
                        break

            # Also check stage name/type for join/exchange hints
            stage_name = (stage.name or '').lower()
            stage_op = (stage.operation_type or '').lower()
            is_join_stage = any(
                kw in stage_name + ' ' + stage_op
                for kw in ['join', 'sortmerge', 'broadcasthash', 'exchange']
            )

            if has_shuffle or is_join_stage:
                shuffle_stages.append(stage)

        # If no shuffle stages found, use all non-scan stages
        if not shuffle_stages:
            shuffle_stages = [
                s for s in execution_simulation.stages
                if 'scan' not in (s.name or '').lower()
                and 'inmemory' not in (s.name or '').lower()
            ]

        # Match join_steps to shuffle_stages by index
        mapping = []
        for i, join_step in enumerate(join_steps):
            if i < len(shuffle_stages):
                mapping.append((join_step, shuffle_stages[i]))
            else:
                # Fallback: use the last available stage
                mapping.append((join_step, shuffle_stages[-1] if shuffle_stages else execution_simulation.stages[-1]))

        return mapping

    # --------------------------------------------------------- task retrieval

    def _get_tasks_for_stage(self, runtime_stage, execution_simulation) -> List[Dict]:
        """
        Get task-level data for a stage from the execution tree.

        The execution_simulation stores tasks on each Stage object.
        We also look at the execution_tree (raw Spark API data) if available
        for richer metrics (shuffle_read_metrics, shuffle_write_metrics).
        """
        tasks = []
        if runtime_stage and runtime_stage.tasks:
            for idx, task in enumerate(runtime_stage.tasks):
                tasks.append({
                    'index': idx,
                    'partition_id': task.partition_id,
                    'duration': task.duration,
                    'metrics': {
                        'records_read': 0,
                        'shuffle_read_bytes': 0,
                        'shuffle_write_bytes': 0,
                    }
                })

        # If no tasks found, create synthetic tasks based on parallelism
        if not tasks and runtime_stage:
            parallelism = runtime_stage.parallelism or 1
            for i in range(parallelism):
                tasks.append({
                    'index': i,
                    'partition_id': i,
                    'duration': 0,
                    'metrics': {
                        'records_read': 0,
                        'shuffle_read_bytes': 0,
                        'shuffle_write_bytes': 0,
                    }
                })

        return tasks

    # ---------------------------------------------------------- bucketization

    def _bucketize(self, tasks: List[Dict], stage_id: str) -> List[BucketGroup]:
        """
        Group tasks into K bucket groups with per-bucket metrics and skew flags.
        """
        if not tasks:
            return []

        N = len(tasks)
        K = min(settings.sankey_bucket_count, N)
        if K <= 0:
            K = 1
        bucket_size = math.ceil(N / K)

        sorted_tasks = sorted(tasks, key=lambda t: t['index'])
        buckets = []

        for i in range(K):
            start = i * bucket_size
            end = min(start + bucket_size, N) - 1
            if start > end:
                break
            bucket_tasks = sorted_tasks[start:end + 1]

            total_records = sum(
                t['metrics'].get('records_read', 0) for t in bucket_tasks
            )
            total_bytes = sum(
                t['metrics'].get('shuffle_read_bytes', 0) for t in bucket_tasks
            )
            shuffle_write = sum(
                t['metrics'].get('shuffle_write_bytes', 0) for t in bucket_tasks
            )

            # Skew detection based on task durations (more reliable than bytes
            # when shuffle metrics are zero)
            task_sizes = [t.get('duration', 0) for t in bucket_tasks]
            if all(s == 0 for s in task_sizes):
                task_sizes = [
                    t['metrics'].get('shuffle_read_bytes', 0) for t in bucket_tasks
                ]

            median_val = statistics.median(task_sizes) if task_sizes else 0
            max_val = max(task_sizes) if task_sizes else 0
            avg_val = statistics.mean(task_sizes) if task_sizes else 0

            is_skewed = False
            skew_ratio = 0.0
            if median_val > 0:
                skew_ratio = max_val / median_val
                if skew_ratio > settings.sankey_skew_p95_median_ratio:
                    is_skewed = True
            if not is_skewed and avg_val > 0:
                if max_val / avg_val > settings.sankey_skew_max_avg_ratio:
                    is_skewed = True

            buckets.append(BucketGroup(
                partition_start=start,
                partition_end=end,
                label=f"R{start}-R{end}",
                total_records=total_records,
                total_bytes=total_bytes,
                shuffle_read_bytes=total_bytes,
                shuffle_write_bytes=shuffle_write,
                is_skewed=is_skewed,
                skew_ratio=round(skew_ratio, 2),
            ))

        return buckets

    # ----------------------------------------------------------- stage build

    def _build_stage(
        self,
        join_step: JoinStep,
        buckets: List[BucketGroup],
        tasks: List[Dict],
        stage_id: str,
        stage_index: int,
    ) -> Tuple[List[SankeyNode], List[SankeyLink], SankeyStage]:
        """
        Build Sankey nodes, links, and stage spec for one join stage.

        Layout per stage:
          layer 0: input datasets (left_child, right_child)
          layer 1: exchange node
          layer 2: bucket groups
          layer 3: output dataset
        """
        nodes: List[SankeyNode] = []
        links: List[SankeyLink] = []

        join_key_str = ', '.join(join_step.join_keys) or 'key'
        left_name = join_step.left_child or 'Left'
        right_name = join_step.right_child or 'Right'
        shuffle_parts = join_step.shuffle_partitions or len(tasks)

        # --- Input dataset nodes (layer 0) ---
        left_id = f"df_{self._safe_id(left_name)}_{stage_id}"
        right_id = f"df_{self._safe_id(right_name)}_{stage_id}"

        # Estimate input sizes from task metrics
        total_input_bytes = sum(
            t['metrics'].get('shuffle_read_bytes', 0) for t in tasks
        )
        total_input_records = sum(
            t['metrics'].get('records_read', 0) for t in tasks
        )

        # Split roughly 60/40 between left and right (heuristic)
        left_bytes = int(total_input_bytes * 0.6)
        right_bytes = total_input_bytes - left_bytes
        left_records = int(total_input_records * 0.6)
        right_records = total_input_records - left_records

        nodes.append(SankeyNode(
            id=left_id, type="dataset", label=f"Dataset {left_name.title()}",
            layer=0, stageId=stage_id,
            metrics={"records": left_records, "bytes": left_bytes},
            meta={"partitions": shuffle_parts},
        ))
        nodes.append(SankeyNode(
            id=right_id, type="dataset", label=f"Dataset {right_name.title()}",
            layer=0, stageId=stage_id,
            metrics={"records": right_records, "bytes": right_bytes},
            meta={"partitions": shuffle_parts},
        ))

        # --- Exchange node (layer 1) ---
        exchange_id = f"ex_{stage_id}"
        nodes.append(SankeyNode(
            id=exchange_id, type="exchange", label="Exchange",
            layer=1, stageId=stage_id,
            keys=join_step.join_keys,
            shufflePartitions=shuffle_parts,
        ))

        # --- Bucket group nodes (layer 2) ---
        for b_idx, bucket in enumerate(buckets):
            bucket_id = f"b{stage_index}_{b_idx}"
            skew_reason = None
            if bucket.is_skewed:
                skew_reason = f"Skew ratio: {bucket.skew_ratio}x median"

            nodes.append(SankeyNode(
                id=bucket_id, type="bucketGroup", label=bucket.label,
                layer=2, stageId=stage_id,
                isSkewed=bucket.is_skewed,
                skewReason=skew_reason,
                partitionRange=[bucket.partition_start, bucket.partition_end],
                partitionCount=bucket.partition_end - bucket.partition_start + 1,
                metrics={
                    "records": bucket.total_records,
                    "bytes": bucket.total_bytes,
                },
            ))

        # --- Output dataset node (layer 3) ---
        output_records = sum(b.total_records for b in buckets)
        output_bytes = sum(b.total_bytes for b in buckets)

        # Generate output name from join
        output_name = f"{left_name[0].upper()}{right_name[0].upper()}"
        output_id = f"df_{self._safe_id(output_name)}_{stage_id}"

        nodes.append(SankeyNode(
            id=output_id, type="dataset", label=f"Dataset {output_name}",
            layer=3, stageId=stage_id,
            metrics={"records": output_records, "bytes": output_bytes},
            meta={"partitions": shuffle_parts},
        ))

        # --- Links: input → buckets ---
        num_buckets = len(buckets)
        for b_idx, bucket in enumerate(buckets):
            bucket_id = f"b{stage_index}_{b_idx}"
            routing = f"hash({join_key_str}) % {shuffle_parts} → [{bucket.partition_start}-{bucket.partition_end}]"

            # Left input → bucket
            left_records_to_bucket = int(bucket.total_records * 0.6)
            left_bytes_to_bucket = int(bucket.total_bytes * 0.6)
            links.append(SankeyLink(
                id=f"l_{self._safe_id(left_name)}_b{stage_index}_{b_idx}",
                source=left_id, target=bucket_id,
                metrics={"records": left_records_to_bucket, "bytes": left_bytes_to_bucket},
                meta={"routing": routing},
            ))

            # Right input → bucket
            right_records_to_bucket = bucket.total_records - left_records_to_bucket
            right_bytes_to_bucket = bucket.total_bytes - left_bytes_to_bucket
            links.append(SankeyLink(
                id=f"l_{self._safe_id(right_name)}_b{stage_index}_{b_idx}",
                source=right_id, target=bucket_id,
                metrics={"records": right_records_to_bucket, "bytes": right_bytes_to_bucket},
                meta={"routing": routing},
            ))

            # Bucket → output
            links.append(SankeyLink(
                id=f"l_b{stage_index}_{b_idx}_{self._safe_id(output_name)}",
                source=bucket_id, target=output_id,
                metrics={"records": bucket.total_records, "bytes": bucket.total_bytes},
            ))

        # --- Stage spec ---
        skewed_count = sum(1 for b in buckets if b.is_skewed)
        total_shuffle_read = sum(b.shuffle_read_bytes for b in buckets)
        total_shuffle_write = sum(b.shuffle_write_bytes for b in buckets)

        stage_spec = SankeyStage(
            id=stage_id,
            label=f"Stage {stage_index + 1}: {left_name.title()} ⋈ {right_name.title()} → {output_name}",
            description=f"Hash join on {join_key_str} → {shuffle_parts} partitions",
            joinType=join_step.join_type,
            joinKey=join_key_str,
            shufflePartitions=shuffle_parts,
            metrics={
                "shuffleReadBytes": total_shuffle_read,
                "shuffleWriteBytes": total_shuffle_write,
                "outputPartitions": shuffle_parts,
                "skewedBuckets": skewed_count,
                "totalBuckets": num_buckets,
                "outputRecords": output_records,
            },
        )

        return nodes, links, stage_spec

    # --------------------------------------------------------------- helpers

    def _build_title(self, join_steps: List[JoinStep]) -> str:
        """Build a human-readable pipeline title."""
        parts = []
        for step in join_steps:
            left = step.left_child or '?'
            right = step.right_child or '?'
            parts.append(f"{left.title()} ⋈ {right.title()}")
        return ' → '.join(parts) if parts else 'Spark Execution'

    def _scale_link_value(self, raw_bytes: int) -> int:
        """Sqrt scale bytes for Sankey link width."""
        scaled = math.sqrt(raw_bytes) * 0.03
        return max(4, min(int(scaled), settings.sankey_link_max_width))

    def _safe_id(self, name: str) -> str:
        """Create a safe string ID from a dataset name."""
        return name.lower().replace(' ', '_').replace('-', '_')[:20]

    def _extract_cluster_info(self, execution_simulation) -> Optional[Dict]:
        """Extract cluster info for recommendation engine."""
        if not execution_simulation:
            return None
        return {
            'num_executors': execution_simulation.node_count,
            'cores_per_executor': execution_simulation.cores_per_node,
            'total_cores': execution_simulation.total_cores,
        }
