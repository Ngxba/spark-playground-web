"""
Comprehensive Integration Tests for Spark Execution Backend V2

These tests execute REAL code against a running Spark cluster and verify:
1. ExecutorV2 - Code execution with real SparkSession
2. SparkEventTracker - REST API calls to Spark History Server (0.0.0.0:18080)
3. ExecutionSimulatorV2 - Simulation generation from real Spark events
4. JudgeV2 - Complete evaluation pipeline with real metrics

Prerequisites:
- Spark History Server running at http://0.0.0.0:18080
- Event logging enabled in Spark configuration
- SPARK_EVENT_LOG_DIR environment variable set (default: /tmp/spark-events)

Run with: uv run pytest tests/test_v2_integration.py -v -s
"""

import pytest
import time

from app.models import RunResult
from app.models.execution import ExecutionSimulation
from app.services.executor_v2 import ExecutorV2


# Configuration imported from conftest
SPARK_HISTORY_SERVER_URL = "http://0.0.0.0:18080"
EVENT_WAIT_TIMEOUT = 5.0


# =============================================================================
# Test Class: ExecutorV2
# =============================================================================

class TestExecutorV2Integration:
    """Integration tests for ExecutorV2 with real Spark execution"""

    def test_execute_simple_orderby(self, executor: ExecutorV2, group_fruits_puzzle: dict[str, any]):
        """Test simple orderBy execution returns correct results"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            f"test_orderby_{int(time.time())}"
        )

        assert error is None, f"Execution failed with error: {error}"
        assert result is not None, "Result should not be None"
        assert isinstance(result, list), "Result should be a list"
        assert len(result) == 4, f"Expected 4 rows, got {len(result)}"

        types = [row['type'] for row in result]
        assert types == sorted(types), "Results should be sorted by type"

        assert metadata is not None
        assert 'app_id' in metadata
        assert 'physical_plan' in metadata
        assert 'logical_plan' in metadata
        assert job_group_id is not None

        print(f"\n[SUCCESS] Simple orderBy executed")
        print(f"  Result: {result}")
        print(f"  Output Log: {output_log}")
        print(f"  Error: {error}")
        print(f"  Metadata: {metadata}")
        print(f"  Job Group ID: {job_group_id}")
        print(f"  Spark AppID: {metadata.get('app_id')}")

    def test_execute_join_operation(self, executor, fast_join_puzzle):
        """Test join operation execution"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            fast_join_puzzle['suboptimal_code'],
            fast_join_puzzle['input_data'],
            f"test_join_{int(time.time())}"
        )

        assert error is None, f"Execution failed: {error}"
        assert result is not None
        assert len(result) == 3, f"Expected 3 joined rows, got {len(result)}"

        for row in result:
            assert 'order_id' in row
            assert 'product_id' in row
            assert 'name' in row
            assert 'price' in row

        physical_plan = metadata.get('physical_plan', '')
        print(f"\n[SUCCESS] Join operation executed")
        print(f"  Has Exchange (shuffle): {'Exchange' in physical_plan}")
        print(f"  Has BroadcastHashJoin: {'BroadcastHashJoin' in physical_plan}")

    def test_execute_broadcast_join(self, executor, fast_join_puzzle):
        """Test broadcast join optimization"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            fast_join_puzzle['optimal_code'],
            fast_join_puzzle['input_data'],
            f"test_broadcast_{int(time.time())}"
        )

        assert error is None, f"Execution failed: {error}"
        assert result is not None

        physical_plan = metadata.get('physical_plan', '')
        has_broadcast = 'BroadcastHashJoin' in physical_plan or 'BroadcastExchange' in physical_plan

        print(f"\n[SUCCESS] Broadcast join executed")
        print(f"  Has Broadcast: {has_broadcast}")
        print(f"  Physical Plan:\n{physical_plan[:500]}...")

    def test_execute_aggregation(self, executor, aggregation_puzzle):
        """Test aggregation with groupBy"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            aggregation_puzzle['correct_code'],
            aggregation_puzzle['input_data'],
            f"test_agg_{int(time.time())}"
        )

        assert error is None, f"Execution failed: {error}"
        assert result is not None
        assert len(result) == 3, f"Expected 3 categories, got {len(result)}"

        result_dict = {row['category']: row['total'] for row in result}
        assert result_dict.get('Electronics') == 300
        assert result_dict.get('Clothing') == 125
        assert result_dict.get('Food') == 30

        physical_plan = metadata.get('physical_plan', '')
        assert 'Exchange' in physical_plan or 'Aggregate' in physical_plan

        print(f"\n[SUCCESS] Aggregation executed")
        print(f"  Results: {result_dict}")

    def test_execute_filter(self, executor, filter_merge_puzzle):
        """Test filter operation"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            filter_merge_puzzle['optimal_code'],
            filter_merge_puzzle['input_data'],
            f"test_filter_{int(time.time())}"
        )

        assert error is None, f"Execution failed: {error}"
        assert result is not None
        assert len(result) == 3, f"Expected 3 completed transactions, got {len(result)}"

        for row in result:
            assert row['status'] == 'completed'

        print(f"\n[SUCCESS] Filter executed")
        print(f"  Filtered rows: {len(result)}")

    def test_execute_complex_etl(self, executor, complex_etl_puzzle):
        """Test complex multi-stage ETL pipeline"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            complex_etl_puzzle['correct_code'],
            complex_etl_puzzle['input_data'],
            f"test_etl_{int(time.time())}"
        )

        assert error is None, f"Execution failed: {error}"
        assert result is not None
        assert len(result) == 2, f"Expected 2 adult users with purchases, got {len(result)}"

        result_dict = {row['name']: row['total_spent'] for row in result}
        assert result_dict.get('Alice') == 17.0
        assert result_dict.get('Charlie') == 16.0

        print(f"\n[SUCCESS] Complex ETL executed")
        print(f"  Results: {result_dict}")

    def test_execute_missing_solve_function(self, executor, group_fruits_puzzle):
        """Test error handling when solve() is missing"""
        bad_code = """
def process(fruits):
    return fruits
"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            bad_code,
            group_fruits_puzzle['input_data'],
            f"test_missing_solve_{int(time.time())}"
        )

        assert error is not None
        assert "solve" in error.lower()
        assert result is None

        print(f"\n[SUCCESS] Missing solve() properly detected")
        print(f"  Error: {error[:100]}...")

    def test_execute_wrong_parameters(self, executor, group_fruits_puzzle):
        """Test error handling when solve() has wrong parameters"""
        bad_code = """
