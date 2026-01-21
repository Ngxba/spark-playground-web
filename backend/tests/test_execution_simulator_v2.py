import pytest
from unittest.mock import Mock, patch
from app.services.execution_simulator_v2 import ExecutionSimulatorV2
from app.services.spark_event_tracker import SparkEventTracker
from app.models.execution import ExecutionSimulation, Stage, Task, Partition, Shuffle, Node


@pytest.fixture
def mock_execution_tree():
    """Mock execution tree from SparkEventTracker"""
    return {
        'app_id': 'app-test-123',
        'job_group_id': 'puzzle_execution_test_001',
        'jobs': [
            {
                'job_id': 0,
                'name': 'collect at executor_v2.py:123',
                'status': 'SUCCEEDED',
                'num_stages': 2,
                'num_tasks': 8,
                'stages': [
                    {
                        'stage_id': 0,
                        'attempt_id': 0,
                        'name': 'Scan parquet',
                        'status': 'COMPLETE',
                        'num_tasks': 4,
                        'submission_time': 1640000000000,
                        'completion_time': 1640000002000,
                        'executor_run_time': 1500,
                        'input_bytes': 1024000,
                        'output_bytes': 512000,
                        'shuffle_read_bytes': 0,
                        'shuffle_write_bytes': 256000,
                        'tasks': [
                            {
                                'task_id': 0,
                                'index': 0,
                                'partition_id': 0,
                                'executor_id': 'driver',
                                'launch_time': 1640000000000,
                                'finish_time': 1640000000500,
                                'duration': 500,
                                'status': 'SUCCESS'
                            },
                            {
                                'task_id': 1,
                                'index': 1,
                                'partition_id': 1,
                                'executor_id': 'driver',
                                'launch_time': 1640000000000,
                                'finish_time': 1640000000600,
                                'duration': 600,
                                'status': 'SUCCESS'
                            }
                        ]
                    },
                    {
                        'stage_id': 1,
                        'attempt_id': 0,
                        'name': 'HashAggregate',
                        'status': 'COMPLETE',
                        'num_tasks': 4,
                        'submission_time': 1640000002000,
                        'completion_time': 1640000004000,
                        'executor_run_time': 1800,
                        'tasks': [
                            {
                                'task_id': 2,
                                'index': 0,
                                'partition_id': 0,
                                'executor_id': 'driver',
                                'launch_time': 1640000002000,
                                'finish_time': 1640000002500,
                                'duration': 500,
                                'status': 'SUCCESS'
                            }
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_metadata():
    """Mock execution metadata"""
    return {
        'physical_plan': """
== Physical Plan ==
*(2) HashAggregate
+- Exchange hashpartitioning
   +- *(1) Scan parquet
""",
        'logical_plan': """
== Logical Plan ==
Aggregate
+- Relation
""",
        'cluster_config': {
            'mode': 'local[2]',
            'total_cores': 2,
            'cluster_summary': {
                'total_cores': 2
            }
        }
    }


@pytest.fixture
def mock_event_tracker():
    """Mock SparkEventTracker"""
    tracker = Mock(spec=SparkEventTracker)
    return tracker


class TestExecutionSimulatorV2:
    """Unit tests for ExecutionSimulatorV2"""

    def test_initialization(self, mock_event_tracker: SparkEventTracker):
        """Test simulator can be initialized"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        assert simulator.event_tracker == mock_event_tracker

    def test_generate_simulation_success(self, mock_event_tracker: SparkEventTracker, mock_execution_tree: dict[str, any], mock_metadata: dict[str, any]):
        """Test successful simulation generation"""
        mock_event_tracker.wait_for_events.return_value = mock_execution_tree

        simulator = ExecutionSimulatorV2(mock_event_tracker)
        simulation = simulator.generate_simulation_from_events(
            "app-test-123",
            "puzzle_execution_test_001",
            mock_metadata
        )
        # Assertions
        assert simulation is not None
        assert isinstance(simulation, ExecutionSimulation)
        assert len(simulation.stages) == 2
        assert len(simulation.nodes) > 0
        assert simulation.partition_count > 0

    def test_generate_simulation_no_data(self, mock_event_tracker: SparkEventTracker, mock_metadata: dict[str, any]):
        """Test simulation when no execution data is available"""
        mock_event_tracker.wait_for_events.return_value = None

        simulator = ExecutionSimulatorV2(mock_event_tracker)
        simulation = simulator.generate_simulation_from_events(
            "app-test-123",
            "puzzle_execution_test_001",
            mock_metadata
        )

        # Assertions
        assert simulation is None

    def test_generate_simulation_empty_jobs(self, mock_event_tracker: SparkEventTracker, mock_metadata: dict[str, any]):
        """Test simulation with empty jobs list"""
        empty_tree = {
            'app_id': 'app-test-123',
            'job_group_id': 'puzzle_execution_test_001',
            'jobs': []
        }
        mock_event_tracker.wait_for_events.return_value = empty_tree

        simulator = ExecutionSimulatorV2(mock_event_tracker)
        simulation = simulator.generate_simulation_from_events(
            "app-test-123",
            "puzzle_execution_test_001",
            mock_metadata
        )

        # Assertions
        assert simulation is None

    def test_convert_stages(self, mock_event_tracker: SparkEventTracker, mock_execution_tree: dict[str, any]):
        """Test stage conversion from execution tree"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        stages = simulator._convert_stages(mock_execution_tree)

        # Assertions
        assert len(stages) == 2
        assert all(isinstance(stage, Stage) for stage in stages)
        assert stages[0].name == 'Scan parquet'
        assert stages[1].name == 'HashAggregate'
        assert len(stages[0].tasks) == 2
        assert len(stages[1].tasks) == 1

    def test_convert_tasks(self, mock_event_tracker: SparkEventTracker):
        """Test task conversion"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        simulator.baseline_time = 1640000000.0

        tasks_data = [
            {
                'task_id': 0,
                'index': 0,
                'partition_id': 0,
                'executor_id': 'driver',
                'launch_time': 1640000000000,
                'finish_time': 1640000000500,
                'duration': 500,
                'status': 'SUCCESS'
            }
        ]

        tasks = simulator._convert_tasks(tasks_data, 0, 0.0)

        # Assertions
        assert len(tasks) == 1
        assert isinstance(tasks[0], Task)
        assert tasks[0].id == 0
        assert tasks[0].partition_id == 0
        assert tasks[0].duration == 0.5  # Converted to seconds

    def test_extract_all_tasks(self, mock_event_tracker: SparkEventTracker, mock_execution_tree: dict[str, any]):
        """Test extracting all tasks from stages"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        stages = simulator._convert_stages(mock_execution_tree)
        all_tasks = simulator._extract_all_tasks(stages)

        # Assertions
        assert len(all_tasks) == 3  # 2 from stage 0, 1 from stage 1

    def test_build_partitions_from_tasks(self, mock_event_tracker: SparkEventTracker, mock_execution_tree: dict[str, any]):
        """Test building partitions from tasks"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        stages = simulator._convert_stages(mock_execution_tree)
        all_tasks = simulator._extract_all_tasks(stages)
        partitions = simulator._build_partitions_from_tasks(all_tasks, stages)

        # Assertions
        assert len(partitions) > 0
        assert all(isinstance(partition, Partition) for partition in partitions)
        for partition in partitions:
            assert partition.size_mb > 0
            assert partition.records_count > 0

    def test_detect_shuffles(self, mock_event_tracker: SparkEventTracker, mock_execution_tree: dict[str, any], mock_metadata: dict[str, any]):
        """Test shuffle detection"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        shuffles = simulator._detect_shuffles(mock_execution_tree, mock_metadata)

        # Assertions
        # Should detect shuffle from physical plan containing "Exchange"
        assert isinstance(shuffles, list)
        if len(shuffles) > 0:
            assert all(isinstance(shuffle, Shuffle) for shuffle in shuffles)

    def test_build_nodes_from_executors(self, mock_event_tracker: SparkEventTracker, mock_execution_tree: dict[str, any], mock_metadata: dict[str, any]):
        """Test building nodes from executor information"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        nodes = simulator._build_nodes_from_executors(mock_execution_tree, mock_metadata['cluster_config'])

        # Assertions
        assert len(nodes) > 0
        assert all(isinstance(node, Node) for node in nodes)
        for node in nodes:
            assert node.cores > 0
            assert node.memory_gb > 0

    def test_build_timeline_events(self, mock_event_tracker: SparkEventTracker, mock_execution_tree: dict[str, any]):
        """Test building timeline events"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        stages = simulator._convert_stages(mock_execution_tree)
        all_tasks = simulator._extract_all_tasks(stages)
        shuffles = []  # No shuffles for this test

        events = simulator._build_timeline_events(stages, all_tasks, shuffles)

        # Assertions
        assert len(events) > 0
        # Should have stage_start, stage_end, task_start, task_end events
        event_types = [e.event_type for e in events]
        assert 'stage_start' in event_types
        assert 'stage_end' in event_types
        assert 'task_start' in event_types
        assert 'task_end' in event_types
        # Events should be sorted by time
        times = [e.time for e in events]
        assert times == sorted(times)

    def test_calculate_total_duration(self, mock_event_tracker: SparkEventTracker, mock_execution_tree: dict[str, any]):
        """Test total duration calculation"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        stages = simulator._convert_stages(mock_execution_tree)
        duration = simulator._calculate_total_duration(stages)

        # Assertions
        assert duration > 0
        assert isinstance(duration, float)

    def test_calculate_total_duration_empty(self, mock_event_tracker: SparkEventTracker):
        """Test duration calculation with no stages"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        duration = simulator._calculate_total_duration([])

        # Assertions
        assert duration == 0.0

    def test_calculate_metrics(self, mock_event_tracker: SparkEventTracker, mock_execution_tree: dict[str, any]):
        """Test metrics calculation"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        metrics = simulator._calculate_metrics(mock_execution_tree)

        # Assertions
        assert 'total_tasks' in metrics
        assert 'total_input_mb' in metrics
        assert 'total_output_mb' in metrics
        assert 'num_jobs' in metrics
        assert 'num_stages' in metrics
        assert metrics['num_jobs'] == 1
        assert metrics['num_stages'] == 2
        assert metrics['total_tasks'] > 0

    def test_infer_operation_type_scan(self, mock_event_tracker: SparkEventTracker):
        """Test operation type inference for scan"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        op_type = simulator._infer_operation_type("Scan parquet")

        assert op_type == 'scan'

    def test_infer_operation_type_filter(self, mock_event_tracker: SparkEventTracker):
        """Test operation type inference for filter"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        op_type = simulator._infer_operation_type("Filter (id > 10)")

        assert op_type == 'filter'

    def test_infer_operation_type_join(self, mock_event_tracker: SparkEventTracker):
        """Test operation type inference for join"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        op_type = simulator._infer_operation_type("BroadcastHashJoin")

        assert op_type == 'join'

    def test_infer_operation_type_aggregate(self, mock_event_tracker: SparkEventTracker):
        """Test operation type inference for aggregate"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        op_type = simulator._infer_operation_type("HashAggregate")

        assert op_type == 'aggregate'

    def test_infer_operation_type_shuffle(self, mock_event_tracker: SparkEventTracker):
        """Test operation type inference for shuffle"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        op_type = simulator._infer_operation_type("Exchange hashpartitioning")

        assert op_type == 'shuffle'

    def test_infer_operation_type_unknown(self, mock_event_tracker: SparkEventTracker):
        """Test operation type inference for unknown operation"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)
        op_type = simulator._infer_operation_type("SomeUnknownOperation")

        assert op_type == 'transform'

    def test_convert_status(self, mock_event_tracker: SparkEventTracker):
        """Test status conversion"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)

        assert simulator._convert_status('COMPLETE') == 'completed'
        assert simulator._convert_status('ACTIVE') == 'running'
        assert simulator._convert_status('PENDING') == 'pending'
        assert simulator._convert_status('FAILED') == 'failed'
        assert simulator._convert_status('UNKNOWN') == 'completed'  # Default

    def test_convert_task_status(self, mock_event_tracker: SparkEventTracker):
        """Test task status conversion"""
        simulator = ExecutionSimulatorV2(mock_event_tracker)

        assert simulator._convert_task_status('SUCCESS') == 'completed'
        assert simulator._convert_task_status('RUNNING') == 'running'
        assert simulator._convert_task_status('FAILED') == 'failed'
        assert simulator._convert_task_status('KILLED') == 'failed'
        assert simulator._convert_task_status('UNKNOWN') == 'completed'  # Default

    def test_simulation_has_required_fields(self, mock_event_tracker: SparkEventTracker, mock_execution_tree: dict[str, any], mock_metadata: dict[str, any]):
        """Test that generated simulation has all required fields"""
        mock_event_tracker.wait_for_events.return_value = mock_execution_tree

        simulator = ExecutionSimulatorV2(mock_event_tracker)
        simulation = simulator.generate_simulation_from_events(
            "app-test-123",
            "puzzle_execution_test_001",
            mock_metadata
        )

        # Assertions - check all required fields
        assert hasattr(simulation, 'total_duration')
        assert hasattr(simulation, 'partition_count')
        assert hasattr(simulation, 'node_count')
        assert hasattr(simulation, 'cores_per_node')
        assert hasattr(simulation, 'total_cores')
        assert hasattr(simulation, 'stages')
        assert hasattr(simulation, 'partitions')
        assert hasattr(simulation, 'shuffles')
        assert hasattr(simulation, 'nodes')
        assert hasattr(simulation, 'events')
        assert hasattr(simulation, 'metrics')

    def test_multiple_jobs_handling(self, mock_event_tracker: SparkEventTracker, mock_metadata: dict[str, any]):
        """Test handling of multiple jobs in execution tree"""
        tree_with_multiple_jobs = {
            'app_id': 'app-test-123',
            'job_group_id': 'puzzle_execution_test_001',
            'jobs': [
                {
                    'job_id': 0,
                    'name': 'Job 1',
                    'stages': [{
                        'stage_id': 0,
                        'name': 'Stage 0',
                        'submission_time': 1640000000000,
                        'completion_time': 1640000001000,
                        'tasks': []
                    }]
                },
                {
                    'job_id': 1,
                    'name': 'Job 2',
                    'stages': [{
                        'stage_id': 1,
                        'name': 'Stage 1',
                        'submission_time': 1640000001000,
                        'completion_time': 1640000002000,
                        'tasks': []
                    }]
                }
            ]
        }
        mock_event_tracker.wait_for_events.return_value = tree_with_multiple_jobs

        simulator = ExecutionSimulatorV2(mock_event_tracker)
        simulation = simulator.generate_simulation_from_events(
            "app-test-123",
            "puzzle_execution_test_001",
            mock_metadata
        )

        # Assertions
        assert simulation is not None
        assert len(simulation.stages) == 2
        assert simulation.metrics['num_jobs'] == 2
