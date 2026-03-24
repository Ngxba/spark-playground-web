import time
from typing import Dict, Any, Optional
from app.models import RunResult, MetricsResult
from app.services.executor_v2 import ExecutorV2
from app.services.spark_event_tracker import SparkEventTracker
from app.services.execution_simulator_v2 import ExecutionSimulatorV2
from app.services.operation_detector import OperationDetector
from app.services.hint_generator import HintGenerator
import pandas as pd
from app.models.puzzle import SparkConfig
from app.config import settings


class JudgeV2:
    """
    V2 Judge system with function-based submission and real Spark event tracking.

    Key improvements over V1:
    - Users submit def solve(...) -> DataFrame
    - Real execution data from Spark REST API
    - No toPandas() jobs (clean Spark logs)
    - Precise job group tracking
    - Accurate visualization data
    """

    def __init__(self):
        self.executor = ExecutorV2()
        self.event_tracker = SparkEventTracker()
        self.execution_simulator = ExecutionSimulatorV2(self.event_tracker)
        self.operation_detector = OperationDetector()
        self.hint_generator = HintGenerator()

    def evaluate(
        self,
        puzzle_id: str,
        code: str,
        input_data: Dict[str, Any],
        expected_output: Any,
        spark_config: Optional[SparkConfig] = None
    ) -> RunResult:
        """
        Evaluate user code for a puzzle using real Spark execution tracking.

        Args:
            puzzle_id: ID of the puzzle
            code: User's code containing def solve(...)
            input_data: Input data for the puzzle
            expected_output: Expected output

        Returns:
            RunResult with evaluation details including real Spark metrics
        """
        # Generate unique execution ID for tracking
        execution_id = f"{puzzle_id}_{int(time.time() * 1000)}"

        # Execute the code with V2 executor
        result, output_log, error, metadata, job_group_id = self.executor.execute(
            code, input_data, execution_id, spark_config=spark_config
        )

        # If there was an execution error
        if error:
            return self._create_error_result(error, output_log, code, expected_output)

        # Extract app_id for Spark UI link and event fetching
        app_id = metadata.get('app_id') if metadata else None

        # Build execution simulation from Spark events
        execution_simulation = None
        if app_id and job_group_id:
            # Prefer the pre-fetched tree from the active Spark UI (fetched
            # before spark.stop() in the executor — zero race condition).
            # Falls back to History Server polling if not available.
            pre_fetched_tree = metadata.get('execution_tree') if metadata else None
            if pre_fetched_tree:
                print(f"Using pre-fetched execution tree from active Spark UI")
            else:
                print(f"Fetching execution data from History Server for app {app_id}")

            execution_simulation = self.execution_simulator.generate_simulation_from_events(
                app_id, job_group_id, metadata,
                execution_tree=pre_fetched_tree
            )

            if execution_simulation:
                print(f"Successfully generated simulation with {len(execution_simulation.stages)} stages")
            else:
                print("Warning: Could not generate simulation from real events (will use fallback)")

        # Analyze the execution using Spark metadata
        analysis = self.operation_detector.analyze_from_metadata(metadata)

        # Calculate metrics from analysis
        metrics = self._create_metrics_from_analysis(analysis, execution_simulation)

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

        if metadata and 'physical_plan' in metadata:
            physical_plan = metadata.get('physical_plan')
            logical_plan = metadata.get('logical_plan')

            # Try to extract DAG from physical plan
            dag_structure = self.operation_detector.extract_dag_structure(physical_plan)

            # If extraction failed, create simple DAG from operations
            if not dag_structure or not dag_structure.get('nodes'):
                operations = analysis.get('operations', [])
                dag_structure = self.operation_detector.create_simple_dag_from_operations(operations)
                print(f"DAG extraction failed, using fallback with {len(operations)} operations")

        # Build Spark UI URL
        spark_ui_url = settings.spark_history_server_url
        if app_id:
            spark_ui_url = f"{settings.spark_history_server_url}/history/{app_id}/jobs/"

        # Generate stage flow for interactive visualization
        stage_flow = None
        if execution_simulation:
            stage_flow = self._generate_stage_flow_from_simulation(execution_simulation)

        # Generate Sankey spec for Timeline View
        sankey_spec = None
        if metadata and execution_simulation:
            from app.services.sankey_spec_generator import SankeySpecGenerator
            try:
                generator = SankeySpecGenerator()
                physical_plan = metadata.get('physical_plan', '')
                has_join = any(kw in (physical_plan or '') for kw in ['SortMergeJoin', 'BroadcastHashJoin', 'BroadcastNestedLoopJoin'])
                if not has_join:
                    print(f"Sankey: No join operators in physical plan — skipping (query has no joins)")
                else:
                    sankey_spec = generator.generate(metadata, execution_simulation)
                    if sankey_spec:
                        print(f"Generated Sankey spec with {len(sankey_spec.get('stages', []))} stages")
                    else:
                        print(f"Sankey: Generator returned None (could not map joins to stages)")
            except Exception as e:
                print(f"Warning: Sankey spec generation failed: {e}")
                import traceback
                traceback.print_exc()

        # Extract cluster configuration
        cluster_config = None
        if metadata and 'cluster_config' in metadata:
            cluster_config = metadata['cluster_config']

        return RunResult(
            correct=is_correct,
            output=result,
            expected_output=expected_output,
            user_code=code,
            metrics=metrics,
            stars=stars,
            hint=hint,
            execution_log=output_log if output_log else None,
            dag_structure=dag_structure,
            physical_plan=physical_plan,
            logical_plan=logical_plan,
            spark_ui_url=spark_ui_url,
            execution_simulation=execution_simulation,
            stage_flow=stage_flow,
            cluster_config=cluster_config,
            executors_info=metadata.get('executors_info'),
            sankey_spec=sankey_spec,
        )

    def _create_error_result(self, error: str, output_log: str, code: str, expected_output: Any = None) -> RunResult:
        """Create RunResult for execution errors."""
        return RunResult(
            correct=False,
            output=None,
            expected_output=expected_output,
            user_code=code,
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

    def _create_metrics_from_analysis(
        self,
        analysis: Dict,
        execution_simulation=None
    ) -> MetricsResult:
        """
        Create MetricsResult from real Spark analysis.

        Args:
            analysis: Analysis dict from OperationDetector.analyze_from_metadata()
            execution_simulation: Optional ExecutionSimulation with real metrics

        Returns:
            MetricsResult with real Spark metrics
        """
        # Use real data from execution_simulation if available
        if execution_simulation:
            num_shuffles = len(execution_simulation.shuffles)
            num_stages = len(execution_simulation.stages)
        else:
            num_shuffles = analysis.get('num_shuffles', 0)
            num_stages = analysis.get('estimated_stages', 1)

        return MetricsResult(
            time_simulated=0.0,  # We don't track actual time for now
            shuffles=num_shuffles,
            stages=num_stages,
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

                # Convert to DataFrames and ensure same column order
                df_actual = pd.DataFrame(actual)
                df_expected = pd.DataFrame(expected)

                # Use expected column order for both (standardize)
                if set(df_actual.columns) != set(df_expected.columns):
                    return False

                # Reorder actual columns to match expected
                df_actual = df_actual[df_expected.columns]

                # Sort both by all columns (now in same order)
                df_actual = df_actual.sort_values(
                    by=list(df_actual.columns)
                ).reset_index(drop=True)
                df_expected = df_expected.sort_values(
                    by=list(df_expected.columns)
                ).reset_index(drop=True)

                return df_actual.equals(df_expected)

            # Direct comparison for other types
            return actual == expected

        except Exception as e:
            print(f"Error checking correctness: {e}")
            return False

    def _calculate_stars(
        self,
        is_correct: bool,
        analysis: Dict,
        metrics: MetricsResult,
        puzzle_id: str
    ) -> int:
        """
        Calculate star rating (0-3) based on correctness and real Spark optimizations.

        Uses real metrics from Spark query plans instead of heuristics.
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

    def _generate_stage_flow_from_simulation(self, execution_simulation) -> Dict[str, Any]:
        """
        Generate stage-by-stage flow for interactive visualization.

        Args:
            execution_simulation: ExecutionSimulation with real data

        Returns:
            Stage flow dictionary with frontend-compatible structure
        """
        if not execution_simulation or not execution_simulation.stages:
            return None

        stages_flow = []
        shuffle_count = 0

        total_stages = len(execution_simulation.stages)
        for i, stage in enumerate(execution_simulation.stages):
            # Classify stage type
            stage_type = self._classify_stage_type(
                stage.name, stage.operation_type, i, total_stages
            )

            # Determine if this is a shuffle (use stage_type for consistency)
            is_shuffle = stage_type == 'shuffle'
            if is_shuffle:
                shuffle_count += 1

            # Get partition counts
            # For shuffle stages: input = current stage partitions, output = next stage partitions
            # For non-shuffle stages: input = output = current stage partitions
            current_partitions = stage.parallelism or len(stage.tasks) or 1
            next_partitions = current_partitions
            if i + 1 < len(execution_simulation.stages):
                next_stage = execution_simulation.stages[i + 1]
                next_partitions = next_stage.parallelism or len(next_stage.tasks) or current_partitions

            # For shuffle/exchange stages, show before→after partition change
            if is_shuffle or 'exchange' in (stage.name or '').lower():
                input_partitions = current_partitions
                output_partitions = next_partitions
            else:
                # Non-shuffle stages: just show current partitions
                input_partitions = current_partitions
                output_partitions = current_partitions

            # Check for repartition
            is_repartition = input_partitions != output_partitions and not is_shuffle

            # Generate a user-friendly stage name
            display_name = self._get_display_name(stage.name, stage.operation_type, stage_type)

            stage_info = {
                'id': stage.id,
                'name': display_name,
                'type': stage_type,
                'operation': stage.operation_type or display_name,
                'input': {'partitionCount': input_partitions or 1},
                'output': {'partitionCount': output_partitions or 1},
                'isShuffle': is_shuffle,
                'isRepartition': is_repartition,
                'explanation': self._generate_stage_explanation(display_name, stage_type),
                'performanceNote': self._generate_performance_note(stage_type, is_shuffle),
                # Keep original fields for compatibility
                'operation_type': stage.operation_type,
                'parallelism': stage.parallelism or 1,
                'num_tasks': len(stage.tasks) if stage.tasks else 0,
                'dependencies': stage.dependencies or [],
                'start_time': stage.start_time or 0,
                'end_time': stage.end_time or 0,
                'duration': (stage.end_time or 0) - (stage.start_time or 0)
            }
            stages_flow.append(stage_info)

        return {
            'stages': stages_flow,
            'shuffleCount': shuffle_count,
            'explanation': self._generate_pipeline_explanation(stages_flow, shuffle_count),
            'total_stages': len(stages_flow),
            'total_duration': execution_simulation.total_duration
        }

    def _classify_stage_type(self, name: str, operation_type: str, stage_index: int = 0, total_stages: int = 1) -> str:
        """
        Classify stage into semantic types for frontend visualization.

        Returns one of: 'scan', 'shuffle', 'aggregate', 'transform', 'output'
        """
        name_lower = (name or '').lower()
        op_lower = (operation_type or '').lower()
        combined = name_lower + ' ' + op_lower

        # Check for scan operations
        if any(kw in combined for kw in ['scan', 'inmemory', 'parquet', 'csv', 'json', 'orc']):
            return 'scan'

        # Check for shuffle/exchange operations
        if any(kw in combined for kw in ['exchange', 'shuffle', 'repartition', 'coalesce']):
            return 'shuffle'

        # Check for aggregation operations
        if any(kw in combined for kw in ['aggregate', 'hashaggregate', 'sortmerge', 'groupby', 'count', 'sum', 'avg']):
            return 'aggregate'

        # Check for output/collect operations
        if any(kw in combined for kw in ['collect', 'show', 'topandas', 'write', 'save']):
            return 'output'

        # Check for join operations (classify as transform)
        if any(kw in combined for kw in ['join', 'broadcasthashjoin', 'sortmergejoin', 'broadcastnestedloop']):
            return 'transform'

        # Check for filter/project operations
        if any(kw in combined for kw in ['filter', 'project', 'select', 'where']):
            return 'transform'

        # Check for sort operations
        if any(kw in combined for kw in ['sort', 'orderby']):
            return 'transform'

        # Heuristics based on position
        if stage_index == 0:
            return 'scan'  # First stage is usually data loading
        if stage_index == total_stages - 1:
            return 'output'  # Last stage is usually output

        return 'transform'

    def _get_display_name(self, name: str, operation_type: str, stage_type: str) -> str:
        """Generate a user-friendly display name for a stage."""
        # If we have a meaningful name from Spark, clean it up
        if name:
            # Clean up names like "collect at script.py:123" -> "Collect"
            name_lower = name.lower()

            # Map common Spark operation names to clean display names
            name_mappings = {
                'collect': 'Collect Results',
                'show': 'Show Results',
                'topandas': 'Convert to Pandas',
                'scan': 'Scan Data',
                'filter': 'Filter',
                'project': 'Project',
                'exchange': 'Exchange (Shuffle)',
                'hashaggregate': 'Hash Aggregate',
                'sortmerge': 'Sort Merge Join',
                'broadcasthashjoin': 'Broadcast Hash Join',
                'sort': 'Sort',
                'repartition': 'Repartition',
            }

            for keyword, display in name_mappings.items():
                if keyword in name_lower:
                    return display

        # Fallback to type-based names
        type_names = {
            'scan': 'Scan Data',
            'shuffle': 'Exchange (Shuffle)',
            'aggregate': 'Aggregate',
            'transform': 'Transform',
            'output': 'Collect Results'
        }

        return type_names.get(stage_type, operation_type or name or 'Processing')

    def _generate_stage_explanation(self, name: str, stage_type: str) -> str:
        """Generate educational explanation for a stage based on its type."""
        explanations = {
            'scan': "Reading data from source.\nThis step loads your input data into memory, dividing it into partitions for parallel processing.",
            'shuffle': "Redistributing data across partitions.\nThis is an expensive operation where data moves between executors over the network. Try to minimize shuffles!",
            'aggregate': "Aggregating data (groupBy, sum, count, etc.).\nThis combines rows based on keys. If data isn't already partitioned by the key, a shuffle may occur.",
            'transform': "Transforming data (filter, project, join, etc.).\nThis step processes data within each partition without moving data between executors.",
            'output': "Collecting results.\nThis gathers the final output from all partitions."
        }
        return explanations.get(stage_type, "Processing data...")

    def _generate_performance_note(self, stage_type: str, is_shuffle: bool) -> Optional[str]:
        """Generate performance tips for specific stage types."""
        if is_shuffle:
            return "Warning: Shuffle operations are expensive! Consider using broadcast joins for small tables or repartitioning data strategically."
        if stage_type == 'aggregate':
            return "Tip: Aggregations work best when data is already partitioned by the grouping key."
        return None

    def _generate_pipeline_explanation(self, stages: list, shuffle_count: int) -> str:
        """Generate overall pipeline explanation."""
        if shuffle_count == 0:
            return f"This query executes in {len(stages)} stages with no shuffles - very efficient!"
        elif shuffle_count == 1:
            return f"This query executes in {len(stages)} stages with 1 shuffle operation."
        else:
            return f"This query executes in {len(stages)} stages with {shuffle_count} shuffles - consider optimizations to reduce data movement."