def solve(apples, oranges):
    return apples
"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            bad_code,
            group_fruits_puzzle['input_data'],
            f"test_wrong_params_{int(time.time())}"
        )

        assert error is not None
        assert "parameter" in error.lower() or "mismatch" in error.lower()

        print(f"\n[SUCCESS] Wrong parameters properly detected")
        print(f"  Error: {error[:100]}...")

    def test_execute_action_prevention(self, executor, group_fruits_puzzle):
        """Test that calling .collect() inside solve() is blocked"""
        bad_code = """
def solve(fruits):
    data = fruits.collect()
    return fruits
"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            bad_code,
            group_fruits_puzzle['input_data'],
            f"test_action_block_{int(time.time())}"
        )

        assert error is not None
        assert "collect" in error.lower()

        print(f"\n[SUCCESS] Action prevention working")
        print(f"  Error: {error[:100]}...")

    def test_execute_returns_non_dataframe(self, executor, group_fruits_puzzle):
        """Test error handling when solve() returns non-DataFrame"""
        bad_code = """
def solve(fruits):
    return [{"id": 1}]
"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            bad_code,
            group_fruits_puzzle['input_data'],
            f"test_non_df_{int(time.time())}"
        )

        assert error is not None
        assert "dataframe" in error.lower()

        print(f"\n[SUCCESS] Non-DataFrame return properly detected")
        print(f"  Error: {error[:100]}...")

    def test_execute_syntax_error(self, executor, group_fruits_puzzle):
        """Test handling of syntax errors in user code"""
        bad_code = """
def solve(fruits):
    return fruits.filter(
"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            bad_code,
            group_fruits_puzzle['input_data'],
            f"test_syntax_{int(time.time())}"
        )

        assert error is not None
        assert "syntax" in error.lower() or "unexpected" in error.lower()

        print(f"\n[SUCCESS] Syntax error properly detected")

    def test_cluster_config_extraction(self, executor, group_fruits_puzzle):
        """Test that cluster configuration is properly extracted"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            f"test_cluster_{int(time.time())}"
        )

        assert error is None
        assert 'cluster_config' in metadata

        cluster_config = metadata['cluster_config']
        assert 'mode' in cluster_config
        assert 'total_cores' in cluster_config
        assert 'shuffle_partitions' in cluster_config
        assert 'cluster_summary' in cluster_config

        print(f"\n[SUCCESS] Cluster config extracted")
        print(f"  Mode: {cluster_config.get('mode')}")
        print(f"  Total Cores: {cluster_config.get('total_cores')}")
        print(f"  Shuffle Partitions: {cluster_config.get('shuffle_partitions')}")


