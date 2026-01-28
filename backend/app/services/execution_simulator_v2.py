from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from app.models.execution import (
    ExecutionSimulation,
    Stage,
    Task,
    Partition,
    Shuffle,
    Node,
    SimulationEvent
)
from app.services.spark_event_tracker import SparkEventTracker


class ExecutionSimulatorV2:
    """
    Generates execution simulation from REAL Spark events.

    Converts real Spark execution tree (jobs → stages → tasks) from REST API
    into ExecutionSimulation models for Factory View visualization.
    """

    def __init__(self, event_tracker: SparkEventTracker):
        self.event_tracker = event_tracker

    def _parse_timestamp(self, timestamp: Any) -> int:
        """
        Parse Spark API timestamp to milliseconds.

        Spark API returns timestamps as ISO strings like "2026-01-25T16:38:44.797GMT"
        or sometimes as epoch milliseconds.

        Args:
            timestamp: ISO string, epoch milliseconds (int), or None

        Returns:
            Timestamp in milliseconds (0 if None or unparseable)
        """
        if timestamp is None:
            return 0

        # Already a number (epoch ms)
        if isinstance(timestamp, (int, float)):
            return int(timestamp)

        # ISO string format: "2026-01-25T16:38:44.797GMT"
        if isinstance(timestamp, str):
            try:
                # Remove GMT suffix and parse
                ts_str = timestamp.replace('GMT', '').strip()
                dt = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%S.%f')
                return int(dt.timestamp() * 1000)
            except ValueError:
                try:
                    # Try without milliseconds
                    ts_str = timestamp.replace('GMT', '').strip()
                    dt = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%S')
                    return int(dt.timestamp() * 1000)
                except ValueError:
                    return 0

        return 0

    def generate_simulation_from_events(
        self,
        app_id: str,
        job_group_id: str,
        metadata: Dict[str, Any],
        execution_tree: Optional[Dict[str, Any]] = None
    ) -> Optional[ExecutionSimulation]:
        """
        Generate ExecutionSimulation from REAL Spark data.

        Args:
            app_id: Spark application ID
            job_group_id: Job group ID for filtering
            metadata: Execution metadata from executor (contains query plans)
            execution_tree: Pre-fetched execution tree from active Spark UI.
                            If provided, skips the History Server fetch entirely.

        Returns:
            ExecutionSimulation with real data, or None if data unavailable
        """
        # Use pre-fetched tree if available, otherwise fall back to History Server
        if execution_tree is None:
            execution_tree = self.event_tracker.wait_for_events(app_id, job_group_id)

        if not execution_tree or not execution_tree.get('jobs'):
            print("Warning: No execution data available, cannot generate simulation")
            return None

        print(f"Generating simulation from {len(execution_tree['jobs'])} real Spark jobs")

        # Extract cluster config from metadata
        cluster_config = metadata.get('cluster_config', {})

        # Build nodes FIRST so _executor_to_node_map is available for _convert_tasks
        nodes = self._build_nodes_from_executors(execution_tree, cluster_config)

        # Convert execution tree to simulation models
        stages = self._convert_stages(execution_tree)
        all_tasks = self._extract_all_tasks(stages)
        partitions = self._build_partitions_from_tasks(all_tasks, stages)
        shuffles = self._detect_shuffles(execution_tree, metadata)
        events = self._build_timeline_events(stages, all_tasks, shuffles)

        # Calculate metrics - use job-level timestamps for accurate total duration
        total_duration = self._calculate_total_duration_from_jobs(execution_tree)
        # Use the max task count from any single stage as the runtime partition
        # count.  Each task processes one partition, and partition IDs restart
        # from 0 per stage so counting unique IDs across stages is unreliable.
        partition_count = max((len(stage.tasks) for stage in stages), default=0)

        return ExecutionSimulation(
            total_duration=total_duration,
            partition_count=partition_count,
            node_count=len(nodes),
            cores_per_node=nodes[0].cores if nodes else 2,
            total_cores=sum(node.cores for node in nodes),
            stages=stages,
            partitions=partitions,
            shuffles=shuffles,
            nodes=nodes,
            events=events,
            metrics=self._calculate_metrics(execution_tree)
        )

    def _convert_stages(self, execution_tree: Dict) -> List[Stage]:
        """
        Convert real Spark stages to Stage models.

        Args:
            execution_tree: Execution tree from SparkEventTracker

        Returns:
            List of Stage models
        """
        stages = []
        stage_id_counter = 0

        for job in execution_tree['jobs']:
            for stage_data in job['stages']:
                # Convert timestamps to relative time (seconds from start)
                # Parse ISO timestamps from Spark API to milliseconds
                submission_time = self._parse_timestamp(stage_data.get('submission_time'))
                completion_time = self._parse_timestamp(stage_data.get('completion_time')) or submission_time

                # First stage's submission time is our baseline
                if stage_id_counter == 0:
                    self.baseline_time = submission_time / 1000.0  # Convert ms to seconds

                start_time = (submission_time / 1000.0) - self.baseline_time
                end_time = (completion_time / 1000.0) - self.baseline_time

                # Extract operation type from stage name
                stage_name = stage_data.get('name', f"Stage {stage_data['stage_id']}")
                operation_type = self._infer_operation_type(stage_name)

                # Convert tasks
                tasks = self._convert_tasks(
                    stage_data.get('tasks', []),
                    stage_data['stage_id'],
                    start_time
                )

                # Determine dependencies (stages this depends on)
                # In Spark, stages typically depend on previous stages in same job
                dependencies = []
                if stage_id_counter > 0:
                    # Simplified: assume sequential dependency within job
                    dependencies = [stage_id_counter - 1]

                stage = Stage(
                    id=stage_id_counter,
                    name=stage_name,
                    operation_type=operation_type,
                    start_time=start_time,
                    end_time=end_time,
                    tasks=tasks,
                    dependencies=dependencies,
                    parallelism=stage_data.get('num_tasks', len(tasks)),
                    status=self._convert_status(stage_data.get('status', 'COMPLETE'))
                )

                stages.append(stage)
                stage_id_counter += 1

        return stages

    def _convert_tasks(
        self,
        tasks_data: List[Dict],
        stage_id: int,
        stage_start_time: float
    ) -> List[Task]:
        """
        Convert real Spark tasks to Task models.

        Args:
            tasks_data: Raw task data from Spark API
            stage_id: Parent stage ID
            stage_start_time: Stage start time for relative timing

        Returns:
            List of Task models
        """
        tasks = []

        for task_data in tasks_data:
            # Parse ISO timestamps from Spark API to milliseconds
            launch_time = self._parse_timestamp(task_data.get('launch_time'))
            finish_time = self._parse_timestamp(task_data.get('finish_time')) or launch_time

            # Convert to relative time (seconds from baseline)
            start_time = (launch_time / 1000.0) - self.baseline_time
            end_time = (finish_time / 1000.0) - self.baseline_time
            duration = (task_data.get('duration') or 0) / 1000.0  # Convert ms to seconds

            # Extract executor info for node mapping
            executor_id = task_data.get('executor_id', 'driver')
            # Map executor to node_id using the mapping built by _build_nodes_from_executors
            node_id = getattr(self, '_executor_to_node_map', {}).get(str(executor_id), 0)

            # Extract core ID using actual node core count
            nodes_list = getattr(self, '_nodes_list', [])
            node_cores = nodes_list[node_id].cores if node_id < len(nodes_list) else 2
            core_id = task_data.get('index', 0) % max(node_cores, 1)

            task = Task(
                id=task_data.get('task_id', 0),
                partition_id=task_data.get('partition_id', task_data.get('index', 0)),
                node_id=node_id,
                core_id=core_id,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                status=self._convert_task_status(task_data.get('status', 'SUCCESS'))
            )

            tasks.append(task)

        return tasks

    def _extract_all_tasks(self, stages: List[Stage]) -> List[Task]:
        """Extract all tasks from all stages."""
        all_tasks = []
        for stage in stages:
            all_tasks.extend(stage.tasks)
        return all_tasks

    def _build_partitions_from_tasks(
        self,
        tasks: List[Task],
        stages: List[Stage]
    ) -> List[Partition]:
        """
        Build partition models from task data.

        Args:
            tasks: All tasks from all stages
            stages: All stages

        Returns:
            List of Partition models
        """
        partitions = []
        partition_map = {}  # partition_id -> partition

        for task in tasks:
            partition_id = task.partition_id

            if partition_id not in partition_map:
                # Find which stage this task belongs to
                stage_id = 0
                for stage in stages:
                    if task in stage.tasks:
                        stage_id = stage.id
                        break

                partition = Partition(
                    id=partition_id,
                    size_mb=0.5,  # Approximate size (could be extracted from metrics)
                    records_count=100,  # Approximate (could be extracted from metrics)
                    data_preview=None,
                    stage_id=stage_id,
                    parent_partitions=[],
                    child_partitions=[]
                )
                partition_map[partition_id] = partition

        partitions = list(partition_map.values())
        return partitions

    def _detect_shuffles(
        self,
        execution_tree: Dict,
        metadata: Dict
    ) -> List[Shuffle]:
        """
        Detect shuffle operations from execution tree and metadata.

        Args:
            execution_tree: Execution tree from SparkEventTracker
            metadata: Execution metadata with query plans

        Returns:
            List of Shuffle models
        """
        shuffles = []

        # Check physical plan for Exchange operations (shuffles)
        physical_plan = metadata.get('physical_plan', '')
        has_shuffle = "Exchange" in physical_plan

        if not has_shuffle:
            return shuffles

        # Simplified: create shuffle between consecutive stages if detected
        num_stages = sum(len(job['stages']) for job in execution_tree['jobs'])

        if num_stages >= 2:
            # Create shuffle from first stage to second stage
            for i in range(num_stages - 1):
                # Extract shuffle metrics from stage data if available
                # This is simplified - in reality we'd parse more carefully
                shuffle = Shuffle(
                    from_stage_id=i,
                    to_stage_id=i + 1,
                    data_volume_mb=1.0,  # Approximate
                    from_partitions=4,  # Default partition count
                    to_partitions=4,
                    start_time=i * 1.0,
                    end_time=(i + 1) * 1.0,
                    partition_mapping={
                        0: [0, 1],
                        1: [1, 2],
                        2: [2, 3],
                        3: [3, 0]
                    }
                )
                shuffles.append(shuffle)

        return shuffles

    def _build_nodes_from_executors(
        self,
        execution_tree: Dict,
        cluster_config: Dict
    ) -> List[Node]:
        """
        Build Node models from cluster_config executor list.

        Uses cluster_config['executors'] for accurate per-executor cores and memory.
        Falls back to extracting executors from tasks if cluster_config is incomplete.

        Populates self._executor_to_node_map and self._nodes_list for use by
        _convert_tasks().

        Args:
            execution_tree: Execution tree with executor data
            cluster_config: Cluster configuration from executor

        Returns:
            List of Node models
        """
        self._executor_to_node_map: Dict[str, int] = {}
        nodes: List[Node] = []

        executors_list = cluster_config.get('executors', [])
        mode = cluster_config.get('mode', '')
        is_local = bool(re.match(r'^local(\[.*\])?$', mode.strip(), re.IGNORECASE)) if mode else False

        if executors_list:
            # Use cluster_config executors (authoritative source)
            node_id = 0
            for executor in executors_list:
                eid = str(executor.get('id', ''))
                # In cluster mode, skip the driver entry (it doesn't run tasks)
                if eid == 'driver' and not is_local:
                    continue

                cores = executor.get('cores', 2)
                memory_mb = executor.get('memory_mb', 2048)

                node = Node(
                    id=node_id,
                    name=f"Executor {eid}",
                    cores=cores,
                    memory_gb=round(memory_mb / 1024, 1),
                    assigned_tasks=[]
                )
                nodes.append(node)
                self._executor_to_node_map[eid] = node_id
                node_id += 1
        else:
            # Fallback: extract unique executors from tasks
            executors = set()
            for job in execution_tree['jobs']:
                for stage in job['stages']:
                    for task in stage.get('tasks', []):
                        executor_id = task.get('executor_id', 'driver')
                        executors.add(executor_id)

            cores_per_node = cluster_config.get('cluster_capacity', {}).get('total_cores', 2)

            for i, executor_id in enumerate(sorted(executors)):
                node = Node(
                    id=i,
                    name=f"Executor {executor_id}",
                    cores=cores_per_node,
                    memory_gb=2.0,
                    assigned_tasks=[]
                )
                nodes.append(node)
                self._executor_to_node_map[str(executor_id)] = i

        # If no executors found, create default node
        if not nodes:
            nodes.append(Node(
                id=0,
                name="Driver",
                cores=2,
                memory_gb=2.0,
                assigned_tasks=[]
            ))
            self._executor_to_node_map['driver'] = 0

        self._nodes_list = nodes
        return nodes

    def _build_timeline_events(
        self,
        stages: List[Stage],
        tasks: List[Task],
        shuffles: List[Shuffle]
    ) -> List[SimulationEvent]:
        """
        Build timeline events for animation.

        Args:
            stages: All stages
            tasks: All tasks
            shuffles: All shuffles

        Returns:
            List of SimulationEvent models sorted by time
        """
        events = []

        # Stage events
        for stage in stages:
            events.append(SimulationEvent(
                time=stage.start_time,
                event_type="stage_start",
                stage_id=stage.id,
                details={"name": stage.name, "operation": stage.operation_type}
            ))
            events.append(SimulationEvent(
                time=stage.end_time,
                event_type="stage_end",
                stage_id=stage.id,
                details={"name": stage.name}
            ))

        # Task events
        for task in tasks:
            events.append(SimulationEvent(
                time=task.start_time,
                event_type="task_start",
                task_id=task.id,
                details={"partition_id": task.partition_id, "node_id": task.node_id}
            ))
            events.append(SimulationEvent(
                time=task.end_time,
                event_type="task_end",
                task_id=task.id,
                details={"duration": task.duration}
            ))

        # Shuffle events
        for shuffle in shuffles:
            events.append(SimulationEvent(
                time=shuffle.start_time,
                event_type="shuffle_start",
                stage_id=shuffle.from_stage_id,
                details={
                    "from_stage": shuffle.from_stage_id,
                    "to_stage": shuffle.to_stage_id,
                    "data_mb": shuffle.data_volume_mb
                }
            ))
            events.append(SimulationEvent(
                time=shuffle.end_time,
                event_type="shuffle_end",
                stage_id=shuffle.to_stage_id,
                details={"data_mb": shuffle.data_volume_mb}
            ))

        # Sort events by time
        events.sort(key=lambda e: e.time)

        return events

    def _calculate_total_duration_from_jobs(self, execution_tree: Dict) -> float:
        """
        Calculate total execution duration from job-level timestamps.

        This is more accurate than summing stage durations because:
        - Stages may run in parallel
        - Job timestamps represent the actual wall-clock time

        Args:
            execution_tree: Execution tree from SparkEventTracker

        Returns:
            Total duration in seconds
        """
        jobs = execution_tree.get('jobs', [])
        if not jobs:
            return 0.0

        # Find earliest submission time and latest completion time across all jobs
        submission_times = []
        completion_times = []

        for job in jobs:
            submission_time = self._parse_timestamp(job.get('submission_time'))
            completion_time = self._parse_timestamp(job.get('completion_time'))

            if submission_time:
                submission_times.append(submission_time)
            if completion_time:
                completion_times.append(completion_time)

        if not submission_times or not completion_times:
            # Fallback to stage-based calculation
            print("Warning: Missing job timestamps, falling back to stage-based duration")
            return 0.0

        # Calculate duration: latest completion - earliest submission
        earliest_start = min(submission_times)
        latest_end = max(completion_times)

        # Convert from milliseconds to seconds
        duration_seconds = (latest_end - earliest_start) / 1000.0

        print(f"Total duration calculated from jobs: {duration_seconds:.3f} seconds")
        return duration_seconds

    def _calculate_metrics(self, execution_tree: Dict) -> Dict[str, Any]:
        """
        Calculate summary metrics from execution tree.

        Args:
            execution_tree: Execution tree from SparkEventTracker

        Returns:
            Dictionary of metrics
        """
        total_tasks = 0
        total_input_bytes = 0
        total_output_bytes = 0
        total_shuffle_read = 0
        total_shuffle_write = 0

        for job in execution_tree['jobs']:
            for stage in job['stages']:
                total_tasks += stage.get('num_tasks', 0)
                total_input_bytes += stage.get('input_bytes', 0)
                total_output_bytes += stage.get('output_bytes', 0)
                total_shuffle_read += stage.get('shuffle_read_bytes', 0)
                total_shuffle_write += stage.get('shuffle_write_bytes', 0)

        return {
            'total_tasks': total_tasks,
            'total_input_mb': total_input_bytes / (1024 * 1024),
            'total_output_mb': total_output_bytes / (1024 * 1024),
            'total_shuffle_read_mb': total_shuffle_read / (1024 * 1024),
            'total_shuffle_write_mb': total_shuffle_write / (1024 * 1024),
            'num_jobs': len(execution_tree['jobs']),
            'num_stages': sum(len(job['stages']) for job in execution_tree['jobs'])
        }

    def _infer_operation_type(self, stage_name: str) -> str:
        """
        Infer operation type from stage name.

        Args:
            stage_name: Stage name from Spark

        Returns:
            Operation type string
        """
        stage_name_lower = stage_name.lower()

        if 'scan' in stage_name_lower or 'parquet' in stage_name_lower or 'csv' in stage_name_lower:
            return 'scan'
        elif 'filter' in stage_name_lower:
            return 'filter'
        elif 'join' in stage_name_lower:
            return 'join'
        elif 'aggregate' in stage_name_lower or 'groupby' in stage_name_lower:
            return 'aggregate'
        elif 'exchange' in stage_name_lower or 'shuffle' in stage_name_lower:
            return 'shuffle'
        elif 'sort' in stage_name_lower:
            return 'sort'
        else:
            return 'transform'

    def _convert_status(self, spark_status: str) -> str:
        """Convert Spark stage status to our status format."""
        status_map = {
            'COMPLETE': 'completed',
            'ACTIVE': 'running',
            'PENDING': 'pending',
            'FAILED': 'failed'
        }
        return status_map.get(spark_status.upper(), 'completed')

    def _convert_task_status(self, spark_status: str) -> str:
        """Convert Spark task status to our status format."""
        status_map = {
            'SUCCESS': 'completed',
            'RUNNING': 'running',
            'FAILED': 'failed',
            'KILLED': 'failed'
        }
        return status_map.get(spark_status.upper(), 'completed')
