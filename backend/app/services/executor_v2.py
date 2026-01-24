from pyspark.sql import SparkSession, DataFrame as SparkDataFrame
from pyspark.sql.functions import col, broadcast, sum, count, avg, when, lit
import inspect
from typing import Any, Dict, Tuple, Optional, List
import sys
from io import StringIO
from pathlib import Path
import traceback
import threading
import time
import re
import boto3
from botocore.client import Config
from urllib.parse import urlparse

from app.config import settings


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

    def _ensure_s3a_eventlog_prefix(self, event_log_dir: str, endpoint: str, access_key: str, secret_key: str) -> None:
        """
        Ensure the S3 bucket exists and that the event-log prefix exists by writing a tiny marker object.

        event_log_dir should be like: s3a://bucket/prefix/
        """
        u = urlparse(event_log_dir.replace("s3a://", "s3://", 1))
        bucket = u.netloc
        prefix = (u.path or "/").lstrip("/")
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        # Put marker under a meta sub-prefix so it doesn't look like an event log file
        marker_key = f"{prefix}_meta/.keep"

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
            # region_name=os.getenv("AWS_REGION", "us-east-1"),
        )

        # Create bucket if missing (idempotent-ish)
        try:
            s3.head_bucket(Bucket=bucket)
        except Exception:
            s3.create_bucket(Bucket=bucket)

        # Create marker object (idempotent)
        s3.put_object(Bucket=bucket, Key=marker_key, Body=b"")

    def _create_spark_session(self) -> SparkSession:
        """Create a new SparkSession for this execution"""
        app_name = f"SparkPlayground-{int(time.time())}"

        # Get configuration from settings
        event_log_dir = settings.spark_event_log_dir
        use_s3 = event_log_dir.startswith("s3a://") if event_log_dir else False

        # Build SparkSession with base configuration
        builder = (SparkSession.builder
                .master(settings.spark_master_url)
                .appName(app_name)
                .config("spark.sql.shuffle.partitions", str(settings.spark_shuffle_partitions))
                .config("spark.driver.memory", settings.spark_driver_memory)
                .config("spark.executor.memory", settings.spark_executor_memory)
                .config("spark.sql.adaptive.enabled", "true"))

        # Configure event logging only if explicitly set
        if event_log_dir:
            builder = builder.config("spark.eventLog.enabled", "true")
            builder = builder.config("spark.eventLog.dir", event_log_dir)
            builder = builder.config("spark.eventLog.compress", "false")

            # Add S3 (MinIO) configuration only if using S3
            if use_s3 and settings.minio_endpoint:
                event_log_dir = event_log_dir.rstrip("/") + "/"
                self._ensure_s3a_eventlog_prefix(
                    event_log_dir,
                    settings.minio_endpoint,
                    settings.minio_access_key,
                    settings.minio_secret_key
                )

                builder = (builder
                    .config("spark.hadoop.fs.s3a.endpoint", settings.minio_endpoint)
                    .config("spark.hadoop.fs.s3a.access.key", settings.minio_access_key)
                    .config("spark.hadoop.fs.s3a.secret.key", settings.minio_secret_key)
                    .config("spark.hadoop.fs.s3a.path.style.access", "true")
                    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
                    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
                    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"))

        # Add JARs if available
        jar_dir = Path(settings.pyspark_jars_dir)
        jars = [str(p) for p in jar_dir.glob("*.jar")] if jar_dir.is_dir() else []
        if jars:
            builder = builder.config("spark.jars", ",".join(jars))

        spark = builder.getOrCreate()
        return spark

    def _get_cluster_config(self, spark: SparkSession) -> Dict[str, Any]:
        """
        Extract cluster configuration information from SparkSession.

        Dynamically queries the Spark cluster for actual executor information
        using statusTracker and getExecutorMemoryStatus.

        Note: Executors are dynamically created per job and terminated after,
        so this captures the state at the time of the call.

        Returns:
            Dictionary containing cluster configuration details
        """
        try:
            sc = spark.sparkContext
            conf = sc.getConf()

            # Extract configuration values from actual Spark config
            master = conf.get("spark.master", "unknown")
            driver_memory = conf.get("spark.driver.memory", "unknown")
            executor_memory = conf.get("spark.executor.memory", "unknown")
            shuffle_partitions = conf.get("spark.sql.shuffle.partitions", "unknown")

            # Try to parse shuffle_partitions as int
            try:
                shuffle_partitions = int(shuffle_partitions)
            except (ValueError, TypeError):
                pass

            # Get executor information from SparkContext
            executors = []
            total_executor_cores = 0
            total_executor_memory = 0

            if self._is_local_mode(master):
                # Local mode - driver acts as executor (single JVM)
                import multiprocessing
                if "[*]" in master:
                    num_cores = multiprocessing.cpu_count()
                elif "[" in master:
                    try:
                        num_cores = int(master.split("[")[1].split("]")[0])
                    except:
                        num_cores = 1
                else:
                    num_cores = 1

                executors = [{
                    "id": "driver",
                    "host": "localhost",
                    "cores": num_cores,
                    "memory_mb": self._parse_memory_string(driver_memory),
                }]
                total_executor_cores = num_cores
                total_executor_memory = self._parse_memory_string(driver_memory)
            else:
                # Cluster mode - query actual executor info using statusTracker
                try:
                    # Get executor IDs from statusTracker (excluding driver)
                    executor_infos = sc._jsc.sc().statusTracker().getExecutorInfos()
                    executor_ids = [e.executorId() for e in executor_infos]
                    executor_ids_without_driver = [eid for eid in executor_ids if eid != "driver"]

                    # Get memory status per executor (includes driver)
                    executor_memory_status = sc._jsc.sc().getExecutorMemoryStatus()

                    # Get cores per executor from config
                    cores_per_executor = conf.get("spark.executor.cores", None)
                    if cores_per_executor:
                        try:
                            cores_per_executor = int(cores_per_executor)
                        except:
                            cores_per_executor = None

                    # If not in config, estimate from defaultParallelism
                    if not cores_per_executor:
                        default_parallelism = sc.defaultParallelism
                        num_executors = len(executor_ids_without_driver)
                        cores_per_executor = max(1, default_parallelism // max(1, num_executors)) if num_executors > 0 else 1

                    # Build executor info list
                    for executor_info in executor_infos:
                        executor_id = executor_info.executorId()
                        is_driver = executor_id == "driver"

                        # Get host and port from executor info
                        host = executor_info.host()
                        port = executor_info.port()

                        # Get memory info if available
                        memory_mb = 0
                        memory_used_mb = 0
                        if executor_memory_status.containsKey(f"{host}:{port}"):
                            mem_tuple = executor_memory_status.get(f"{host}:{port}")
                            max_mem_bytes = mem_tuple._1() if hasattr(mem_tuple, '_1') else 0
                            remaining_mem_bytes = mem_tuple._2() if hasattr(mem_tuple, '_2') else 0
                            memory_mb = int(max_mem_bytes / (1024 * 1024))
                            memory_used_mb = int((max_mem_bytes - remaining_mem_bytes) / (1024 * 1024))
                        elif executor_memory_status.containsKey(executor_id):
                            mem_tuple = executor_memory_status.get(executor_id)
                            max_mem_bytes = mem_tuple._1() if hasattr(mem_tuple, '_1') else 0
                            remaining_mem_bytes = mem_tuple._2() if hasattr(mem_tuple, '_2') else 0
                            memory_mb = int(max_mem_bytes / (1024 * 1024))
                            memory_used_mb = int((max_mem_bytes - remaining_mem_bytes) / (1024 * 1024))

                        executor_data = {
                            "id": executor_id,
                            "host": host,
                            "port": port,
                            "cores": cores_per_executor if not is_driver else 0,
                            "memory_mb": memory_mb,
                            "memory_used_mb": memory_used_mb,
                        }
                        executors.append(executor_data)

                        if not is_driver:
                            total_executor_cores += cores_per_executor
                            total_executor_memory += memory_mb

                except Exception as e:
                    # Fallback: use configuration values
                    print(f"Warning: Failed to get executor info from statusTracker: {e}")
                    executor_cores = conf.get("spark.executor.cores", "1")
                    num_executors = conf.get("spark.executor.instances", "1")

                    try:
                        executor_cores = int(executor_cores)
                        num_executors = int(num_executors)
                    except:
                        executor_cores = 1
                        num_executors = 1

                    for i in range(num_executors):
                        executors.append({
                            "id": f"executor_{i}",
                            "cores": executor_cores,
                            "memory_mb": self._parse_memory_string(executor_memory),
                            "memory_used_mb": 0,
                        })

                    total_executor_cores = executor_cores * num_executors
                    total_executor_memory = self._parse_memory_string(executor_memory) * num_executors

            return {
                "mode": master,
                "driver_memory": driver_memory,
                "executor_memory": executor_memory,
                "shuffle_partitions": shuffle_partitions,
                "default_parallelism": sc.defaultParallelism,
                "executors": executors,
                "cluster_summary": {
                    "total_executors": len([e for e in executors if e["id"] != "driver"]),
                    "total_cores": total_executor_cores,
                    "total_memory_mb": total_executor_memory,
                }
            }
        except Exception as e:
            # Return error info without hardcoded fallbacks
            return {
                "mode": "unknown",
                "error": f"Failed to extract cluster config: {str(e)}",
                "cluster_summary": {
                    "total_executors": 0,
                    "total_cores": 0,
                    "total_memory_mb": 0,
                }
            }

    def _is_local_mode(self, master: str) -> bool:
        """
        Check if Spark is running in local mode.

        Local mode formats:
        - local
        - local[N]
        - local[*]
        - local[N, F]  (N threads, F max failures)

        NOT local mode:
        - spark://localhost:7077 (standalone cluster on localhost)
        - spark://127.0.0.1:7077
        """
        return bool(re.match(r'^local(\[\d+\]|\[\*\]|\[\d+,\s*\d+\])?$', master.strip(), re.IGNORECASE))

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
        import time
        try:
            spark.stop()
            # Small delay to ensure event logs are flushed to disk
            time.sleep(0.5)
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
            sc = spark.sparkContext
            print("spark.driver.host =", sc.getConf().get("spark.driver.host"))
            print("spark.driver.bindAddress =", sc.getConf().get("spark.driver.bindAddress"))
            print("spark.driver.port =", sc.getConf().get("spark.driver.port"))
            print("spark.blockManager.port =", sc.getConf().get("spark.blockManager.port"))
            app_id = spark.sparkContext.applicationId
            print("Spark UI:", spark.sparkContext.uiWebUrl)

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