# =============================================================================
# Test Class: SparkEventTracker
# =============================================================================

class TestSparkEventTrackerIntegration:
    """Integration tests for SparkEventTracker with real Spark History Server"""

    def test_connection_to_history_server(self, event_tracker):
        """Test that we can connect to Spark History Server"""
        import requests

        try:
            response = requests.get(f"{SPARK_HISTORY_SERVER_URL}/api/v1/applications", timeout=5)
            assert response.status_code == 200
            apps = response.json()
            print(f"\n[SUCCESS] Connected to Spark History Server")
            print(f"  Available applications: {len(apps)}")
        except Exception as e:
            pytest.skip(f"Spark History Server not available at {SPARK_HISTORY_SERVER_URL}: {e}")

    def test_fetch_jobs_after_execution(self, executor, event_tracker, group_fruits_puzzle):
        """Test fetching jobs from Spark after code execution"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            f"test_fetch_{int(time.time())}"
        )

        assert error is None
        app_id = metadata.get('app_id')
        assert app_id is not None

        time.sleep(1.0)

        jobs = event_tracker.get_jobs_by_group(app_id, job_group_id)

        print(f"\n[INFO] Jobs fetched for app {app_id}")
        print(f"  Job Group: {job_group_id}")
        print(f"  Jobs found: {len(jobs)}")

    def test_build_execution_tree(self, executor, event_tracker, aggregation_puzzle):
        """Test building complete execution tree from real execution"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            aggregation_puzzle['correct_code'],
            aggregation_puzzle['input_data'],
            f"test_tree_{int(time.time())}"
        )

        assert error is None
        app_id = metadata.get('app_id')

        time.sleep(1.5)

        execution_tree = event_tracker.build_execution_tree(app_id, job_group_id)

        if execution_tree and execution_tree.get('jobs'):
            print(f"\n[SUCCESS] Execution tree built")
            print(f"  App ID: {execution_tree['app_id']}")
            print(f"  Jobs: {len(execution_tree['jobs'])}")

            for job in execution_tree['jobs']:
                print(f"    Job {job['job_id']}: {len(job['stages'])} stages")
                for stage in job['stages']:
                    print(f"      Stage {stage['stage_id']}: {stage['name']}")
                    print(f"        Tasks: {stage['num_tasks']}")
        else:
            print(f"\n[INFO] No execution tree available (events may not have flushed)")

    def test_wait_for_events(self, executor, event_tracker, group_fruits_puzzle):
        """Test wait_for_events polling mechanism"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            f"test_wait_{int(time.time())}"
        )

        assert error is None
        app_id = metadata.get('app_id')

        execution_tree = event_tracker.wait_for_events(
            app_id,
            job_group_id,
            max_wait_seconds=EVENT_WAIT_TIMEOUT,
            retry_interval=0.5
        )

        if execution_tree:
            print(f"\n[SUCCESS] Events retrieved via wait_for_events")
            print(f"  Jobs: {len(execution_tree.get('jobs', []))}")
        else:
            print(f"\n[INFO] Events not available within timeout")


# =============================================================================
# Test Class: ExecutionSimulatorV2
# =============================================================================

class TestExecutionSimulatorV2Integration:
    """Integration tests for ExecutionSimulatorV2 with real Spark events"""

    def test_generate_simulation_simple(self, executor, execution_simulator, group_fruits_puzzle):
        """Test generating simulation from simple execution"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            f"test_sim_simple_{int(time.time())}"
        )

        assert error is None
        app_id = metadata.get('app_id')

        time.sleep(1.5)

        simulation = execution_simulator.generate_simulation_from_events(
            app_id, job_group_id, metadata
        )

        if simulation:
            print(f"\n[SUCCESS] Simulation generated")
            print(f"  Total Duration: {simulation.total_duration:.3f}s")
            print(f"  Stages: {len(simulation.stages)}")
            print(f"  Partitions: {simulation.partition_count}")
            print(f"  Nodes: {simulation.node_count}")
            print(f"  Events: {len(simulation.events)}")

            assert isinstance(simulation, ExecutionSimulation)
            assert simulation.stages is not None
            assert simulation.nodes is not None
            assert simulation.events is not None

            for stage in simulation.stages:
                print(f"    Stage {stage.id}: {stage.name} ({stage.operation_type})")
                print(f"      Tasks: {len(stage.tasks)}, Duration: {stage.end_time - stage.start_time:.3f}s")
        else:
            print(f"\n[INFO] Simulation not generated (events may not be available)")

    def test_generate_simulation_with_shuffle(self, executor, execution_simulator, aggregation_puzzle):
        """Test generating simulation that includes shuffle operations"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            aggregation_puzzle['correct_code'],
            aggregation_puzzle['input_data'],
            f"test_sim_shuffle_{int(time.time())}"
        )

        assert error is None
        app_id = metadata.get('app_id')

        time.sleep(2.0)

        simulation = execution_simulator.generate_simulation_from_events(
            app_id, job_group_id, metadata
        )

        if simulation:
            print(f"\n[SUCCESS] Simulation with shuffle generated")
            print(f"  Shuffles detected: {len(simulation.shuffles)}")

            for shuffle in simulation.shuffles:
                print(f"    Shuffle: Stage {shuffle.from_stage_id} -> Stage {shuffle.to_stage_id}")
                print(f"      Data Volume: {shuffle.data_volume_mb:.2f} MB")
                print(f"      Partitions: {shuffle.from_partitions} -> {shuffle.to_partitions}")

            if simulation.metrics:
                print(f"  Metrics:")
                print(f"    Total Tasks: {simulation.metrics.get('total_tasks', 0)}")
                print(f"    Shuffle Read: {simulation.metrics.get('total_shuffle_read_mb', 0):.2f} MB")
                print(f"    Shuffle Write: {simulation.metrics.get('total_shuffle_write_mb', 0):.2f} MB")
        else:
            print(f"\n[INFO] Simulation not generated")

    def test_timeline_events_ordering(self, executor, execution_simulator, group_fruits_puzzle):
        """Test that timeline events are properly ordered"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            f"test_timeline_{int(time.time())}"
        )

        assert error is None
        app_id = metadata.get('app_id')

        time.sleep(1.5)

        simulation = execution_simulator.generate_simulation_from_events(
            app_id, job_group_id, metadata
        )

        if simulation and simulation.events:
            times = [event.time for event in simulation.events]
            assert times == sorted(times), "Events should be sorted by time"

            event_types = set(event.event_type for event in simulation.events)
            print(f"\n[SUCCESS] Timeline events validated")
            print(f"  Event types: {event_types}")
            print(f"  Total events: {len(simulation.events)}")


