from typing import List, Dict, Any, Optional
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

    def generate_simulation_from_events(
        self,
        app_id: str,
        job_group_id: str,
        metadata: Dict[str, Any]
    ) -> Optional[ExecutionSimulation]:
        """
        Generate ExecutionSimulation from REAL Spark data.

        Args:
            app_id: Spark application ID
            job_group_id: Job group ID for filtering
            metadata: Execution metadata from executor (contains query plans)

        Returns:
            ExecutionSimulation with real data, or None if data unavailable
        """
        # Fetch real execution tree from Spark REST API
        execution_tree = self.event_tracker.wait_for_events(app_id, job_group_id)

        if not execution_tree or not execution_tree.get('jobs'):
            print("Warning: No execution data available, cannot generate simulation")
            return None

        print(f"Generating simulation from {len(execution_tree['jobs'])} real Spark jobs")

        # Extract cluster config from metadata
        cluster_config = metadata.get('cluster_config', {})

        # Convert execution tree to simulation models
        stages = self._convert_stages(execution_tree)
        all_tasks = self._extract_all_tasks(stages)
        partitions = self._build_partitions_from_tasks(all_tasks, stages)
        shuffles = self._detect_shuffles(execution_tree, metadata)
        nodes = self._build_nodes_from_executors(execution_tree, cluster_config)
        events = self._build_timeline_events(stages, all_tasks, shuffles)

        # Calculate metrics
        total_duration = self._calculate_total_duration(stages)
        partition_count = len(set(task.partition_id for task in all_tasks))

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
                submission_time = stage_data.get('submission_time', 0)
                completion_time = stage_data.get('completion_time', submission_time)

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
            launch_time = task_data.get('launch_time', 0)
            finish_time = task_data.get('finish_time', launch_time)

            # Convert to relative time (seconds from baseline)
            start_time = (launch_time / 1000.0) - self.baseline_time
            end_time = (finish_time / 1000.0) - self.baseline_time
            duration = task_data.get('duration', 0) / 1000.0  # Convert ms to seconds

            # Extract executor info for node mapping
            executor_id = task_data.get('executor_id', 'driver')
            # Map executor to node_id (simplified: use hash of executor_id)
            node_id = abs(hash(executor_id)) % 2  # Limit to 2 nodes for local mode

            # Extract core ID (simplified: use task index % cores)
            core_id = task_data.get('index', 0) % 2

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
        Build Node models from executor information.

        Args:
            execution_tree: Execution tree with executor data
            cluster_config: Cluster configuration from executor

        Returns:
            List of Node models
        """
        # Extract unique executors from tasks
        executors = set()
        for job in execution_tree['jobs']:
            for stage in job['stages']:
                for task in stage.get('tasks', []):
                    executor_id = task.get('executor_id', 'driver')
                    executors.add(executor_id)

        # Get cores from cluster config
        cores_per_node = cluster_config.get('cluster_summary', {}).get('total_cores', 2)

        nodes = []
        for i, executor_id in enumerate(sorted(executors)):
            node = Node(
                id=i,
                name=f"Executor {executor_id}",
                cores=cores_per_node,
                memory_gb=2.0,  # From cluster config
                assigned_tasks=[]
            )
            nodes.append(node)

        # If no executors found, create default node
        if not nodes:
            nodes.append(Node(
                id=0,
                name="Driver",
                cores=2,
                memory_gb=2.0,
                assigned_tasks=[]
            ))

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

    def _calculate_total_duration(self, stages: List[Stage]) -> float:
        """Calculate total execution duration from stages."""
        if not stages:
            return 0.0

        start_time = min(stage.start_time for stage in stages)
        end_time = max(stage.end_time for stage in stages)
        return end_time - start_time

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
