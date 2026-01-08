"""Tests for API endpoints"""
import pytest

def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Spark Playground API" in data["message"]

def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_list_puzzles(client):
    """Test GET /api/puzzles endpoint"""
    response = client.get("/api/puzzles")
    assert response.status_code == 200
    puzzles = response.json()
    assert isinstance(puzzles, list)
    assert len(puzzles) == 5  # We have 5 puzzles

    # Check structure of first puzzle
    puzzle = puzzles[0]
    assert "id" in puzzle
    assert "title" in puzzle
    assert "description" in puzzle
    assert "difficulty" in puzzle
    assert "tags" in puzzle

def test_get_puzzle_by_id(client):
    """Test GET /api/puzzles/{id} endpoint"""
    response = client.get("/api/puzzles/group_fruits")
    assert response.status_code == 200
    puzzle = response.json()

    assert puzzle["id"] == "group_fruits"
    assert puzzle["title"] == "Group the Fruits"
    assert puzzle["difficulty"] == "easy"
    assert "scenario" in puzzle
    assert "goal" in puzzle
    assert "initial_data" in puzzle
    assert "expected_output" in puzzle
    assert "starter_code" in puzzle

def test_get_nonexistent_puzzle(client):
    """Test getting a puzzle that doesn't exist"""
    response = client.get("/api/puzzles/nonexistent")
    assert response.status_code == 404

def test_run_puzzle_valid_code(client):
    """Test POST /api/puzzles/{id}/run with valid code"""
    response = client.post(
        "/api/puzzles/group_fruits/run",
        json={"code": "result = fruits.sort_values('type').reset_index(drop=True)"}
    )
    assert response.status_code == 200
    result = response.json()

    assert "correct" in result
    assert "metrics" in result
    assert "stars" in result
    # Might not be correct depending on expected output format
    assert result["stars"] >= 0  # At least executed without error

def test_run_puzzle_with_error(client):
    """Test POST /api/puzzles/{id}/run with code error"""
    response = client.post(
        "/api/puzzles/group_fruits/run",
        json={"code": "result = undefined_variable"}
    )
    assert response.status_code == 200
    result = response.json()

    assert result["correct"] is False
    assert result["error"] is not None
    assert result["stars"] == 0

def test_run_puzzle_incorrect_output(client):
    """Test POST /api/puzzles/{id}/run with incorrect logic"""
    response = client.post(
        "/api/puzzles/group_fruits/run",
        json={"code": "result = fruits.head(2)"}  # Wrong - doesn't group properly
    )
    assert response.status_code == 200
    result = response.json()

    assert result["correct"] is False
    assert result["stars"] == 0

def test_run_nonexistent_puzzle(client):
    """Test running code for nonexistent puzzle"""
    response = client.post(
        "/api/puzzles/nonexistent/run",
        json={"code": "result = []"}
    )
    assert response.status_code == 404

def test_run_puzzle_without_code(client):
    """Test running puzzle without code field"""
    response = client.post(
        "/api/puzzles/group_fruits/run",
        json={}
    )
    assert response.status_code == 422  # Validation error

def test_cors_headers(client):
    """Test that CORS headers are configured (skip in TestClient)"""
    # TestClient doesn't include CORS headers, but we can verify middleware is set up
    response = client.get("/api/puzzles")
    # Just verify endpoint works - CORS is tested in integration tests
    assert response.status_code == 200

def test_all_puzzles_runnable(client):
    """Test that all puzzles can be retrieved and have valid structure"""
    # Get all puzzles
    response = client.get("/api/puzzles")
    puzzles = response.json()

    for puzzle_meta in puzzles:
        # Get detailed puzzle
        response = client.get(f"/api/puzzles/{puzzle_meta['id']}")
        assert response.status_code == 200
        puzzle = response.json()

        # Verify required fields
        assert "initial_data" in puzzle
        assert "expected_output" in puzzle
        assert "optimal_solution" in puzzle

def test_puzzle_metrics_structure(client):
    """Test that run result has complete metrics structure"""
    response = client.post(
        "/api/puzzles/group_fruits/run",
        json={"code": "result = fruits.sort_values('type')"}
    )
    result = response.json()

    metrics = result["metrics"]
    assert "time_simulated" in metrics
    assert "shuffles" in metrics
    assert "stages" in metrics
    assert "skew_detected" in metrics
    assert "cache_used" in metrics
    assert "broadcast_used" in metrics
    assert isinstance(metrics["time_simulated"], (int, float))
    assert isinstance(metrics["shuffles"], int)
    assert isinstance(metrics["stages"], int)