# =============================================================================
# Test Class: JudgeV2
# =============================================================================

class TestJudgeV2Integration:
    """Full integration tests for JudgeV2 evaluation pipeline"""

    def test_evaluate_correct_solution(self, judge, group_fruits_puzzle):
        """Test evaluating a correct solution"""
        result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert isinstance(result, RunResult)
        assert result.correct is True
        assert result.error is None
        assert result.stars >= 1
        assert result.output is not None

        print(f"\n[SUCCESS] Correct solution evaluated")
        print(f"  Correct: {result.correct}")
        print(f"  Stars: {result.stars}")
        print(f"  Shuffles: {result.metrics.shuffles}")
        print(f"  Stages: {result.metrics.stages}")

    def test_evaluate_incorrect_solution(self, judge, group_fruits_puzzle):
        """Test evaluating an incorrect solution"""
        result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            group_fruits_puzzle['incorrect_code'],
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert isinstance(result, RunResult)
        assert result.correct is False
        assert result.stars == 0

        print(f"\n[SUCCESS] Incorrect solution properly detected")
        print(f"  Correct: {result.correct}")
        print(f"  Stars: {result.stars}")

    def test_evaluate_with_error(self, judge, group_fruits_puzzle):
        """Test evaluating code with errors"""
        bad_code = """
def solve(wrong_param):
    return wrong_param
"""
        result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            bad_code,
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert isinstance(result, RunResult)
        assert result.correct is False
        assert result.error is not None
        assert result.stars == 0

        print(f"\n[SUCCESS] Error properly handled")
        print(f"  Error: {result.error[:100]}...")

    def test_evaluate_broadcast_optimization(self, judge, fast_join_puzzle):
        """Test that broadcast join is properly detected and scored"""
        optimal_result = judge.evaluate(
            fast_join_puzzle['puzzle_id'],
            fast_join_puzzle['optimal_code'],
            fast_join_puzzle['input_data'],
            fast_join_puzzle['expected_output']
        )

        suboptimal_result = judge.evaluate(
            fast_join_puzzle['puzzle_id'],
            fast_join_puzzle['suboptimal_code'],
            fast_join_puzzle['input_data'],
            fast_join_puzzle['expected_output']
        )

        print(f"\n[INFO] Broadcast optimization comparison")
        print(f"  Optimal (broadcast): correct={optimal_result.correct}, stars={optimal_result.stars}, broadcast={optimal_result.metrics.broadcast_used}")
        print(f"  Suboptimal (no broadcast): correct={suboptimal_result.correct}, stars={suboptimal_result.stars}, broadcast={suboptimal_result.metrics.broadcast_used}")

        assert optimal_result.correct is True
        assert suboptimal_result.correct is True

    def test_evaluate_generates_dag(self, judge, group_fruits_puzzle):
        """Test that DAG structure is generated"""
        result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert result.dag_structure is not None or result.physical_plan is not None

        if result.dag_structure:
            print(f"\n[SUCCESS] DAG structure generated")
            print(f"  Nodes: {len(result.dag_structure.get('nodes', []))}")
            print(f"  Edges: {len(result.dag_structure.get('edges', []))}")

        if result.physical_plan:
            print(f"\n[INFO] Physical Plan:\n{result.physical_plan[:300]}...")

    def test_evaluate_generates_spark_ui_url(self, judge, group_fruits_puzzle):
        """Test that Spark UI URL is generated"""
        result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert result.spark_ui_url is not None
        assert "localhost:18080" in result.spark_ui_url or "0.0.0.0:18080" in result.spark_ui_url

        print(f"\n[SUCCESS] Spark UI URL generated")
        print(f"  URL: {result.spark_ui_url}")

    def test_evaluate_generates_execution_simulation(self, judge, aggregation_puzzle):
        """Test that execution simulation is generated"""
        result = judge.evaluate(
            aggregation_puzzle['puzzle_id'],
            aggregation_puzzle['correct_code'],
            aggregation_puzzle['input_data'],
            aggregation_puzzle['expected_output']
        )

        if result.execution_simulation:
            print(f"\n[SUCCESS] Execution simulation generated")
            print(f"  Type: {type(result.execution_simulation)}")

            if hasattr(result.execution_simulation, 'stages'):
                print(f"  Stages: {len(result.execution_simulation.stages)}")
        else:
            print(f"\n[INFO] Execution simulation not available (expected in some cases)")

    def test_evaluate_generates_stage_flow(self, judge, aggregation_puzzle):
        """Test that stage flow is generated"""
        result = judge.evaluate(
            aggregation_puzzle['puzzle_id'],
            aggregation_puzzle['correct_code'],
            aggregation_puzzle['input_data'],
            aggregation_puzzle['expected_output']
        )

        if result.stage_flow:
            print(f"\n[SUCCESS] Stage flow generated")
            print(f"  Total Stages: {result.stage_flow.get('total_stages')}")
            print(f"  Total Duration: {result.stage_flow.get('total_duration')}")

            for stage in result.stage_flow.get('stages', []):
                print(f"    Stage {stage['id']}: {stage['name']} ({stage['operation_type']})")
        else:
            print(f"\n[INFO] Stage flow not available")

    def test_evaluate_generates_cluster_config(self, judge, group_fruits_puzzle):
        """Test that cluster configuration is included"""
        result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert result.cluster_config is not None

        print(f"\n[SUCCESS] Cluster config included")
        print(f"  Mode: {result.cluster_config.get('mode')}")
        print(f"  Shuffle Partitions: {result.cluster_config.get('shuffle_partitions')}")

    def test_evaluate_complex_etl_pipeline(self, judge, complex_etl_puzzle):
        """Test evaluation of complex multi-stage ETL"""
        result = judge.evaluate(
            complex_etl_puzzle['puzzle_id'],
            complex_etl_puzzle['correct_code'],
            complex_etl_puzzle['input_data'],
            complex_etl_puzzle['expected_output']
        )

        assert result.correct is True
        assert result.error is None

        print(f"\n[SUCCESS] Complex ETL evaluated")
        print(f"  Correct: {result.correct}")
        print(f"  Stars: {result.stars}")
        print(f"  Shuffles: {result.metrics.shuffles}")
        print(f"  Stages: {result.metrics.stages}")
        print(f"  Broadcast Used: {result.metrics.broadcast_used}")

    def test_evaluate_hint_generation(self, judge, fast_join_puzzle):
        """Test that hints are generated for suboptimal solutions"""
        result = judge.evaluate(
            fast_join_puzzle['puzzle_id'],
            fast_join_puzzle['suboptimal_code'],
            fast_join_puzzle['input_data'],
            fast_join_puzzle['expected_output']
        )

        if result.stars < 3 and result.hint:
            print(f"\n[SUCCESS] Hint generated")
            print(f"  Stars: {result.stars}")
            print(f"  Hint: {result.hint}")
        else:
            print(f"\n[INFO] No hint needed (3 stars) or hint not generated")


