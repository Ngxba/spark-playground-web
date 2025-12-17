from pyspark.sql import SparkSession, DataFrame as SparkDataFrame
from pyspark.sql.functions import col, broadcast, sum, count, avg
import pandas as pd
from typing import Any, Dict, Tuple, Optional
import sys
from io import StringIO
import traceback
import threading
import time


class TimeoutException(Exception):
    pass


class CodeExecutor:
    """Executes user code in a controlled environment using real PySpark"""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds

    def _create_spark_session(self) -> SparkSession:
        """Create a new SparkSession for this execution"""
        import os
        import time

        # Generate unique app name with timestamp
        app_name = f"SparkPlayground-{int(time.time())}"
        event_log_dir = os.getenv("SPARK_EVENT_LOG_DIR", "/tmp/spark-events")

        spark = (SparkSession.builder
                .master("local[*]")  # Use all available cores
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
        import os
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
            # In local[*] mode, Spark uses all available cores
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
                    "is_active": False  # Will be set to True during execution
                }]

                total_executor_cores = num_cores
                total_executor_memory = self._parse_memory_string(driver_memory)
            else:
                # For actual cluster mode (not used in this app currently)
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
                    "cores_in_use": 0  # Will be updated during execution
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
            # Log but don't fail on cleanup errors
            print(f"Warning: Error stopping SparkSession: {e}", file=sys.stderr)

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

    def execute(self, code: str, input_data: Dict[str, Any]) -> Tuple[Any, str, str, Optional[Dict[str, Any]]]:
        """
        Execute user code with input data using PySpark

        Args:
            code: User's PySpark code
            input_data: Dictionary of data to make available as Spark DataFrames

        Returns:
            Tuple of (result, stdout, error_message, execution_metadata)
            execution_metadata contains: logical_plan, physical_plan, spark_metrics, app_id
        """
        spark = None
        result = None
        error_msg = None
        execution_metadata = None
        app_id = None

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            # Create SparkSession
            spark = self._create_spark_session()

            # Capture application ID for History Server link
            app_id = spark.sparkContext.applicationId

            # Extract cluster configuration
            cluster_config = self._get_cluster_config(spark)

            # Prepare execution environment with PySpark functions
            exec_globals = {
                'spark': spark,
                'col': col,
                'broadcast': broadcast,
                'sum': sum,
                'count': count,
                'avg': avg,
                '__builtins__': __builtins__,
            }

            # Convert input data to Spark DataFrames
            for key, value in input_data.items():
                if isinstance(value, list):
                    # Convert list of dicts to Spark DataFrame
                    if value:  # Only if not empty
                        exec_globals[key] = spark.createDataFrame(value)
                elif isinstance(value, dict):
                    # Convert dict to Spark DataFrame
                    pandas_df = pd.DataFrame(value)
                    exec_globals[key] = spark.createDataFrame(pandas_df)
                else:
                    exec_globals[key] = value

            # Store reference to capture DataFrame operations
            exec_globals['__result_df__'] = None
            exec_globals['__output_captured__'] = []

            # Wrap show() to capture output and DataFrame
            original_show = SparkDataFrame.show
            def show_wrapper(self, n=20, truncate=True, vertical=False):
                exec_globals['__result_df__'] = self
                return original_show(self, n, truncate, vertical)
            SparkDataFrame.show = show_wrapper

            # Wrap collect() to capture DataFrame
            original_collect = SparkDataFrame.collect
            def collect_wrapper(self):
                exec_globals['__result_df__'] = self
                return original_collect(self)
            SparkDataFrame.collect = collect_wrapper

            # Execute the code with timeout
            def execute_code():
                exec(code, exec_globals)

            self._execute_with_timeout(execute_code, self.timeout_seconds)

            # Restore original methods
            SparkDataFrame.show = original_show
            SparkDataFrame.collect = original_collect

            # Try to get the result DataFrame
            result_df = exec_globals.get('__result_df__')

            # If no explicit action was called, look for result variable
            if result_df is None:
                for var_name in ['result', 'output', 'df', 'final', 'answer']:
                    if var_name in exec_globals:
                        var = exec_globals[var_name]
                        if isinstance(var, SparkDataFrame):
                            result_df = var
                            break

            # If still no result, look for last DataFrame variable
            if result_df is None:
                user_vars = {k: v for k, v in exec_globals.items()
                           if not k.startswith('_') and k not in ['spark', 'col', 'broadcast', 'sum', 'count', 'avg', 'pd', 'np']
                           and k not in input_data.keys()}
                for var in reversed(list(user_vars.values())):
                    if isinstance(var, SparkDataFrame):
                        result_df = var
                        break

            # Convert result to records format
            if result_df is not None:
                try:
                    # Limit to 1000 rows for safety
                    result = result_df.limit(1000).toPandas().to_dict('records')

                    # Extract execution metadata
                    execution_metadata = self._extract_execution_metadata(result_df)
                    # Add application ID and cluster config to metadata
                    if execution_metadata:
                        if app_id:
                            execution_metadata['app_id'] = app_id
                        execution_metadata['cluster_config'] = cluster_config
                except Exception as e:
                    error_msg = f"Error collecting results: {str(e)}"
            else:
                error_msg = "No output detected. Did you call .show() or .collect()?"

        except TimeoutException as e:
            error_msg = str(e)
        except SyntaxError as e:
            error_msg = f"Syntax Error: {str(e)}"
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        finally:
            # Stop SparkSession
            if spark is not None:
                self._stop_spark_session(spark)

            # Restore stdout
            sys.stdout = old_stdout
            output_log = captured_output.getvalue()

        return result, output_log, error_msg, execution_metadata

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
