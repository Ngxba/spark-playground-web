import pandas as pd
from typing import Dict, Any, Optional
from app.models import RunResult, MetricsResult
from app.services.executor import CodeExecutor
from app.services.operation_detector import OperationDetector
from app.services.metrics_calculator import MetricsCalculator
from app.services.hint_generator import HintGenerator
from app.services.execution_simulator import ExecutionSimulator

class Judge:
    """Main judge system that evaluates user code with real PySpark execution"""

    def __init__(self):
        self.executor = CodeExecutor()
        self.operation_detector = OperationDetector()
        self.metrics_calculator = MetricsCalculator()
        self.hint_generator = HintGenerator()
        self.execution_simulator = ExecutionSimulator()

    def evaluate(
        self,
        puzzle_id: str,
        code: str,
        input_data: Dict[str, Any],
        expected_output: Any
    ) -> RunResult:
        """
        Evaluate user code for a puzzle using real PySpark execution

        Args:
            puzzle_id: ID of the puzzle
            code: User's PySpark code
            input_data: Input data for the puzzle
            expected_output: Expected output

        Returns:
            RunResult with evaluation details including real Spark metrics
        """
        # Execute the code (now returns execution_metadata from Spark)
        result, output_log, error, execution_metadata = self.executor.execute(code, input_data)

        # If there was an execution error
        if error:
            return RunResult(
                correct=False,
                output=None,
                metrics=MetricsResult(
                    time_simulated=0.0,
                    shuffles=0,
                    stages=0,
                    skew_detected=False,
                    cache_used=False,
                    broadcast_used=False
                ),
                stars=0,
                error=error,
                execution_log=output_log
            )

        # Analyze the execution using REAL Spark metadata
        analysis = self.operation_detector.analyze_from_metadata(execution_metadata)

        # Calculate metrics from real Spark analysis
        metrics = self._create_metrics_from_analysis(analysis)

        # Check correctness
        is_correct = self._check_correctness(result, expected_output)

        # Calculate star rating based on real Spark metrics
        stars = self._calculate_stars(is_correct, analysis, metrics, puzzle_id)

        # Generate hint
        hint = self.hint_generator.generate_hint(puzzle_id, analysis, is_correct, stars)

        # Include DAG structure and query plans for frontend visualization
        dag_structure = None
        physical_plan = None
        logical_plan = None

        if execution_metadata and 'physical_plan' in execution_metadata:
            physical_plan = execution_metadata.get('physical_plan')
            logical_plan = execution_metadata.get('logical_plan')

            # Try to extract DAG from physical plan
            dag_structure = self.operation_detector.extract_dag_structure(physical_plan)

            # If extraction failed, create simple DAG from operations
            if not dag_structure or not dag_structure.get('nodes'):
                operations = analysis.get('operations', [])
                dag_structure = self.operation_detector.create_simple_dag_from_operations(operations)
                print(f"DAG extraction failed, using fallback with {len(operations)} operations")

            # Debug logging
            if dag_structure:
                print(f"Generated DAG: {len(dag_structure.get('nodes', []))} nodes, {len(dag_structure.get('edges', []))} edges")
            else:
                print("Warning: No DAG structure generated")

        # Build specific application URL if we have app_id
        spark_ui_url = "http://localhost:18080"
        if execution_metadata and 'app_id' in execution_metadata:
            app_id = execution_metadata['app_id']
            # Link directly to the specific application details page
            spark_ui_url = f"http://localhost:18080/history/{app_id}/jobs/"

        # Generate execution simulation for Factory View
        execution_simulation = None
        stage_flow = None
        if execution_metadata and physical_plan:
            execution_simulation = self.execution_simulator.generate_simulation(
                physical_plan=physical_plan,
                logical_plan=logical_plan,
                execution_metadata=execution_metadata
            )
            # Generate stage-by-stage flow for interactive visualization
            stage_flow = self.execution_simulator.generate_stage_flow(
                physical_plan=physical_plan,
                logical_plan=logical_plan,
                execution_metadata=execution_metadata
            )

        # Extract cluster configuration
        cluster_config = None
        if execution_metadata and 'cluster_config' in execution_metadata:
            cluster_config = execution_metadata['cluster_config']

        return RunResult(
            correct=is_correct,
            output=result,
            metrics=metrics,
            stars=stars,
            hint=hint,
            execution_log=output_log if output_log else None,
            dag_structure=dag_structure,  # DAG structure for Visual DAG tab
            physical_plan=physical_plan,  # Raw physical plan for Physical Plan tab
            logical_plan=logical_plan,    # Raw logical plan for Logical Plan tab
            spark_ui_url=spark_ui_url,  # Link to specific app in History Server
            execution_simulation=execution_simulation,  # Simulation data for Factory View
            stage_flow=stage_flow,  # Stage-by-stage flow for interactive visualization
            cluster_config=cluster_config  # Cluster configuration and resource information
        )

    def _create_metrics_from_analysis(self, analysis: Dict) -> MetricsResult:
        """
        Create MetricsResult from real Spark analysis

        Args:
            analysis: Analysis dict from OperationDetector.analyze_from_metadata()

        Returns:
            MetricsResult with real Spark metrics
        """
        return MetricsResult(
            time_simulated=0.0,  # We don't track actual time for now
            shuffles=analysis.get('num_shuffles', 0),
            stages=analysis.get('estimated_stages', 1),
            skew_detected=False,  # Could be enhanced with partition analysis
            cache_used=analysis.get('has_cache', False),
            broadcast_used=analysis.get('has_broadcast', False)
        )

    def _check_correctness(self, actual: Any, expected: Any) -> bool:
        """Check if actual output matches expected output"""
        try:
            if actual is None:
                return False

            # Handle dict outputs (like cache puzzle with multiple results)
            if isinstance(actual, dict) and isinstance(expected, dict):
                # Check if all keys match
                if set(actual.keys()) != set(expected.keys()):
                    return False

                # Check each key's value
                for key in actual.keys():
                    if not self._check_correctness(actual[key], expected[key]):
                        return False
                return True

            # Convert to DataFrames for comparison if they're lists of dicts
            if isinstance(actual, list) and isinstance(expected, list):
                if len(actual) == 0 and len(expected) == 0:
                    return True
                if len(actual) != len(expected):
                    return False

                # Convert to DataFrames and sort for comparison
                df_actual = pd.DataFrame(actual).sort_values(by=list(pd.DataFrame(actual).columns)).reset_index(drop=True)
                df_expected = pd.DataFrame(expected).sort_values(by=list(pd.DataFrame(expected).columns)).reset_index(drop=True)

                return df_actual.equals(df_expected)

            # Direct comparison for other types
            return actual == expected

        except Exception:
            return False

    def _calculate_stars(
        self,
        is_correct: bool,
        analysis: Dict,
        metrics: MetricsResult,
        puzzle_id: str
    ) -> int:
        """
        Calculate star rating (0-3) based on correctness and real Spark optimizations

        Uses real metrics from Spark query plans instead of heuristics
        """
        if not is_correct:
            return 0

        # Use performance score from operation detector if available
        if 'performance_score' in analysis:
            return analysis['performance_score']

        # Fallback to manual calculation
        optimal_criteria = self._get_optimal_criteria(puzzle_id)

        score = 3  # Start with perfect score

        # Penalty for excessive shuffles
        if metrics.shuffles > optimal_criteria.get('max_shuffles', 2):
            score -= 1

        # Penalty for not using broadcast when it should be used
        if optimal_criteria.get('should_broadcast', False) and not metrics.broadcast_used:
            score -= 1

        # Penalty for filter after join (detected from real plan)
        if analysis.get('filter_after_join', False):
            score -= 1

        # Penalty for not caching when reusing data
        if optimal_criteria.get('should_cache', False) and not metrics.cache_used:
            score -= 1

        # Ensure score is in valid range
        return max(1, min(3, score))

    def _get_optimal_criteria(self, puzzle_id: str) -> Dict:
        """Get optimal solution criteria for a puzzle"""
        criteria = {
            'group_fruits': {
                'max_shuffles': 1,
                'max_time': 5.0,
                'should_broadcast': False,
                'should_cache': False,
            },
            'fast_join': {
                'max_shuffles': 0,  # Broadcast join should have no shuffles
                'max_time': 3.0,
                'should_broadcast': True,
                'should_cache': False,
            },
            'total_output': {
                'max_shuffles': 1,  # GroupBy requires one shuffle
                'max_time': 4.0,
                'should_broadcast': False,
                'should_cache': False,
            },
            'filter_merge': {
                'max_shuffles': 1,
                'max_time': 4.0,
                'should_broadcast': False,
                'should_cache': False,
            },
            'cache_puzzle': {
                'max_shuffles': 2,  # GroupBy + filter, but with cache
                'max_time': 6.0,
                'should_broadcast': False,
                'should_cache': True,
            },
        }

        return criteria.get(puzzle_id, {
            'max_shuffles': 2,
            'max_time': 10.0,
            'should_broadcast': False,
            'should_cache': False,
        })