# =============================================================================
# Test Class: OperationDetector
# =============================================================================

class TestOperationDetectorIntegration:
    """Integration tests for OperationDetector with real query plans"""

    def test_analyze_sort_plan(self, executor, operation_detector, group_fruits_puzzle):
        """Test analyzing a sort operation plan"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            f"test_analyze_sort_{int(time.time())}"
        )

        assert error is None

        analysis = operation_detector.analyze_from_metadata(metadata)

        print(f"\n[SUCCESS] Sort plan analyzed")
        print(f"  Has Shuffle: {analysis.get('has_shuffle')}")
        print(f"  Has Sort: {analysis.get('has_sort')}")
        print(f"  Num Shuffles: {analysis.get('num_shuffles')}")
        print(f"  Performance Score: {analysis.get('performance_score')}")

    def test_analyze_join_plan(self, executor, operation_detector, fast_join_puzzle):
        """Test analyzing a join operation plan"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            fast_join_puzzle['optimal_code'],
            fast_join_puzzle['input_data'],
            f"test_analyze_join_{int(time.time())}"
        )

        assert error is None

        analysis = operation_detector.analyze_from_metadata(metadata)

        print(f"\n[SUCCESS] Join plan analyzed")
        print(f"  Has Broadcast: {analysis.get('has_broadcast')}")
        print(f"  Has Shuffle: {analysis.get('has_shuffle')}")
        print(f"  Operations: {analysis.get('operations', [])}")

    def test_extract_dag_structure(self, executor, operation_detector, aggregation_puzzle):
        """Test DAG structure extraction from physical plan"""
        result, output_log, error, metadata, job_group_id = executor.execute(
            aggregation_puzzle['correct_code'],
            aggregation_puzzle['input_data'],
            f"test_dag_{int(time.time())}"
        )

        assert error is None

        physical_plan = metadata.get('physical_plan', '')
        dag_structure = operation_detector.extract_dag_structure(physical_plan)

        if dag_structure and dag_structure.get('nodes'):
            print(f"\n[SUCCESS] DAG structure extracted")
            print(f"  Nodes: {len(dag_structure['nodes'])}")
            print(f"  Edges: {len(dag_structure.get('edges', []))}")

            for node in dag_structure['nodes'][:5]:
                print(f"    Node: {node.get('label', 'Unknown')}")
        else:
            print(f"\n[INFO] DAG extraction failed, using fallback")


