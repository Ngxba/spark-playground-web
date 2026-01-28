from pyspark.sql import SparkSession, DataFrame as SparkDataFrame
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
from app.models.puzzle import SparkConfig
from app.config import settings
import json
from urllib.request import urlopen
from app.models.execution import ExecutorInfo

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

    def _create_spark_session(self, spark_config: Optional[SparkConfig]) -> SparkSession:
        """Create a new SparkSession for this execution"""
        app_name = f"SparkPlayground-{int(time.time())}"

        # Resolve config: use spark_config overrides if provided, else settings defaults
        shuffle_partitions = str(
            spark_config.shuffle_partitions
            if spark_config and spark_config.shuffle_partitions is not None
            else settings.spark_shuffle_partitions
        )
        executor_cores = str(
            spark_config.executor_cores
            if spark_config and spark_config.executor_cores is not None
            else settings.spark_executor_cores
        )
        executor_memory = (
            spark_config.executor_memory
            if spark_config and spark_config.executor_memory is not None
            else settings.spark_executor_memory
        )

        # Get configuration from settings
        event_log_dir = settings.spark_event_log_dir
        use_s3 = event_log_dir.startswith("s3a://") if event_log_dir else False

        # Build SparkSession with base configuration
        builder = (SparkSession.builder
                .master(settings.spark_master_url)
                .appName(app_name)
                .config("spark.sql.shuffle.partitions", shuffle_partitions)
                .config("spark.driver.memory", settings.spark_driver_memory)
                .config("spark.executor.memory", executor_memory)
                .config("spark.executor.cores", executor_cores)
                .config("spark.sql.adaptive.enabled", "false")
                # Disk space optimization configs
                # .config("spark.broadcast.compress", "true")  # Compress broadcast variables
                # .config("spark.shuffle.compress", "true")    # Compress shuffle data
                # .config("spark.shuffle.spill.compress", "true")  # Compress spilled data
                # .config("spark.io.compression.codec", "lz4")  # Fast compression codec
                # .config("spark.memory.fraction", "0.8")  # 80% memory for execution/storage
                # .config("spark.memory.storageFraction", "0.3")  # 30% of that for storage
                # .config("spark.cleaner.referenceTracking.cleanCheckpoints", "true")  # Clean checkpoints
                # .config("spark.shuffle.service.enabled", "false")  # Disable external shuffle (not needed for standalone)
        )

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

        # Explicitly set SQL runtime configs AFTER getOrCreate() to guarantee
        # they take effect even if a session was reused (builder.config() alone
        # does not reliably apply SQL configs on an existing session).
        spark.conf.set("spark.sql.shuffle.partitions", shuffle_partitions)
        spark.conf.set("spark.sql.adaptive.enabled", "false")

        return spark

    def _calculate_memory_overhead(self, memory_mb: int, overhead_factor: float = 0.1, min_overhead_mb: int = 384) -> int:
        """
        Calculate memory overhead following Spark's default formula.

        Spark's default: max(384MB, 10% of executor/driver memory)

        Args:
            memory_mb: Base memory in MB
            overhead_factor: Percentage of memory for overhead (default 0.1 = 10%)
            min_overhead_mb: Minimum overhead in MB (default 384MB)

        Returns:
            Memory overhead in MB
        """
        calculated_overhead = int(memory_mb * overhead_factor)
        return max(min_overhead_mb, calculated_overhead)

    def _get_standalone_cluster_capacity(self):
        url = settings.spark_master_ui_url.rstrip("/") + "/json/"
        data = json.load(urlopen(url))

        workers = data.get("workers", [])

        # NOTE: cannot use sum() here — pyspark.sql.functions.sum shadows the builtin.
        total_cores = 0
        total_mem_mb = 0
        for w in workers:
            total_cores += w.get("cores", 0)
            total_mem_mb += w.get("memory", 0)

        return {
            "total_workers": len(workers),
            "total_cores": total_cores,
            "total_memory_mb": total_mem_mb,
        }

    def _get_executors_info(self, spark: SparkSession) -> List[ExecutorInfo]:
        """
        Extract executor information from SparkContext.

        Dynamically queries the Spark cluster for actual executor information
        using statusTracker and getExecutorMemoryStatus.

        Note: Executors are dynamically created per job and terminated after,
        so this captures the state at the time of the call.

        Returns:
            List of executor information dictionaries
        """
        sc = spark.sparkContext
        conf = sc.getConf()
        executors = []
        master = conf.get("spark.master", "unknown")
        driver_memory = conf.get("spark.driver.memory", "unknown")
        executor_memory = conf.get("spark.executor.memory", "unknown")

        # Get memory overhead configs
        driver_memory_mb = self._parse_memory_string(driver_memory)
        executor_memory_mb = self._parse_memory_string(executor_memory)

        # Get or calculate driver memory overhead
        driver_overhead_str = conf.get("spark.driver.memoryOverhead", None)
        if driver_overhead_str:
            driver_overhead_mb = self._parse_memory_string(driver_overhead_str)
        else:
            driver_overhead_mb = self._calculate_memory_overhead(driver_memory_mb)

        # Get or calculate executor memory overhead
        executor_overhead_str = conf.get("spark.executor.memoryOverhead", None)
        if executor_overhead_str:
            executor_overhead_mb = self._parse_memory_string(executor_overhead_str)
        else:
            executor_overhead_mb = self._calculate_memory_overhead(executor_memory_mb)

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

            executors = [ExecutorInfo(
                id="driver",
                host=master,
                port=0,
                cores=num_cores,
                memory_mb=driver_memory_mb,
                memory_overhead_mb=driver_overhead_mb
            )]
            
        else:
            # Cluster mode - query actual executor info using statusTracker
            try:
                executor_infos = sc._jsc.sc().statusTracker().getExecutorInfos()

                # Driver host from config — used to identify the driver entry
                # among executor_infos (SparkExecutorInfo has no executorId field).
                driver_host = conf.get("spark.driver.host", "")

                # Get memory status per executor (includes driver)
                executor_memory_status = sc._jsc.sc().getExecutorMemoryStatus()

                def get_attr_safe(obj, attr):
                    """Safely get attribute, handling both method and property access (py4j)"""
                    val = getattr(obj, attr, None)
                    if val is not None:
                        if callable(val):
                            try:
                                return val()
                            except Exception:
                                return None
                        return val
                    # Java-style getter fallback: attr -> getAttr()
                    getter_name = 'get' + attr[0].upper() + attr[1:]
                    getter = getattr(obj, getter_name, None)
                    if getter is not None and callable(getter):
                        try:
                            return getter()
                        except Exception:
                            return None
                    return None

                # First pass: count workers (non-driver) to compute cores_per_executor
                worker_count = 0
                for executor_info in executor_infos:
                    host = get_attr_safe(executor_info, 'host') or "localhost"
                    if host != driver_host:
                        worker_count += 1

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
                    cores_per_executor = max(1, default_parallelism // max(1, worker_count)) if worker_count > 0 else 1

                # Second pass: build executor info list
                driver_found = False
                worker_idx = 0
                for executor_info in executor_infos:
                    host = get_attr_safe(executor_info, 'host') or "localhost"
                    port = get_attr_safe(executor_info, 'port') or 0

                    # Identify the driver by matching host with spark.driver.host.
                    # Only the first match counts (avoids false positives when
                    # driver and workers happen to share a host).
                    is_driver = (not driver_found and host == driver_host)
                    if is_driver:
                        driver_found = True
                        executor_id = "driver"
                    else:
                        executor_id = str(worker_idx)
                        worker_idx += 1

                    # Get memory info if available
                    memory_mb = 0
                    try:
                        mem_tuple = None
                        for key in [f"{host}:{port}", executor_id]:
                            try:
                                mem_tuple = executor_memory_status.apply(key)
                                break
                            except Exception:
                                continue

                        if mem_tuple is not None:
                            max_mem_bytes = mem_tuple._1() if hasattr(mem_tuple, '_1') else 0
                            memory_mb = int(max_mem_bytes / (1024 * 1024))
                    except Exception:
                        pass  # Memory info not available

                    executor_data = ExecutorInfo(
                        id=executor_id,
                        host=host,
                        port=port,
                        cores=cores_per_executor if not is_driver else 0,
                        memory_mb=memory_mb,
                        memory_overhead_mb=driver_overhead_mb if is_driver else executor_overhead_mb
                    )
                    executors.append(executor_data)

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
                    executors.append(ExecutorInfo(
                        id=str(i),
                        host="unknown",
                        port=0,
                        cores=executor_cores,
                        memory_mb=executor_memory_mb,
                        memory_overhead_mb=executor_overhead_mb
                    ))

        return executors

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

            cluster_capacity_info = self._get_standalone_cluster_capacity()
            # Extract configuration values from actual Spark config
            master = conf.get("spark.master", "")
            spark_mode = next(
                (
                    mode for mode, match in {
                        "local": master.startswith("local"),
                        "standalone": master.startswith("spark://"),
                        "yarn": master == "yarn",
                        "kubernetes": master.startswith("k8s://"),
                        "mesos": master.startswith("mesos://"),
                    }.items()
                    if match
                ),
                "unknown",
            )
            driver_memory = conf.get("spark.driver.memory", "unknown")
            executor_memory = conf.get("spark.executor.memory", "unknown")
            executor_cores = conf.get("spark.executor.cores", "unknown")
            shuffle_partitions = conf.get("spark.sql.shuffle.partitions", "unknown")

            # Get memory overhead with fallback to calculated value
            driver_memory_overhead_str = conf.get("spark.driver.memoryOverhead", None)
            if driver_memory_overhead_str:
                driver_memory_overhead = driver_memory_overhead_str
            else:
                driver_memory_mb = self._parse_memory_string(driver_memory)
                driver_memory_overhead = f"{self._calculate_memory_overhead(driver_memory_mb)}m"

            executor_memory_overhead_str = conf.get("spark.executor.memoryOverhead", None)
            if executor_memory_overhead_str:
                executor_memory_overhead = executor_memory_overhead_str
            else:
                executor_memory_mb = self._parse_memory_string(executor_memory)
                executor_memory_overhead = f"{self._calculate_memory_overhead(executor_memory_mb)}m"

            # Try to parse shuffle_partitions as int
            try:
                shuffle_partitions = int(shuffle_partitions)
            except (ValueError, TypeError):
                pass

            return {
                "mode": spark_mode,
                "driver_memory": driver_memory,
                "executor_memory": executor_memory,
                "executor_cores": executor_cores,
                "shuffle_partitions": shuffle_partitions,
                "default_parallelism": sc.defaultParallelism,
                "driver_memory_overhead": driver_memory_overhead,
                "executor_memory_overhead": executor_memory_overhead,
                "cluster_capacity": cluster_capacity_info,
            }
        except Exception as e:
            # Return error info without hardcoded fallbacks
            return {
                "mode": "unknown",
                "error": f"Failed to extract cluster config: {str(e)}",
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
                "1. Takes 'spark' as the first parameter (SparkSession)\n"
                "2. Takes raw data parameters (list[dict]) matching the puzzle inputs\n"
                "3. Creates DataFrames using spark.createDataFrame(data)\n"
                "4. Returns a DataFrame as the result\n\n"
                "Example:\n"
                "from pyspark.sql import SparkSession, DataFrame\n\n"
                "def solve(spark: SparkSession, fruits: list[dict]) -> DataFrame:\n"
                "    df = spark.createDataFrame(fruits)\n"
                "    result = df.filter(...)\n"
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

        # Expected: 'spark' + all input_data_keys
        expected_params = ['spark'] + sorted(input_data_keys)
        # Actual: first param should be 'spark', rest should be data keys (sorted)
        if len(param_names) == 0 or param_names[0] != 'spark':
            error = (
                f"First parameter must be 'spark'!\n\n"
                f"Expected signature: def solve(spark: SparkSession, {', '.join(sorted(input_data_keys))})\n"
                f"Got parameters: {param_names}\n\n"
                f"The 'spark' parameter gives you the SparkSession to create DataFrames."
            )
            return None, error

        # Check remaining parameters (after 'spark')
        actual_data_params = sorted(param_names[1:])
        expected_data_params = sorted(input_data_keys)

        if len(actual_data_params) != len(expected_data_params):
            error = (
                f"Parameter count mismatch!\n"
                f"Expected: spark + {expected_data_params}\n"
                f"Got: {param_names}"
            )
            return None, error

        # Validate parameter names match
        if actual_data_params != expected_data_params:
            error = (
                f"Parameter names don't match!\n"
                f"Expected: ['spark'] + {expected_data_params}\n"
                f"Got: {param_names}\n\n"
                f"Make sure your function parameters match the input data names."
            )
            return None, error

        return solve_func, None

    def _call_user_function(
        self,
        user_func: callable,
        spark: SparkSession,
        input_data: Dict[str, Any]
    ) -> SparkDataFrame:
        """
        Call user's solve() function with spark session and raw data.

        Args:
            user_func: The solve() function
            spark: SparkSession for creating DataFrames
            input_data: Dictionary mapping parameter names to raw data (list[dict])

        Returns:
            Result DataFrame from user function
        """
        # Build kwargs: spark + raw data for each input key
        sig = inspect.signature(user_func)
        kwargs = {'spark': spark}

        for param_name in sig.parameters.keys():
            if param_name == 'spark':
                continue  # Already added
            if param_name not in input_data:
                raise ValueError(f"Missing input data for parameter: {param_name}")
            kwargs[param_name] = input_data[param_name]

        # Call function with spark and raw data
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
        execution_id: str,
        spark_config:Optional[SparkConfig]=None
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
            spark = self._create_spark_session(spark_config=spark_config)
            sc = spark.sparkContext
            print("spark.driver.host =", sc.getConf().get("spark.driver.host"))
            print("spark.driver.bindAddress =", sc.getConf().get("spark.driver.bindAddress"))
            print("spark.driver.port =", sc.getConf().get("spark.driver.port"))
            print("spark.blockManager.port =", sc.getConf().get("spark.blockManager.port"))
            app_id = spark.sparkContext.applicationId
            print("Spark UI:", spark.sparkContext.uiWebUrl)

            # 2. Raw data will be passed directly to solve() function
            # Users create their own DataFrames with spark.createDataFrame(data)
            # This allows control over initial partitioning via .repartition()

            # 3. Setup execution environment
            # Only provide builtins - users must explicitly import what they need
            # This is more educational and teaches real PySpark patterns
            exec_globals = {
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

                # 7. Call solve() function with spark session and raw data
                result_df = self._call_user_function(user_func, spark, input_data)

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

            # 12. Collect with job group (THE critical step)
            result, job_group_id = self._collect_with_job_group(
                result_df, spark, execution_id
            )

            # 12.5. Get cluster config AFTER collect (executors fully registered)
            if metadata:
                metadata['cluster_config'] = self._get_cluster_config(spark)

            # 12.6. Get executor info for metadata
            if metadata:
                metadata['executors_info'] = self._get_executors_info(spark)

            # 13. Add job_group_id to metadata
            if metadata:
                metadata['job_group_id'] = job_group_id

            # 13.5 Fetch execution tree from active Spark UI BEFORE stopping
            # the session.  The active UI (port 4040) has all data instantly;
            # the History Server needs event-log flush and has a race condition.
            if metadata and job_group_id and app_id:
                active_ui_url = spark.sparkContext.uiWebUrl
                if active_ui_url:
                    try:
                        from app.services.spark_event_tracker import SparkEventTracker
                        tracker = SparkEventTracker(active_ui_url=active_ui_url)
                        execution_tree = tracker.build_execution_tree(
                            app_id, job_group_id, use_active_ui=True
                        )
                        if execution_tree:
                            metadata['execution_tree'] = execution_tree
                            print(f"Pre-fetched execution tree from active UI ({active_ui_url})")
                    except Exception as e:
                        print(f"Warning: Failed to pre-fetch execution tree: {e}")

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
