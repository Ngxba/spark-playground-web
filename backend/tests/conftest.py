import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def sample_code_valid():
    """Valid code for testing"""
    return "result = fruits.sort_values('type')"

@pytest.fixture
def sample_code_error():
    """Code with syntax error"""
    return "result = fruits.sort_values('type'"  # Missing closing paren

@pytest.fixture
def sample_input_data():
    """Sample input data for testing"""
    return {
        "fruits": [
            {"id": 1, "type": "apple", "color": "red"},
            {"id": 2, "type": "banana", "color": "yellow"},
            {"id": 3, "type": "apple", "color": "red"},
        ]
    }

@pytest.fixture
def sample_expected_output():
    """Sample expected output"""
    return [
        {"id": 1, "type": "apple", "color": "red"},
        {"id": 3, "type": "apple", "color": "red"},
        {"id": 2, "type": "banana", "color": "yellow"},
    ]