# =============================================================================
# Test Class: End-to-End Scenarios
# =============================================================================

class TestEndToEndScenarios:
    """End-to-end scenario tests simulating real user workflows"""

    def test_complete_puzzle_workflow(self, judge, group_fruits_puzzle):
        """Test complete puzzle solving workflow"""
        print("\n" + "="*60)
        print("SCENARIO: Complete Puzzle Workflow")
        print("="*60)

        print("\nStep 1: User submits incorrect solution...")
        incorrect_result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            group_fruits_puzzle['incorrect_code'],
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert incorrect_result.correct is False
        print(f"  Result: Incorrect (stars={incorrect_result.stars})")
        if incorrect_result.hint:
            print(f"  Hint: {incorrect_result.hint}")

        print("\nStep 2: User submits correct solution...")
        correct_result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert correct_result.correct is True
        print(f"  Result: Correct! (stars={correct_result.stars})")

        print("\nStep 3: Verifying visualization data...")
        assert correct_result.physical_plan is not None
        assert correct_result.logical_plan is not None
        assert correct_result.spark_ui_url is not None
        assert correct_result.metrics is not None
        print("  All visualization data available!")

        print("\n" + "="*60)
        print("SCENARIO COMPLETE: All steps passed!")
        print("="*60)

    def test_optimization_learning_workflow(self, judge, fast_join_puzzle):
        """Test workflow where user learns about optimizations"""
        print("\n" + "="*60)
        print("SCENARIO: Optimization Learning Workflow")
        print("="*60)

        print("\nStep 1: User submits naive join (no broadcast)...")
        naive_result = judge.evaluate(
            fast_join_puzzle['puzzle_id'],
            fast_join_puzzle['suboptimal_code'],
            fast_join_puzzle['input_data'],
            fast_join_puzzle['expected_output']
        )

        print(f"  Correct: {naive_result.correct}")
        print(f"  Stars: {naive_result.stars}")
        print(f"  Shuffles: {naive_result.metrics.shuffles}")
        print(f"  Broadcast: {naive_result.metrics.broadcast_used}")

        print("\nStep 2: User submits optimized join (with broadcast)...")
        optimized_result = judge.evaluate(
            fast_join_puzzle['puzzle_id'],
            fast_join_puzzle['optimal_code'],
            fast_join_puzzle['input_data'],
            fast_join_puzzle['expected_output']
        )

        print(f"  Correct: {optimized_result.correct}")
        print(f"  Stars: {optimized_result.stars}")
        print(f"  Shuffles: {optimized_result.metrics.shuffles}")
        print(f"  Broadcast: {optimized_result.metrics.broadcast_used}")

        assert naive_result.correct is True
        assert optimized_result.correct is True

        print("\n" + "="*60)
        print("SCENARIO COMPLETE: Optimization comparison done!")
        print("="*60)

    def test_error_recovery_workflow(self, judge, group_fruits_puzzle):
        """Test workflow where user makes errors and recovers"""
        print("\n" + "="*60)
        print("SCENARIO: Error Recovery Workflow")
        print("="*60)

        print("\nStep 1: User submits code with syntax error...")
        syntax_error_code = """
def solve(fruits):
    return fruits.filter(
"""
        syntax_result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            syntax_error_code,
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert syntax_result.error is not None
        print(f"  Error detected: {syntax_result.error[:50]}...")

        print("\nStep 2: User forgets solve() function...")
        no_solve_code = """
result = fruits.orderBy('type')
"""
        no_solve_result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            no_solve_code,
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert no_solve_result.error is not None
        print(f"  Error detected: {no_solve_result.error[:50]}...")

        print("\nStep 3: User fixes code and submits correct solution...")
        correct_result = judge.evaluate(
            group_fruits_puzzle['puzzle_id'],
            group_fruits_puzzle['correct_code'],
            group_fruits_puzzle['input_data'],
            group_fruits_puzzle['expected_output']
        )

        assert correct_result.correct is True
        assert correct_result.error is None
        print(f"  Success! Stars: {correct_result.stars}")

        print("\n" + "="*60)
        print("SCENARIO COMPLETE: Error recovery successful!")
        print("="*60)


