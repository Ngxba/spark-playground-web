"""
Execution Simulator - Generates animated execution simulations from Spark physical plans
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from app.models.execution import (
    ExecutionSimulation,
    Stage,
    Task,
    Partition,
    Shuffle,
    Node,
    SimulationEvent
)


class ExecutionSimulator:
    """
    Generates execution simulation data from Spark physical plans
    for visualization in the Factory View
    """

    def __init__(self):
        # Cluster configuration
        self.node_count = 4
        self.cores_per_node = 4
        self.total_cores = self.node_count * self.cores_per_node
        self.memory_per_node_gb = 4.0

        # Timing parameters (simulated, in seconds)
        self.base_task_duration = 0.5
        self.shuffle_overhead = 0.3
        self.scan_duration = 0.2
        self.filter_duration = 0.1
        self.join_duration = 0.4
        self.aggregate_duration = 0.3

    def generate_simulation(
        self,
        physical_plan: Optional[str],
        logical_plan: Optional[str],
        execution_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ExecutionSimulation]:
        """
        Generate execution simulation from Spark plans

        Args:
            physical_plan: Spark physical execution plan
            logical_plan: Spark logical query plan
            execution_metadata: Additional execution metadata

        Returns:
            ExecutionSimulation object or None if generation fails
        """
        if not physical_plan:
            return None

        try:
            # Parse physical plan to extract stages
            stages_info = self._parse_physical_plan(physical_plan)

            # Determine partition count
            partition_count = self._estimate_partition_count(
                physical_plan, execution_metadata
            )

            # Generate nodes
            nodes = self._generate_nodes()

            # Generate stages with tasks
            stages, all_tasks = self._generate_stages_and_tasks(
                stages_info, partition_count, nodes
            )

            # Detect and generate shuffles
            shuffles = self._generate_shuffles(stages, stages_info)

            # Generate partitions with lineage tracking
            partitions = self._generate_partitions_with_lineage(stages, shuffles)

            # Generate timeline events
            events = self._generate_events(stages, shuffles)

            # Calculate total duration
            total_duration = max(
                [stage.end_time for stage in stages] if stages else [0]
            )

            # Create metrics summary
            metrics = {
                "total_stages": len(stages),
                "total_tasks": sum(len(stage.tasks) for stage in stages),
                "total_shuffles": len(shuffles),
                "avg_parallelism": sum(stage.parallelism for stage in stages) / len(stages) if stages else 0,
            }

            return ExecutionSimulation(
                total_duration=total_duration,
                partition_count=partition_count,
                node_count=self.node_count,
                cores_per_node=self.cores_per_node,
                total_cores=self.total_cores,
                stages=stages,
                partitions=partitions,
                shuffles=shuffles,
                nodes=nodes,
                events=events,
                metrics=metrics
            )

        except Exception as e:
            print(f"Error generating simulation: {str(e)}")
            return None

    def _parse_physical_plan(self, physical_plan: str) -> List[Dict[str, Any]]:
        """
        Parse physical plan to extract stage information

        Returns:
            List of stage info dictionaries
        """
        stages_info = []

        # Common Spark physical plan operations
        operations = [
            ("Scan", r"FileScan|Scan"),
            ("Filter", r"Filter"),
            ("Project", r"Project"),
            ("HashAggregate", r"HashAggregate"),
            ("SortMergeJoin", r"SortMergeJoin"),
            ("BroadcastHashJoin", r"BroadcastHashJoin"),
            ("Sort", r"Sort"),
            ("Exchange", r"Exchange"),
            ("BroadcastExchange", r"BroadcastExchange"),
        ]

        current_stage = {
            "id": 0,
            "operations": [],
            "has_shuffle": False,
            "has_broadcast": False,
        }

        lines = physical_plan.split('\n')
        for line in lines:
            # Check for each operation type
            for op_name, op_pattern in operations:
                if re.search(op_pattern, line):
                    current_stage["operations"].append(op_name)

                    if op_name == "Exchange":
                        current_stage["has_shuffle"] = True
                    elif op_name == "BroadcastExchange":
                        current_stage["has_broadcast"] = True

        # Create stage name from operations
        if current_stage["operations"]:
            # Remove duplicates while preserving order
            unique_ops = []
            seen = set()
            for op in current_stage["operations"]:
                if op not in seen:
                    unique_ops.append(op)
                    seen.add(op)

            current_stage["name"] = " + ".join(unique_ops[:3])  # Limit to 3 ops
            if len(unique_ops) > 3:
                current_stage["name"] += "..."
            stages_info.append(current_stage)

        # If no operations detected, create a default stage
        if not stages_info:
            stages_info.append({
                "id": 0,
                "name": "Data Processing",
                "operations": ["Scan", "Process"],
                "has_shuffle": False,
                "has_broadcast": False,
            })

        return stages_info

    def _estimate_partition_count(
        self,
        physical_plan: str,
        execution_metadata: Optional[Dict[str, Any]]
    ) -> int:
        """Estimate the number of partitions from the plan"""
        # Default to a reasonable number
        default_partitions = 10

        # Try to extract from plan or metadata
        if execution_metadata and "metrics" in execution_metadata:
            # Could extract from spark.sql.shuffle.partitions config
            pass

        # For now, use default
        return default_partitions

    def _generate_nodes(self) -> List[Node]:
        """Generate worker nodes"""
        nodes = []
        for i in range(self.node_count):
            nodes.append(Node(
                id=i,
                name=f"Worker {i + 1}",
                cores=self.cores_per_node,
                memory_gb=self.memory_per_node_gb,
                assigned_tasks=[]
            ))
        return nodes

    def _generate_stages_and_tasks(
        self,
        stages_info: List[Dict[str, Any]],
        partition_count: int,
        nodes: List[Node]
    ) -> Tuple[List[Stage], List[Task]]:
        """
        Generate stages and their tasks

        Returns:
            Tuple of (stages, all_tasks)
        """
        stages = []
        all_tasks = []
        current_time = 0.0
        task_id_counter = 0

        for stage_idx, stage_info in enumerate(stages_info):
            # Determine operation type
            ops = stage_info.get("operations", [])
            if "Scan" in ops:
                operation_type = "scan"
                stage_duration = self.scan_duration
            elif "Filter" in ops:
                operation_type = "filter"
                stage_duration = self.filter_duration
            elif any(op in ops for op in ["SortMergeJoin", "BroadcastHashJoin"]):
                operation_type = "join"
                stage_duration = self.join_duration
            elif "HashAggregate" in ops:
                operation_type = "aggregate"
                stage_duration = self.aggregate_duration
            elif "Exchange" in ops:
                operation_type = "shuffle"
                stage_duration = self.shuffle_overhead
            else:
                operation_type = "process"
                stage_duration = self.base_task_duration

            # Generate tasks for this stage (one per partition)
            num_tasks = partition_count
            parallelism = min(num_tasks, self.total_cores)

            tasks = []
            stage_start = current_time

            # Distribute tasks across nodes
            for task_idx in range(num_tasks):
                partition_id = task_idx
                node_id = task_idx % self.node_count
                core_id = (task_idx // self.node_count) % self.cores_per_node

                # Calculate when this task starts (based on available cores)
                batch = task_idx // self.total_cores
                task_start = stage_start + (batch * stage_duration)
                task_end = task_start + stage_duration

                task = Task(
                    id=task_id_counter,
                    partition_id=partition_id,
                    node_id=node_id,
                    core_id=core_id,
                    start_time=task_start,
                    end_time=task_end,
                    duration=stage_duration,
                    status="completed"
                )
                tasks.append(task)
                all_tasks.append(task)
                nodes[node_id].assigned_tasks.append(task_id_counter)
                task_id_counter += 1

            # Stage ends when all tasks complete
            stage_end = max(task.end_time for task in tasks) if tasks else stage_start

            stage = Stage(
                id=stage_idx,
                name=stage_info.get("name", f"Stage {stage_idx}"),
                operation_type=operation_type,
                start_time=stage_start,
                end_time=stage_end,
                tasks=tasks,
                dependencies=[] if stage_idx == 0 else [stage_idx - 1],
                parallelism=parallelism,
                status="completed"
            )
            stages.append(stage)

            # Update current time for next stage
            current_time = stage_end

            # Add shuffle time if this stage has shuffle
            if stage_info.get("has_shuffle"):
                current_time += self.shuffle_overhead

        return stages, all_tasks

    def _generate_shuffles(
        self,
        stages: List[Stage],
        stages_info: List[Dict[str, Any]]
    ) -> List[Shuffle]:
        """Generate shuffle operations between stages"""
        shuffles = []

        for idx, stage_info in enumerate(stages_info):
            if stage_info.get("has_shuffle") and idx < len(stages) - 1:
                current_stage = stages[idx]
                next_stage = stages[idx + 1] if idx + 1 < len(stages) else None

                if next_stage:
                    # Estimate shuffle data volume (simplified)
                    data_volume_mb = len(current_stage.tasks) * 2.5  # ~2.5MB per task

                    # Generate partition mapping for this shuffle
                    partition_mapping = self._generate_partition_mapping(
                        from_count=len(current_stage.tasks),
                        to_count=len(next_stage.tasks),
                        shuffle_type="hash"  # Default to hash partitioning
                    )

                    shuffle = Shuffle(
                        from_stage_id=current_stage.id,
                        to_stage_id=next_stage.id,
                        data_volume_mb=data_volume_mb,
                        from_partitions=len(current_stage.tasks),
                        to_partitions=len(next_stage.tasks),
                        start_time=current_stage.end_time,
                        end_time=next_stage.start_time,
                        partition_mapping=partition_mapping
                    )
                    shuffles.append(shuffle)

        return shuffles

    def _generate_partition_mapping(
        self,
        from_count: int,
        to_count: int,
        shuffle_type: str = "hash"
    ) -> Dict[int, List[int]]:
        """
        Generate partition mapping for shuffle operations

        Args:
            from_count: Number of source partitions
            to_count: Number of destination partitions
            shuffle_type: Type of shuffle (hash, range, broadcast)

        Returns:
            Mapping of source partition ID -> list of destination partition IDs
        """
        mapping = {}

        if shuffle_type == "broadcast":
            # Broadcast: each source goes to all destinations
            for i in range(from_count):
                mapping[i] = list(range(to_count))
        elif shuffle_type == "hash":
            # Hash partitioning: simulate hash-based distribution
            # For simplicity: each source contributes to all destinations (all-to-all)
            # In real scenario, this would be based on key distribution
            for i in range(from_count):
                mapping[i] = list(range(to_count))
        elif shuffle_type == "range":
            # Range partitioning: ordered distribution
            # Divide source partitions among destination partitions
            sources_per_dest = from_count / to_count if to_count > 0 else 1
            for i in range(from_count):
                dest_idx = min(int(i / sources_per_dest), to_count - 1)
                if i not in mapping:
                    mapping[i] = []
                if dest_idx < to_count:
                    mapping[i].append(dest_idx)
        else:
            # Default: all-to-all
            for i in range(from_count):
                mapping[i] = list(range(to_count))

        return mapping

    def _generate_partitions(self, partition_count: int) -> List[Partition]:
        """
        Generate partition metadata (legacy method, kept for compatibility)
        Note: Use _generate_partitions_with_lineage() for lineage tracking
        """
        partitions = []
        for i in range(partition_count):
            partitions.append(Partition(
                id=i,
                size_mb=2.5,  # Simulated size
                records_count=1000,  # Simulated record count
                data_preview=None,  # Could add sample data
                stage_id=0,  # Default stage
                parent_partitions=[],
                child_partitions=[]
            ))
        return partitions

    def _generate_partitions_with_lineage(
        self,
        stages: List[Stage],
        shuffles: List[Shuffle]
    ) -> List[Partition]:
        """
        Generate partitions with lineage tracking

        Args:
            stages: All execution stages
            shuffles: All shuffle operations

        Returns:
            List of partitions with parent/child relationships
        """
        partitions = []
        partition_id_counter = 0
        partitions_by_stage = {}

        # Create partitions for each stage
        for stage in stages:
            stage_partition_ids = []
            num_partitions = len(stage.tasks)

            for i in range(num_partitions):
                partition = Partition(
                    id=partition_id_counter,
                    size_mb=2.5,  # Simulated size
                    records_count=1000,  # Simulated record count
                    data_preview=None,
                    stage_id=stage.id,
                    parent_partitions=[],
                    child_partitions=[]
                )
                partitions.append(partition)
                stage_partition_ids.append(partition_id_counter)
                partition_id_counter += 1

            partitions_by_stage[stage.id] = stage_partition_ids

        # Build lineage relationships
        self._build_partition_lineage(partitions, partitions_by_stage, stages, shuffles)

        return partitions

    def _build_partition_lineage(
        self,
        partitions: List[Partition],
        partitions_by_stage: Dict[int, List[int]],
        stages: List[Stage],
        shuffles: List[Shuffle]
    ) -> None:
        """
        Build parent/child relationships between partitions based on stage dependencies

        Args:
            partitions: List of all partitions (modified in-place)
            partitions_by_stage: Mapping of stage_id -> list of partition IDs
            stages: All execution stages
            shuffles: All shuffle operations
        """
        # Create partition lookup by ID
        partition_lookup = {p.id: p for p in partitions}

        # Process each stage to determine lineage
        for stage in stages:
            if not stage.dependencies:
                continue  # First stage has no parents

            current_partition_ids = partitions_by_stage[stage.id]

            for parent_stage_id in stage.dependencies:
                parent_partition_ids = partitions_by_stage[parent_stage_id]

                # Check if there's a shuffle between these stages
                shuffle = next(
                    (s for s in shuffles if s.from_stage_id == parent_stage_id and s.to_stage_id == stage.id),
                    None
                )

                if shuffle and shuffle.partition_mapping:
                    # Wide dependency: use partition mapping
                    for parent_id, dest_ids in shuffle.partition_mapping.items():
                        if parent_id not in partition_lookup:
                            continue
                        parent_partition = partition_lookup[parent_id]
                        for dest_id in dest_ids:
                            if dest_id in partition_lookup:
                                child_partition = partition_lookup[dest_id]
                                if parent_id not in child_partition.parent_partitions:
                                    child_partition.parent_partitions.append(parent_id)
                                if dest_id not in parent_partition.child_partitions:
                                    parent_partition.child_partitions.append(dest_id)
                else:
                    # Narrow dependency: 1-to-1 mapping
                    for i, child_id in enumerate(current_partition_ids):
                        parent_id = parent_partition_ids[i % len(parent_partition_ids)]
                        child_partition = partition_lookup[child_id]
                        parent_partition = partition_lookup[parent_id]
                        if parent_id not in child_partition.parent_partitions:
                            child_partition.parent_partitions.append(parent_id)
                        if child_id not in parent_partition.child_partitions:
                            parent_partition.child_partitions.append(child_id)

    def _generate_events(
        self,
        stages: List[Stage],
        shuffles: List[Shuffle]
    ) -> List[SimulationEvent]:
        """Generate timeline events for animation"""
        events = []

        # Stage events
        for stage in stages:
            events.append(SimulationEvent(
                time=stage.start_time,
                event_type="stage_start",
                stage_id=stage.id,
                details={"name": stage.name}
            ))

            # Task events
            for task in stage.tasks:
                events.append(SimulationEvent(
                    time=task.start_time,
                    event_type="task_start",
                    stage_id=stage.id,
                    task_id=task.id,
                    details={"partition": task.partition_id, "node": task.node_id}
                ))
                events.append(SimulationEvent(
                    time=task.end_time,
                    event_type="task_end",
                    stage_id=stage.id,
                    task_id=task.id
                ))

            events.append(SimulationEvent(
                time=stage.end_time,
                event_type="stage_end",
                stage_id=stage.id
            ))

        # Shuffle events
        for shuffle in shuffles:
            events.append(SimulationEvent(
                time=shuffle.start_time,
                event_type="shuffle_start",
                details={
                    "from_stage": shuffle.from_stage_id,
                    "to_stage": shuffle.to_stage_id,
                    "data_mb": shuffle.data_volume_mb
                }
            ))
            events.append(SimulationEvent(
                time=shuffle.end_time,
                event_type="shuffle_end",
                details={
                    "from_stage": shuffle.from_stage_id,
                    "to_stage": shuffle.to_stage_id
                }
            ))

        # Sort events by time
        events.sort(key=lambda e: e.time)

        return events

    def generate_stage_flow(
        self,
        physical_plan: Optional[str],
        logical_plan: Optional[str],
        execution_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate stage-by-stage execution flow for interactive visualization

        Args:
            physical_plan: Spark physical execution plan
            logical_plan: Spark logical query plan

        Returns:
            Dictionary with stages array and metadata
        """
        if not physical_plan:
            return None

        try:
            # Parse physical plan to identify stages and operations
            stages_info = self._parse_physical_plan_detailed(physical_plan)

            # Generate stage flow with educational content
            stages = []
            for idx, stage_info in enumerate(stages_info):
                stage = {
                    'id': idx,
                    'name': stage_info['name'],
                    'operation': stage_info.get('operation_detail', stage_info['name']),
                    'type': stage_info['type'],
                    'input': {
                        'partitionCount': stage_info.get('input_partitions', 4)
                    },
                    'output': {
                        'partitionCount': stage_info.get('output_partitions', 4)
                    },
                    'isShuffle': stage_info.get('has_shuffle', False),
                    'isRepartition': stage_info.get('is_repartition', False),
                    'explanation': self._generate_stage_explanation(stage_info),
                    'performanceNote': self._generate_performance_note(stage_info),
                    'dependencies': [] if idx == 0 else [idx - 1]
                }
                stages.append(stage)

            # Count shuffles
            shuffle_count = sum(1 for s in stages if s['isShuffle'])

            return {
                'stages': stages,
                'shuffleCount': shuffle_count,
                'explanation': self._generate_overall_explanation(stages)
            }

        except Exception as e:
            print(f"Error generating stage flow: {str(e)}")
            return None

    def _extract_partition_count_from_line(self, line: str) -> Optional[int]:
        """
        Extract partition count from a physical plan line
        Examples:
        - "Exchange rangepartitioning(id, 200)" -> 200
        - "Exchange hashpartitioning(key, 4)" -> 4
        """
        # Try to match patterns like "partitioning(..., N)" where N is the partition count
        match = re.search(r'partitioning\([^,]+,\s*(\d+)\)', line)
        if match:
            return int(match.group(1))

        # Try to match patterns like "ENSURE_REQUIREMENTS, [plan_id=X]" preceded by a number
        match = re.search(r',\s*(\d+)\)\s*,\s*ENSURE_REQUIREMENTS', line)
        if match:
            return int(match.group(1))

        return None

    def _parse_physical_plan_detailed(self, physical_plan: str) -> List[Dict[str, Any]]:
        """
        Parse physical plan with detailed stage information

        Returns:
            List of detailed stage info dictionaries
        """
        stages_info = []
        lines = physical_plan.split('\n')

        # Debug: print physical plan to understand structure
        print("=" * 80)
        print("PHYSICAL PLAN ANALYSIS:")
        print("=" * 80)
        print(physical_plan)
        print("=" * 80)

        # Track operations in order
        operations_found = []

        for line in lines:
            line = line.strip()

            # Scan operations
            if re.search(r'(FileScan|Scan|ExistingRDD)', line):
                operations_found.append({
                    'type': 'scan',
                    'name': 'Scan',
                    'detail': line,
                    'has_shuffle': False,
                    'partition_count': None
                })

            # Filter operations
            elif re.search(r'Filter', line):
                operations_found.append({
                    'type': 'transform',
                    'name': 'Filter',
                    'detail': line,
                    'has_shuffle': False,
                    'partition_count': None
                })

            # Project operations
            elif re.search(r'Project', line):
                operations_found.append({
                    'type': 'transform',
                    'name': 'Project',
                    'detail': line,
                    'has_shuffle': False,
                    'partition_count': None
                })

            # Exchange (Shuffle) operations
            elif re.search(r'Exchange', line) and not re.search(r'BroadcastExchange', line):
                is_repartition = 'RoundRobinPartitioning' in line or 'rangepartitioning' in line.lower()
                partition_count = self._extract_partition_count_from_line(line)
                operations_found.append({
                    'type': 'shuffle',
                    'name': 'Exchange (Shuffle)',
                    'detail': line,
                    'has_shuffle': True,
                    'is_repartition': is_repartition,
                    'partition_count': partition_count
                })

            # HashAggregate operations
            elif re.search(r'HashAggregate', line):
                operations_found.append({
                    'type': 'aggregate',
                    'name': 'HashAggregate',
                    'detail': line,
                    'has_shuffle': False,
                    'partition_count': None
                })

            # Join operations
            elif re.search(r'(SortMergeJoin|BroadcastHashJoin)', line):
                join_type = 'BroadcastHashJoin' if 'BroadcastHashJoin' in line else 'SortMergeJoin'
                operations_found.append({
                    'type': 'aggregate',
                    'name': join_type,
                    'detail': line,
                    'has_shuffle': False,
                    'partition_count': None
                })

            # Sort operations
            elif re.search(r'Sort', line):
                operations_found.append({
                    'type': 'transform',
                    'name': 'Sort',
                    'detail': line,
                    'has_shuffle': False,
                    'partition_count': None
                })

        # Convert operations to stages and track partition counts
        if operations_found:
            # Default starting partition count (Spark default for local mode)
            # This can be overridden if we find explicit partition info
            current_partition_count = 8  # Spark local mode default

            # Try to find the initial partition count from the first scan/input
            first_op = operations_found[0] if operations_found else None
            if first_op and first_op.get('type') == 'scan':
                # Check if partition count is mentioned in the scan line
                partition_from_scan = self._extract_partition_count_from_line(first_op.get('detail', ''))
                if partition_from_scan:
                    current_partition_count = partition_from_scan

            for op in operations_found:
                input_partitions = current_partition_count
                output_partitions = current_partition_count

                # Use explicit partition count from Exchange operations
                if op.get('partition_count') is not None:
                    output_partitions = op['partition_count']
                elif op.get('has_shuffle') or op.get('is_repartition'):
                    # If shuffle but no explicit count, keep current count
                    # (Spark usually maintains partition count unless explicitly changed)
                    output_partitions = current_partition_count

                stage_info = {
                    'name': op['name'],
                    'operation_detail': op.get('detail', op['name']),
                    'type': op['type'],
                    'has_shuffle': op.get('has_shuffle', False),
                    'is_repartition': op.get('is_repartition', False),
                    'input_partitions': input_partitions,
                    'output_partitions': output_partitions
                }

                stages_info.append(stage_info)

                # Update current partition count for next stage
                current_partition_count = output_partitions

                # Debug: print extracted partition info
                print(f"Stage: {op['name']} | Input: {input_partitions} | Output: {output_partitions} | Extracted: {op.get('partition_count')}")

        # If no operations found, create default
        if not stages_info:
            stages_info.append({
                'name': 'Data Processing',
                'operation_detail': 'Process DataFrame',
                'type': 'transform',
                'has_shuffle': False,
                'is_repartition': False,
                'input_partitions': 4,
                'output_partitions': 4
            })

        return stages_info

    def _generate_stage_explanation(self, stage_info: Dict[str, Any]) -> str:
        """Generate educational explanation for a stage"""
        stage_type = stage_info.get('type', 'transform')
        stage_name = stage_info.get('name', '')

        explanations = {
            'scan': "This stage reads the initial data from your DataFrame. The data is automatically split into partitions for parallel processing across multiple CPU cores.",

            'transform': f"This stage performs a {stage_name} transformation on your data. Each partition is processed independently, which means no data movement between workers is needed. This is efficient!",

            'shuffle': "⚠️ This is a SHUFFLE operation - data is being reorganized!\n\nWhat's happening:\n• Data from all partitions is being redistributed\n• Required for operations like groupBy, join, or repartition\n• This is expensive because data moves across the network\n\nWhy it's needed:\n• To group related data together in the same partition\n• Required for your aggregation or grouping operation\n\n💡 Tip: Minimize shuffles for better performance!",

            'aggregate': f"This stage performs {stage_name} on your data. If this follows a shuffle, the data has already been grouped correctly, allowing the aggregation to be computed independently on each partition.",

            'output': "This stage collects and outputs the final results of your computation."
        }

        return explanations.get(stage_type, "This stage processes your data as part of the Spark execution plan.")

    def _generate_performance_note(self, stage_info: Dict[str, Any]) -> Optional[str]:
        """Generate performance tips for a stage"""
        if stage_info.get('has_shuffle'):
            return "⚠️ Shuffle operations are expensive. Consider using broadcast joins for small tables or reducing the number of partitions if you have too many."

        if stage_info.get('is_repartition'):
            return "💡 Repartitioning changes the number of partitions. Make sure this is necessary for your use case."

        return None

    def _generate_overall_explanation(self, stages: List[Dict[str, Any]]) -> str:
        """Generate overall execution summary"""
        total_stages = len(stages)
        shuffle_count = sum(1 for s in stages if s['isShuffle'])

        explanation = f"This query executes in {total_stages} stage(s). "

        if shuffle_count == 0:
            explanation += "Great! No shuffles are needed, which means this query is very efficient. Data stays on the same workers throughout execution."
        elif shuffle_count == 1:
            explanation += "There is 1 shuffle operation, which reorganizes data across the cluster. This is necessary for your query but adds some overhead."
        else:
            explanation += f"There are {shuffle_count} shuffle operations. Each shuffle reorganizes data across the cluster, which can be expensive. Consider if all shuffles are necessary."

        return explanation
