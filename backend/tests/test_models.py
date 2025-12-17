"""Tests for Pydantic models"""
import pytest
from app.models import Puzzle, PuzzleMetadata, RunRequest, RunResult, MetricsResult, Difficulty, ConceptTag

def test_difficulty_enum():
    """Test Difficulty enum values"""
    assert Difficulty.EASY.value == "easy"
    assert Difficulty.MEDIUM.value == "medium"
    assert Difficulty.HARD.value == "hard"

def test_concept_tag_enum():
    """Test ConceptTag enum values"""
    assert ConceptTag.SHUFFLE.value == "shuffle"
    assert ConceptTag.JOIN.value == "join"
    assert ConceptTag.CACHE.value == "cache"

def test_puzzle_metadata():
    """Test PuzzleMetadata model"""
    metadata = PuzzleMetadata(
        id="test_puzzle",
        title="Test Puzzle",
        description="A test puzzle",
        difficulty=Difficulty.EASY,
        tags=[ConceptTag.SHUFFLE, ConceptTag.GROUPBY]
    )
    assert metadata.id == "test_puzzle"
    assert metadata.title == "Test Puzzle"
    assert len(metadata.tags) == 2

def test_puzzle_model():
    """Test complete Puzzle model"""
    puzzle = Puzzle(
        id="test_puzzle",
        title="Test Puzzle",
        description="A test puzzle",
        difficulty=Difficulty.EASY,
        tags=[ConceptTag.SHUFFLE],
        scenario="Test scenario",
        goal="Test goal",
        initial_data={"data": [1, 2, 3]},
        expected_output=[1, 2, 3],
        starter_code="# Start here",
        optimal_solution="result = data",
        visualization_config={"input_conveyors": 1}
    )
    assert puzzle.scenario == "Test scenario"
    assert puzzle.goal == "Test goal"
    assert isinstance(puzzle.initial_data, dict)

def test_run_request():
    """Test RunRequest model"""
    request = RunRequest(code="result = data.sort()")
    assert request.code == "result = data.sort()"

def test_metrics_result():
    """Test MetricsResult model"""
    metrics = MetricsResult(
        time_simulated=2.5,
        shuffles=1,
        stages=2,
        skew_detected=False,
        cache_used=True,
        broadcast_used=False
    )
    assert metrics.time_simulated == 2.5
    assert metrics.shuffles == 1
    assert metrics.cache_used is True

def test_run_result():
    """Test RunResult model"""
    metrics = MetricsResult(
        time_simulated=1.0,
        shuffles=0,
        stages=1,
        skew_detected=False,
        cache_used=False,
        broadcast_used=False
    )
    result = RunResult(
        correct=True,
        output=[1, 2, 3],
        metrics=metrics,
        stars=3,
        hint=None,
        error=None
    )
    assert result.correct is True
    assert result.stars == 3
    assert result.error is None

def test_run_result_with_error():
    """Test RunResult with error"""
    metrics = MetricsResult(
        time_simulated=0.0,
        shuffles=0,
        stages=0,
        skew_detected=False,
        cache_used=False,
        broadcast_used=False
    )
    result = RunResult(
        correct=False,
        output=None,
        metrics=metrics,
        stars=0,
        error="Syntax error"
    )
    assert result.correct is False
    assert result.stars == 0
    assert result.error == "Syntax error"

def test_puzzle_expected_output_list():
    """Test that Puzzle accepts list as expected_output"""
    puzzle = Puzzle(
        id="test",
        title="Test",
        description="Test",
        difficulty=Difficulty.EASY,
        tags=[ConceptTag.SHUFFLE],
        scenario="Test",
        goal="Test",
        initial_data={"data": []},
        expected_output=[{"a": 1}, {"b": 2}],  # List
        optimal_solution="result = data"
    )
    assert isinstance(puzzle.expected_output, list)

def test_puzzle_expected_output_dict():
    """Test that Puzzle accepts dict as expected_output"""
    puzzle = Puzzle(
        id="test",
        title="Test",
        description="Test",
        difficulty=Difficulty.EASY,
        tags=[ConceptTag.CACHE],
        scenario="Test",
        goal="Test",
        initial_data={"data": []},
        expected_output={"counts": [], "items": []},  # Dict
        optimal_solution="result = data"
    )
    assert isinstance(puzzle.expected_output, dict)
