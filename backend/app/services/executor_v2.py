from pyspark.sql import SparkSession, DataFrame as SparkDataFrame
from pyspark.sql.functions import col, broadcast, sum, count, avg, when, lit
import inspect
from typing import Any, Dict, Tuple, Optional, List
import sys
from io import StringIO
import traceback
import threading
import time
import os


class TimeoutException(Exception):
    pass


class ExecutorV2:
    """
    V2 Executor with function-based submission and proper job tracking.

    Key improvements over V1:
    - Users submit def solve(...) -> DataFrame
    - Platform controls when .collect() is called
    - Uses setJobGroup for precise job tracking
    - Converts results with Row.asDict() (no pandas)
    - Prevents users from calling actions inside their function
    """

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds

    def _create_spark_session(self) -> SparkSession:
        """Create a new SparkSession for this execution"""
        # Generate unique app name with timestamp
        app_name = f"SparkPlayground-{int(time.time())}"
        event_log_dir = os.getenv("SPARK_EVENT_LOG_DIR", "/tmp/spark-events")

        # Ensure event log directory exists
        os.makedirs(event_log_dir, exist_ok=True)

        spark = (SparkSession.builder
                .master("local[2]")  # Use 2 cores for testing
                .appName(app_name)
                .config("spark.sql.shuffle.partitions", "4")  # Smaller for local testing
                .config("spark.driver.memory", "2g")
                .config("spark.executor.memory", "2g")
                .config("spark.sql.adaptive.enabled", "true")
                .config("spark.ui.enabled", "true")  # Enable Spark UI
                .config("spark.ui.port", "4040")  # Default Spark UI port
                .config("spark.eventLog.enabled", "true")  # Enable event logging
                .config("spark.eventLog.dir", f"file://{event_log_dir}")  # Event log directory
                .getOrCreate())
        return spark

    def _get_cluster_config(self, spark: SparkSession) -> Dict[str, Any]:
        """
        Extract cluster configuration information from SparkSession

        Returns:
            Dictionary containing cluster configuration details
        """
        import multiprocessing

        try:
            sc = spark.sparkContext
            conf = sc.getConf()

            # Get system info
            total_cores = multiprocessing.cpu_count()

            # Extract configuration values
            master = conf.get("spark.master", "local[*]")
            driver_memory = conf.get("spark.driver.memory", "2g")
            executor_memory = conf.get("spark.executor.memory", "2g")
            shuffle_partitions = int(conf.get("spark.sql.shuffle.partitions", "4"))

            # For local mode, we simulate executor structure
            if "local" in master:
                # Parse number of cores from master string
                if "[*]" in master:
                    num_cores = total_cores
                elif "[" in master:
                    try:
                        num_cores = int(master.split("[")[1].split("]")[0])
                    except:
                        num_cores = 1
                else:
                    num_cores = 1

                # Simulate as a single executor with multiple cores
                executors = [{
                    "id": "driver",
                    "host": "localhost",
                    "cores": num_cores,
                    "memory_mb": self._parse_memory_string(driver_memory),
                    "state": "RUNNING",
                    "is_active": False
                }]

                total_executor_cores = num_cores
                total_executor_memory = self._parse_memory_string(driver_memory)
            else:
                executors = []
                total_executor_cores = 0
                total_executor_memory = 0

            return {
                "mode": master,
                "driver_memory": driver_memory,
                "executor_memory": executor_memory,
                "shuffle_partitions": shuffle_partitions,
                "total_cores": total_cores,
                "executors": executors,
                "cluster_summary": {
                    "total_executors": len(executors),
                    "total_cores": total_executor_cores,
                    "total_memory_mb": total_executor_memory,
                    "cores_available": total_executor_cores,
                    "cores_in_use": 0
                }
            }
        except Exception as e:
            # Return minimal config on error
            return {
                "mode": "local[*]",
                "error": f"Failed to extract cluster config: {str(e)}",
                "cluster_summary": {
                    "total_executors": 1,
                    "total_cores": multiprocessing.cpu_count(),
                    "total_memory_mb": 2048,
                    "cores_available": multiprocessing.cpu_count(),
                    "cores_in_use": 0
                }
            }

    def _parse_memory_string(self, memory_str: str) -> int:
        """Convert memory string like '2g' or '512m' to MB"""
        try:
            memory_str = memory_str.lower().strip()
            if memory_str.endswith('g'):
                return int(float(memory_str[:-1]) * 1024)
            elif memory_str.endswith('m'):
                return int(memory_str[:-1])
            elif memory_str.endswith('k'):
                return int(float(memory_str[:-1]) / 1024)
            else:
                # Assume bytes
                return int(float(memory_str) / (1024 * 1024))
        except:
            return 2048  # Default 2GB

    def _stop_spark_session(self, spark: SparkSession):
        """Stop the SparkSession and clean up resources"""
        try:
            spark.stop()
        except Exception as e:
            print(f"Warning: Error stopping SparkSession: {e}", file=sys.stderr)

    def _setup_action_prevention(self) -> callable:
        """
        Monkey-patch DataFrame methods to prevent user actions.

        Blocks: .collect(), .show(), .count(), .take(), .toPandas(), .head(), .first()

        Returns:
            restore() function to undo patches
        """
        # Store original methods
        original_methods = {
            'collect': SparkDataFrame.collect,
            'show': SparkDataFrame.show,
            'count': SparkDataFrame.count,
            'take': SparkDataFrame.take,
            'head': SparkDataFrame.head,
            'first': SparkDataFrame.first,
        }

        # Also try to block toPandas if it exists
        if hasattr(SparkDataFrame, 'toPandas'):
            original_methods['toPandas'] = SparkDataFrame.toPandas

        def action_blocker(method_name):
            def wrapper(self, *args, **kwargs):
                raise RuntimeError(
                    f"Cannot call .{method_name}() inside solve() function!\n"
                    f"Your function should return a DataFrame without calling actions.\n"
                    f"The platform will handle data collection automatically."
                )
            return wrapper

        # Patch all action methods
        SparkDataFrame.collect = action_blocker('collect')
        SparkDataFrame.show = action_blocker('show')
        SparkDataFrame.count = action_blocker('count')
        SparkDataFrame.take = action_blocker('take')
        SparkDataFrame.head = action_blocker('head')
        SparkDataFrame.first = action_blocker('first')
        if hasattr(SparkDataFrame, 'toPandas'):
            SparkDataFrame.toPandas = action_blocker('toPandas')

        def restore():
            """Restore all original DataFrame methods"""
            SparkDataFrame.collect = original_methods['collect']
            SparkDataFrame.show = original_methods['show']
            SparkDataFrame.count = original_methods['count']
            SparkDataFrame.take = original_methods['take']
            SparkDataFrame.head = original_methods['head']
            SparkDataFrame.first = original_methods['first']
            if 'toPandas' in original_methods:
                SparkDataFrame.toPandas = original_methods['toPandas']

        return restore

    def _extract_and_validate_function(
        self,
        exec_globals: Dict,
        input_data_keys: List[str]
    ) -> Tuple[Optional[callable], Optional[str]]:
        """
        Extract solve() function and validate signature.

        Args:
            exec_globals: Namespace after executing user code
            input_data_keys: Expected parameter names from puzzle input data

        Returns:
            (function, error_message) - function is None if error
        """
        # Check if solve exists
        if 'solve' not in exec_globals:
            error = (
                "No solve() function found!\n\n"
                "Your code must define a function named 'solve' that:\n"
                "1. Takes DataFrame parameters matching the puzzle inputs\n"
                "2. Returns a DataFrame as the result\n\n"
                "Example:\n"
                "def solve(fruits):\n"
                "    result = fruits.filter(...)\n"
                "    return result"
            )
            return None, error

        solve_func = exec_globals['solve']

        # Check if it's actually a function
        if not callable(solve_func):
            error = "solve() must be a function, not " + type(solve_func).__name__
            return None, error

        # Get function signature
        try:
            sig = inspect.signature(solve_func)
            param_names = list(sig.parameters.keys())
        except Exception as e:
            error = f"Could not inspect solve() signature: {str(e)}"
            return None, error

        # Validate parameter count
        expected_params = sorted(input_data_keys)
        actual_params = sorted(param_names)

        if len(param_names) != len(input_data_keys):
            error = (
                f"Parameter count mismatch!\n"
                f"Expected {len(input_data_keys)} parameters: {expected_params}\n"
                f"Got {len(param_names)} parameters: {actual_params}"
            )
            return None, error

        # Validate parameter names match
        if actual_params != expected_params:
            error = (
                f"Parameter names don't match!\n"
                f"Expected: {expected_params}\n"
                f"Got: {actual_params}\n\n"
                f"Make sure your function parameters match the input data names."
            )
            return None, error

        return solve_func, None

    def _call_user_function(
        self,
        user_func: callable,
        spark_dfs: Dict[str, SparkDataFrame]
    ) -> SparkDataFrame:
        """
        Call user's solve() function with DataFrame arguments.

        Args:
            user_func: The solve() function
            spark_dfs: Dictionary mapping parameter names to DataFrames

        Returns:
            Result DataFrame from user function
        """
        # Build kwargs mapping parameter names to DataFrames
        sig = inspect.signature(user_func)
        kwargs = {}

        for param_name in sig.parameters.keys():
            if param_name not in spark_dfs:
                raise ValueError(f"Missing input data for parameter: {param_name}")
            kwargs[param_name] = spark_dfs[param_name]

        # Call function with DataFrames
        result = user_func(**kwargs)
        return result

    def _collect_with_job_group(
        self,
        df: SparkDataFrame,
        spark: SparkSession,
        execution_id: str
    ) -> Tuple[List[Dict], str]:
        """
        THE ONLY place where we call an action.

        Collects DataFrame results with job group tracking and converts to dict records.

        Args:
            df: DataFrame to collect
            spark: SparkSession
            execution_id: Unique execution identifier

        Returns:
            (result_records, job_group_id)
        """
        job_group_id = f"puzzle_execution_{execution_id}"

        # Set job group BEFORE calling action
        spark.sparkContext.setJobGroup(
            groupId=job_group_id,
            description=f"Puzzle evaluation {execution_id}",
            interruptOnCancel=True
        )

        try:
            # Collect and convert WITHOUT pandas
            MAX_ROWS = 10000
            limited_df = df.limit(MAX_ROWS)

            # This is the ONLY .collect() call - tagged with job group
            rows = limited_df.collect()

            # Convert Row objects to dicts manually (no pandas)
            result = [row.asDict() for row in rows]

        finally:
            # Clear job group
            spark.sparkContext.setJobGroup(None, None)

        return result, job_group_id

    def _extract_execution_metadata(self, df: SparkDataFrame) -> Dict[str, Any]:
        """
        Extract Spark execution metadata from a DataFrame

        Returns:
            Dictionary containing logical_plan, physical_plan, and metrics
        """
        try:
            # Get query execution object
            query_execution = df._jdf.queryExecution()

            # Extract logical plan
            logical_plan = query_execution.logical().toString()

            # Extract physical plan (optimized)
            physical_plan = query_execution.executedPlan().toString()

            # Analyze plans for key operations
            has_shuffle = "Exchange" in physical_plan
            has_broadcast = "BroadcastHashJoin" in physical_plan or "BroadcastExchange" in physical_plan
            has_sort = "Sort" in physical_plan
            has_filter = "Filter" in physical_plan or "filter" in logical_plan.lower()
            has_aggregation = "Aggregate" in physical_plan or "HashAggregate" in physical_plan

            # Count stages (approximate from exchanges and shuffles)
            num_exchanges = physical_plan.count("Exchange")
            estimated_stages = num_exchanges + 1 if num_exchanges > 0 else 1

            # Detect filter pushdown (filter appears before join in logical plan)
            filter_pushdown_applied = False
            if "Filter" in logical_plan and "Join" in logical_plan:
                filter_idx = logical_plan.index("Filter") if "Filter" in logical_plan else float('inf')
                join_idx = logical_plan.index("Join") if "Join" in logical_plan else float('inf')
                filter_pushdown_applied = filter_idx < join_idx

            return {
                "logical_plan": logical_plan,
                "physical_plan": physical_plan,
                "metrics": {
                    "has_shuffle": has_shuffle,
                    "has_broadcast": has_broadcast,
                    "has_sort": has_sort,
                    "has_filter": has_filter,
                    "has_aggregation": has_aggregation,
                    "estimated_stages": estimated_stages,
                    "filter_pushdown_applied": filter_pushdown_applied,
                    "num_exchanges": num_exchanges
                }
            }
        except Exception as e:
            return {
                "logical_plan": None,
                "physical_plan": None,
                "metrics": {},
                "error": f"Failed to extract metadata: {str(e)}"
            }

    def _execute_with_timeout(self, func, timeout):
        """Execute a function with a timeout using threading"""
        result = {'output': None, 'error': None, 'completed': False}

        def target():
            try:
                result['output'] = func()
                result['completed'] = True
            except Exception as e:
                result['error'] = e
                result['completed'] = True

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            # Thread is still running - timeout occurred
            raise TimeoutException(f"Code execution timed out after {timeout} seconds")

        if result['error']:
            raise result['error']

        return result['output']

    def execute(
        self,
        code: str,
        input_data: Dict[str, Any],
        execution_id: str
    ) -> Tuple[Any, str, str, Optional[Dict[str, Any]], str]:
        """
        Execute user's solve() function with tracking.

        Args:
            code: User's Python code containing def solve(...)
            input_data: Dictionary of input data (will be converted to DataFrames)
            execution_id: Unique execution identifier for job tracking

        Returns:
            (result, output_log, error, execution_metadata, job_group_id)
        """
        spark = None
        result = None
        error_msg = None
        metadata = None
        job_group_id = None

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            # 1. Create SparkSession
            spark = self._create_spark_session()
            app_id = spark.sparkContext.applicationId

            # 2. Convert input data to Spark DataFrames
            spark_dfs = {}
            for key, value in input_data.items():
                if isinstance(value, list):
                    # Convert list of dicts to Spark DataFrame
                    if value:  # Only if not empty
                        spark_dfs[key] = spark.createDataFrame(value)
                    else:
                        # Empty DataFrame with schema if possible
                        spark_dfs[key] = spark.createDataFrame([], schema="")
                else:
                    # Pass through other types (shouldn't happen in normal puzzles)
                    spark_dfs[key] = value

            # 3. Setup execution environment
            exec_globals = {
                'spark': spark,
                'col': col,
                'broadcast': broadcast,
                'sum': sum,
                'count': count,
                'avg': avg,
                'when': when,
                'lit': lit,
                '__builtins__': __builtins__,
            }

            # 4. Setup action prevention
            restore_actions = self._setup_action_prevention()

            result_df = None
            try:
                # 5. Execute user code to define solve() function
                def execute_code():
                    exec(code, exec_globals)

                self._execute_with_timeout(execute_code, self.timeout_seconds)

                # 6. Extract and validate solve() function
                user_func, validation_error = self._extract_and_validate_function(
                    exec_globals, list(input_data.keys())
                )
                if validation_error:
                    raise ValueError(validation_error)

                # 7. Call solve() function with DataFrames
                result_df = self._call_user_function(user_func, spark_dfs)

                # 8. Validate result is a DataFrame
                if not isinstance(result_df, SparkDataFrame):
                    raise TypeError(
                        f"solve() must return a DataFrame!\n"
                        f"You returned: {type(result_df).__name__}\n"
                        f"Make sure your function ends with: return result_df"
                    )

            finally:
                # 9. Restore DataFrame methods (ALWAYS restore, even on error)
                restore_actions()

            # 10. Extract metadata BEFORE collecting (analyze query plan)
            metadata = self._extract_execution_metadata(result_df)

            # 11. Add app_id to metadata
            if metadata:
                metadata['app_id'] = app_id
                metadata['cluster_config'] = self._get_cluster_config(spark)

            # 12. Collect with job group (THE critical step)
            result, job_group_id = self._collect_with_job_group(
                result_df, spark, execution_id
            )

            # 13. Add job_group_id to metadata
            if metadata:
                metadata['job_group_id'] = job_group_id

        except TimeoutException as e:
            error_msg = str(e)
        except SyntaxError as e:
            error_msg = f"Syntax Error: {str(e)}"
        except TypeError as e:
            error_msg = str(e)
        except ValueError as e:
            error_msg = str(e)
        except RuntimeError as e:
            # Likely from action prevention
            error_msg = str(e)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        finally:
            # 14. Stop SparkSession
            if spark is not None:
                self._stop_spark_session(spark)

            # 15. Restore stdout
            sys.stdout = old_stdout
            output_log = captured_output.getvalue()

        return result, output_log, error_msg, metadata, job_group_id
