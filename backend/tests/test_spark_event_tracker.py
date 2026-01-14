import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.spark_event_tracker import SparkEventTracker


@pytest.fixture
def mock_jobs_response():
    """Mock response for /jobs endpoint"""
    return [
        {
            "jobId": 0,
            "name": "collect at executor_v2.py:123",
            "jobGroup": "puzzle_execution_test_001",
            "status": "SUCCEEDED",
            "numStages": 2,
            "numTasks": 8,
            "numActiveTasks": 0,
            "numCompletedTasks": 8,
            "numFailedTasks": 0,
            "submissionTime": 1640000000000,
            "completionTime": 1640000005000
        },
        {
            "jobId": 1,
            "name": "other job",
            "jobGroup": "other_group",
            "status": "SUCCEEDED",
            "numStages": 1,
            "numTasks": 4
        }
    ]


@pytest.fixture
def mock_job_detail_response():
    """Mock response for /jobs/{job_id} endpoint"""
    return {
        "jobId": 0,
        "name": "collect at executor_v2.py:123",
        "status": "SUCCEEDED",
        "stageIds": [0, 1]
    }


@pytest.fixture
def mock_stage_detail_response():
    """Mock response for /stages/{stage_id} endpoint"""
    return [
        {
            "stageId": 0,
            "attemptId": 0,
            "name": "Scan parquet",
            "status": "COMPLETE",
            "numTasks": 4,
            "numActiveTasks": 0,
            "numCompleteTasks": 4,
            "numFailedTasks": 0,
            "submissionTime": 1640000000000,
            "completionTime": 1640000002000,
            "executorRunTime": 1500,
            "inputBytes": 1024000,
            "outputBytes": 512000,
            "shuffleReadBytes": 0,
            "shuffleWriteBytes": 256000
        }
    ]


@pytest.fixture
def mock_tasks_response():
    """Mock response for /stages/{stage_id}/{attempt}/taskList endpoint"""
    return [
        {
            "taskId": 0,
            "index": 0,
            "attempt": 0,
            "partitionId": 0,
            "status": "SUCCESS",
            "taskLocality": "PROCESS_LOCAL",
            "executorId": "driver",
            "host": "localhost",
            "launchTime": 1640000000000,
            "finishTime": 1640000000500,
            "duration": 500,
            "taskMetrics": {
                "executorRunTime": 450,
                "executorCpuTime": 400,
                "resultSize": 1024,
                "jvmGcTime": 50,
                "memoryBytesSpilled": 0,
                "diskBytesSpilled": 0,
                "inputMetrics": {"bytesRead": 256000},
                "outputMetrics": {"bytesWritten": 128000},
                "shuffleReadMetrics": {},
                "shuffleWriteMetrics": {"bytesWritten": 64000}
            }
        },
        {
            "taskId": 1,
            "index": 1,
            "attempt": 0,
            "partitionId": 1,
            "status": "SUCCESS",
            "taskLocality": "PROCESS_LOCAL",
            "executorId": "driver",
            "host": "localhost",
            "launchTime": 1640000000000,
            "finishTime": 1640000000600,
            "duration": 600,
            "taskMetrics": {
                "executorRunTime": 550,
                "executorCpuTime": 500
            }
        }
    ]