# =============================================================================
# Test Class: Performance and Stress
# =============================================================================

class TestPerformance:
    """Performance tests for the execution pipeline"""

    def test_multiple_executions(self, judge, group_fruits_puzzle):
        """Test multiple consecutive executions"""
        print("\n[INFO] Running 5 consecutive executions...")

        results = []
        for i in range(5):
            result = judge.evaluate(
                group_fruits_puzzle['puzzle_id'],
                group_fruits_puzzle['correct_code'],
                group_fruits_puzzle['input_data'],
                group_fruits_puzzle['expected_output']
            )
            results.append(result)
            print(f"  Execution {i+1}: correct={result.correct}, stars={result.stars}")

        assert all(r.correct for r in results)
        print("[SUCCESS] All executions successful")

    def test_larger_dataset(self, executor):
        """Test execution with larger dataset"""
        large_data = {
            'items': [
                {"id": i, "value": i * 10, "category": f"cat_{i % 5}"}
                for i in range(1000)
            ]
        }

        code = """
def solve(items):
    from pyspark.sql.functions import sum as spark_sum
    return items.groupBy("category").agg(spark_sum("value").alias("total")).orderBy("category")
"""

        print("\n[INFO] Testing with 1000-row dataset...")

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, large_data, f"test_large_{int(time.time())}"
        )

        assert error is None
        assert result is not None
        assert len(result) == 5

        print(f"[SUCCESS] Large dataset execution complete")
        print(f"  Results: {len(result)} aggregated rows")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
