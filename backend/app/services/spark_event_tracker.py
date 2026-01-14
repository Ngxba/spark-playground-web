import requests
from typing import List, Dict, Any, Optional
import time


class SparkEventTracker:
    """
    Tracks Spark execution events via REST API.

    Fetches real job, stage, and task information from Spark History Server
    to provide accurate execution data for visualization.
    """

    def __init__(
        self,
        history_server_url: str = "http://localhost:18080",
        active_ui_url: str = "http://localhost:4040"
    ):
        self.history_server_url = history_server_url.rstrip('/')
        self.active_ui_url = active_ui_url.rstrip('/')

    def get_jobs_by_group(
        self,
        app_id: str,
        job_group_id: str,
        use_active_ui: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all jobs for a specific job group.

        Uses Spark REST API:
        GET /api/v1/applications/{app_id}/jobs

        Filters by jobGroup field.

        Args:
            app_id: Spark application ID
            job_group_id: Job group ID to filter by
            use_active_ui: If True, use active Spark UI instead of History Server

        Returns:
            List of job dictionaries matching the job group
        """
        base_url = self.active_ui_url if use_active_ui else self.history_server_url
        url = f"{base_url}/api/v1/applications/{app_id}/jobs"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            all_jobs = response.json()

            # Filter by job group
            group_jobs = [
                job for job in all_jobs
                if job.get('jobGroup') == job_group_id
            ]

            print(f"Found {len(group_jobs)} jobs for group '{job_group_id}' out of {len(all_jobs)} total jobs")
            return group_jobs

        except requests.exceptions.RequestException as e:
            print(f"Error fetching jobs from {url}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching jobs: {e}")
            return []

    def get_stages_for_job(
        self,
        app_id: str,
        job_id: int,
        use_active_ui: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all stages for a specific job.

        GET /api/v1/applications/{app_id}/jobs/{job_id}

        Args:
            app_id: Spark application ID
            job_id: Job ID
            use_active_ui: If True, use active Spark UI instead of History Server

        Returns:
            List of stage dictionaries with details
        """
        base_url = self.active_ui_url if use_active_ui else self.history_server_url
        url = f"{base_url}/api/v1/applications/{app_id}/jobs/{job_id}"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            job_detail = response.json()

            stage_ids = job_detail.get('stageIds', [])

            # Get details for each stage
            stages = []
            for stage_id in stage_ids:
                stage_detail = self.get_stage_detail(app_id, stage_id, use_active_ui=use_active_ui)
                if stage_detail:
                    stages.append(stage_detail)

            return stages

        except requests.exceptions.RequestException as e:
            print(f"Error fetching stages for job {job_id}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching stages: {e}")
            return []

    def get_stage_detail(
        self,
        app_id: str,
        stage_id: int,
        use_active_ui: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed stage information including task summary.

        GET /api/v1/applications/{app_id}/stages/{stage_id}

        Args:
            app_id: Spark application ID
            stage_id: Stage ID
            use_active_ui: If True, use active Spark UI instead of History Server

        Returns:
            Stage detail dictionary (latest attempt) or None
        """
        base_url = self.active_ui_url if use_active_ui else self.history_server_url
        url = f"{base_url}/api/v1/applications/{app_id}/stages/{stage_id}"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            stages = response.json()

            # API returns array of stage attempts, take the latest
            if stages and len(stages) > 0:
                return stages[-1]  # Latest attempt
            return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching stage {stage_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching stage detail: {e}")
            return None

    def get_tasks_for_stage(
        self,
        app_id: str,
        stage_id: int,
        stage_attempt_id: int = 0,
        use_active_ui: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks for a stage.

        GET /api/v1/applications/{app_id}/stages/{stage_id}/{stage_attempt_id}/taskList

        Args:
            app_id: Spark application ID
            stage_id: Stage ID
            stage_attempt_id: Stage attempt ID (default 0)
            use_active_ui: If True, use active Spark UI instead of History Server

        Returns:
            List of task dictionaries
        """
        base_url = self.active_ui_url if use_active_ui else self.history_server_url
        url = f"{base_url}/api/v1/applications/{app_id}/stages/{stage_id}/{stage_attempt_id}/taskList"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            tasks = response.json()
            return tasks

        except requests.exceptions.RequestException as e:
            print(f"Error fetching tasks for stage {stage_id}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching tasks: {e}")
            return []

    def build_execution_tree(
        self,
        app_id: str,
        job_group_id: str,
        retry_with_active_ui: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Build complete execution tree: Jobs → Stages → Tasks.

        This is the main method that constructs the full execution hierarchy
        with real Spark event data.

        Args:
            app_id: Spark application ID
            job_group_id: Job group ID to filter jobs
            retry_with_active_ui: If History Server fails, try active Spark UI

        Returns:
            Execution tree dictionary with jobs, stages, and tasks, or None if unavailable
        """
        # Try History Server first
        jobs = self.get_jobs_by_group(app_id, job_group_id, use_active_ui=False)

        # If History Server doesn't have the data yet, try active Spark UI
        if not jobs and retry_with_active_ui:
            print(f"No jobs found in History Server, trying active Spark UI...")
            jobs = self.get_jobs_by_group(app_id, job_group_id, use_active_ui=True)

        if not jobs:
            print(f"Warning: No jobs found for app {app_id} with job group '{job_group_id}'")
            return None

        # Determine which UI to use based on where we found jobs
        use_active = (retry_with_active_ui and len(jobs) > 0)

        execution_tree = {
            'app_id': app_id,
            'job_group_id': job_group_id,
            'jobs': []
        }

        for job in jobs:
            job_id = job['jobId']
            print(f"Processing job {job_id}...")

            # Get stages for this job
            stages = self.get_stages_for_job(app_id, job_id, use_active_ui=use_active)

            job_data = {
                'job_id': job_id,
                'name': job.get('name', f'Job {job_id}'),
                'status': job.get('status'),
                'num_stages': job.get('numStages', len(stages)),
                'num_tasks': job.get('numTasks', 0),
                'num_active_tasks': job.get('numActiveTasks', 0),
                'num_completed_tasks': job.get('numCompletedTasks', 0),
                'num_failed_tasks': job.get('numFailedTasks', 0),
                'submission_time': job.get('submissionTime'),
                'completion_time': job.get('completionTime'),
                'stages': []
            }

            for stage in stages:
                stage_id = stage['stageId']
                stage_attempt = stage.get('attemptId', 0)
                print(f"  Processing stage {stage_id} (attempt {stage_attempt})...")

                # Get tasks for this stage
                tasks = self.get_tasks_for_stage(
                    app_id, stage_id, stage_attempt, use_active_ui=use_active
                )

                stage_data = {
                    'stage_id': stage_id,
                    'attempt_id': stage_attempt,
                    'name': stage.get('name', f'Stage {stage_id}'),
                    'status': stage.get('status'),
                    'num_tasks': stage.get('numTasks', len(tasks)),
                    'num_active_tasks': stage.get('numActiveTasks', 0),
                    'num_complete_tasks': stage.get('numCompleteTasks', 0),
                    'num_failed_tasks': stage.get('numFailedTasks', 0),
                    'submission_time': stage.get('submissionTime'),
                    'completion_time': stage.get('completionTime'),
                    'executor_run_time': stage.get('executorRunTime', 0),
                    'input_bytes': stage.get('inputBytes', 0),
                    'output_bytes': stage.get('outputBytes', 0),
                    'shuffle_read_bytes': stage.get('shuffleReadBytes', 0),
                    'shuffle_write_bytes': stage.get('shuffleWriteBytes', 0),
                    'tasks': self._process_tasks(tasks)
                }

                job_data['stages'].append(stage_data)

            execution_tree['jobs'].append(job_data)

        print(f"Built execution tree with {len(execution_tree['jobs'])} jobs")
        return execution_tree

    def _process_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """
        Process task data for easier consumption.

        Extracts key task information and metrics.

        Args:
            tasks: Raw task data from Spark API

        Returns:
            List of processed task dictionaries
        """
        processed = []
        for task in tasks:
            task_metrics = task.get('taskMetrics', {})

            processed_task = {
                'task_id': task.get('taskId'),
                'index': task.get('index'),
                'attempt': task.get('attempt'),
                'partition_id': task.get('partitionId'),
                'status': task.get('status'),
                'task_locality': task.get('taskLocality'),
                'executor_id': task.get('executorId'),
                'host': task.get('host'),
                'launch_time': task.get('launchTime'),
                'finish_time': task.get('finishTime'),
                'duration': task.get('duration', 0),
                'metrics': {
                    'executor_run_time': task_metrics.get('executorRunTime', 0),
                    'executor_cpu_time': task_metrics.get('executorCpuTime', 0),
                    'result_size': task_metrics.get('resultSize', 0),
                    'jvm_gc_time': task_metrics.get('jvmGcTime', 0),
                    'memory_bytes_spilled': task_metrics.get('memoryBytesSpilled', 0),
                    'disk_bytes_spilled': task_metrics.get('diskBytesSpilled', 0),
                    'input_metrics': task_metrics.get('inputMetrics', {}),
                    'output_metrics': task_metrics.get('outputMetrics', {}),
                    'shuffle_read_metrics': task_metrics.get('shuffleReadMetrics', {}),
                    'shuffle_write_metrics': task_metrics.get('shuffleWriteMetrics', {})
                }
            }
            processed.append(processed_task)

        return processed

    def wait_for_events(
        self,
        app_id: str,
        job_group_id: str,
        max_wait_seconds: float = 1.0,
        retry_interval: float = 0.2
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for Spark events to be flushed and available.

        Polls the REST API until jobs are found or timeout is reached.

        Args:
            app_id: Spark application ID
            job_group_id: Job group ID
            max_wait_seconds: Maximum time to wait (default 1.0s)
            retry_interval: Time between retries (default 0.2s)

        Returns:
            Execution tree or None
        """
        start_time = time.time()
        attempt = 0

        while (time.time() - start_time) < max_wait_seconds:
            attempt += 1
            print(f"Attempt {attempt} to fetch execution data...")

            execution_tree = self.build_execution_tree(app_id, job_group_id)

            if execution_tree and execution_tree.get('jobs'):
                print(f"Successfully fetched execution data on attempt {attempt}")
                return execution_tree

            # Wait before retrying
            time.sleep(retry_interval)

        print(f"Timeout waiting for execution data after {max_wait_seconds}s")
        return None