class TestSparkEventTracker:
    """Unit tests for SparkEventTracker"""

    def test_initialization(self):
        """Test tracker can be initialized"""
        tracker = SparkEventTracker()
        assert tracker.history_server_url == "http://localhost:18080"
        assert tracker.active_ui_url == "http://localhost:4040"

    def test_custom_urls(self):
        """Test initialization with custom URLs"""
        tracker = SparkEventTracker(
            history_server_url="http://custom:8080",
            active_ui_url="http://custom:4040"
        )
        assert tracker.history_server_url == "http://custom:8080"
        assert tracker.active_ui_url == "http://custom:4040"

    @patch('requests.get')
    def test_get_jobs_by_group_success(self, mock_get, mock_jobs_response):
        """Test successful job fetching and filtering"""
        mock_get.return_value.json.return_value = mock_jobs_response
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        jobs = tracker.get_jobs_by_group("app-123", "puzzle_execution_test_001")

        # Assertions
        assert len(jobs) == 1
        assert jobs[0]["jobId"] == 0
        assert jobs[0]["jobGroup"] == "puzzle_execution_test_001"

    @patch('requests.get')
    def test_get_jobs_by_group_no_match(self, mock_get, mock_jobs_response):
        """Test job fetching with no matching job group"""
        mock_get.return_value.json.return_value = mock_jobs_response
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        jobs = tracker.get_jobs_by_group("app-123", "non_existent_group")

        # Assertions
        assert len(jobs) == 0

    @patch('requests.get')
    def test_get_jobs_request_error(self, mock_get):
        """Test handling of request errors"""
        mock_get.side_effect = Exception("Connection error")

        tracker = SparkEventTracker()
        jobs = tracker.get_jobs_by_group("app-123", "puzzle_execution_test_001")

        # Assertions
        assert jobs == []

    @patch('requests.get')
    def test_get_stages_for_job(self, mock_get, mock_job_detail_response, mock_stage_detail_response):
        """Test fetching stages for a job"""
        # First call returns job detail, subsequent calls return stage details
        mock_get.return_value.json.side_effect = [
            mock_job_detail_response,
            mock_stage_detail_response,
            mock_stage_detail_response
        ]
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        stages = tracker.get_stages_for_job("app-123", 0)

        # Assertions
        assert len(stages) == 2  # Job has 2 stages
        assert all(isinstance(stage, dict) for stage in stages)

    @patch('requests.get')
    def test_get_stage_detail(self, mock_get, mock_stage_detail_response):
        """Test fetching stage detail"""
        mock_get.return_value.json.return_value = mock_stage_detail_response
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        stage = tracker.get_stage_detail("app-123", 0)

        # Assertions
        assert stage is not None
        assert stage["stageId"] == 0
        assert stage["status"] == "COMPLETE"

    @patch('requests.get')
    def test_get_stage_detail_empty(self, mock_get):
        """Test fetching stage detail when no stages exist"""
        mock_get.return_value.json.return_value = []
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        stage = tracker.get_stage_detail("app-123", 999)

        # Assertions
        assert stage is None

    @patch('requests.get')
    def test_get_tasks_for_stage(self, mock_get, mock_tasks_response):
        """Test fetching tasks for a stage"""
        mock_get.return_value.json.return_value = mock_tasks_response
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        tasks = tracker.get_tasks_for_stage("app-123", 0, 0)

        # Assertions
        assert len(tasks) == 2
        assert tasks[0]["taskId"] == 0
        assert tasks[1]["taskId"] == 1

    @patch('requests.get')
    def test_process_tasks(self, mock_get, mock_tasks_response):
        """Test task processing extracts correct information"""
        tracker = SparkEventTracker()
        processed = tracker._process_tasks(mock_tasks_response)

        # Assertions
        assert len(processed) == 2
        assert processed[0]["task_id"] == 0
        assert processed[0]["partition_id"] == 0
        assert processed[0]["executor_id"] == "driver"
        assert processed[0]["duration"] == 500
        assert "metrics" in processed[0]

    @patch('requests.get')
    def test_build_execution_tree_success(
        self,
        mock_get,
        mock_jobs_response,
        mock_job_detail_response,
        mock_stage_detail_response,
        mock_tasks_response
    ):
        """Test building complete execution tree"""
        # Setup mock responses in order
        mock_get.return_value.json.side_effect = [
            mock_jobs_response,  # get_jobs_by_group
            mock_job_detail_response,  # get_stages_for_job
            mock_stage_detail_response,  # get_stage_detail (stage 0)
            mock_tasks_response,  # get_tasks_for_stage (stage 0)
            mock_stage_detail_response,  # get_stage_detail (stage 1)
            mock_tasks_response  # get_tasks_for_stage (stage 1)
        ]
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        tree = tracker.build_execution_tree("app-123", "puzzle_execution_test_001")

        # Assertions
        assert tree is not None
        assert tree["app_id"] == "app-123"
        assert tree["job_group_id"] == "puzzle_execution_test_001"
        assert len(tree["jobs"]) == 1
        assert tree["jobs"][0]["job_id"] == 0
        assert len(tree["jobs"][0]["stages"]) == 2

    @patch('requests.get')
    def test_build_execution_tree_no_jobs(self, mock_get):
        """Test execution tree when no jobs are found"""
        mock_get.return_value.json.return_value = []
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        tree = tracker.build_execution_tree("app-123", "non_existent_group")

        # Assertions
        assert tree is None

    @patch('requests.get')
    def test_build_execution_tree_retry_active_ui(
        self,
        mock_get,
        mock_jobs_response
    ):
        """Test fallback to active UI when History Server fails"""
        # First call (History Server) returns empty, second (active UI) returns jobs
        mock_get.return_value.json.side_effect = [
            [],  # History Server has no jobs
            mock_jobs_response,  # Active UI has jobs
            {"jobId": 0, "stageIds": []},  # Job detail
        ]
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        tree = tracker.build_execution_tree("app-123", "puzzle_execution_test_001")

        # Assertions
        assert tree is not None
        assert len(tree["jobs"]) == 1

    @patch('requests.get')
    @patch('time.sleep')
    def test_wait_for_events_success(self, mock_sleep, mock_get, mock_jobs_response):
        """Test waiting for events to be available"""
        mock_get.return_value.json.side_effect = [
            [],  # First attempt: no jobs
            mock_jobs_response,  # Second attempt: jobs found
            {"jobId": 0, "stageIds": []}  # Job detail
        ]
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        tree = tracker.wait_for_events("app-123", "puzzle_execution_test_001", max_wait_seconds=1.0)

        # Assertions
        assert tree is not None
        assert mock_sleep.called

    @patch('requests.get')
    @patch('time.sleep')
    def test_wait_for_events_timeout(self, mock_sleep, mock_get):
        """Test timeout when events never become available"""
        mock_get.return_value.json.return_value = []
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        tree = tracker.wait_for_events("app-123", "non_existent", max_wait_seconds=0.4, retry_interval=0.1)

        # Assertions
        assert tree is None
        assert mock_sleep.called

    @patch('requests.get')
    def test_use_active_ui_parameter(self, mock_get, mock_jobs_response):
        """Test using active UI instead of History Server"""
        mock_get.return_value.json.return_value = mock_jobs_response
        mock_get.return_value.raise_for_status = Mock()

        tracker = SparkEventTracker()
        jobs = tracker.get_jobs_by_group("app-123", "puzzle_execution_test_001", use_active_ui=True)

        # Assertions
        assert len(jobs) == 1
        # Verify it called the active UI URL
        called_url = mock_get.call_args[0][0]
        assert "localhost:4040" in called_url

    @patch('requests.get')
    def test_http_error_handling(self, mock_get):
        """Test handling of HTTP errors"""
        mock_get.return_value.raise_for_status.side_effect = Exception("HTTP 500")

        tracker = SparkEventTracker()
        jobs = tracker.get_jobs_by_group("app-123", "puzzle_execution_test_001")

        # Assertions
        assert jobs == []

    def test_url_normalization(self):
        """Test that URLs are properly normalized (trailing slashes removed)"""
        tracker = SparkEventTracker(
            history_server_url="http://localhost:18080/",
            active_ui_url="http://localhost:4040/"
        )
        assert tracker.history_server_url == "http://localhost:18080"
        assert tracker.active_ui_url == "http://localhost:4040"
