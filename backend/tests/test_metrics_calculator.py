"""Tests for MetricsCalculator service"""
import pytest
from app.services.metrics_calculator import MetricsCalculator

def test_metrics_no_operations():
    """Test metrics for code with no special operations"""
    analysis = {
        'operations': [],
        'has_shuffle': False,
        'has_join': False,
        'has_broadcast': False,
        'has_cache': False,
        'has_groupby': False,
        'has_filter': False,
        'filter_after_join': False,
        'has_reuse_without_cache': False,
        'has_aggregation': False,
    }
    metrics = MetricsCalculator.calculate(analysis)

    assert metrics.shuffles == 0
    assert metrics.stages == 1  # Base stage
    assert metrics.time_simulated == 1.0  # Base time

def test_metrics_with_groupby():
    """Test metrics for groupby operation"""
    analysis = {
        'operations': ['groupby'],
        'has_shuffle': True,
        'has_join': False,
        'has_broadcast': False,
        'has_cache': False,
        'has_groupby': True,
        'has_filter': False,
        'filter_after_join': False,
        'has_reuse_without_cache': False,
        'has_aggregation': False,
    }
    metrics = MetricsCalculator.calculate(analysis)

    assert metrics.shuffles == 1
    assert metrics.stages >= 2  # Base + shuffle
    assert metrics.time_simulated > 1.0

def test_metrics_with_join_no_broadcast():
    """Test metrics for join without broadcast"""
    analysis = {
        'operations': ['join'],
        'has_shuffle': True,
        'has_join': True,
        'has_broadcast': False,
        'has_cache': False,
        'has_groupby': False,
        'has_filter': False,
        'filter_after_join': False,
        'has_reuse_without_cache': False,
        'has_aggregation': False,
    }
    metrics = MetricsCalculator.calculate(analysis)

    assert metrics.shuffles == 1
    assert metrics.time_simulated >= 4.0  # Higher for shuffle join

def test_metrics_with_broadcast_join():
    """Test metrics for broadcast join"""
    analysis = {
        'operations': ['join'],
        'has_shuffle': False,  # Broadcast avoids shuffle
        'has_join': True,
        'has_broadcast': True,
        'has_cache': False,
        'has_groupby': False,
        'has_filter': False,
        'filter_after_join': False,
        'has_reuse_without_cache': False,
        'has_aggregation': False,
    }
    metrics = MetricsCalculator.calculate(analysis)

    assert metrics.shuffles == 0
    assert metrics.broadcast_used is True
    # Broadcast join should be faster than shuffle join
    assert metrics.time_simulated < 4.0

def test_metrics_with_cache():
    """Test metrics when caching is used"""
    analysis = {
        'operations': ['cache'],
        'has_shuffle': False,
        'has_join': False,
        'has_broadcast': False,
        'has_cache': True,
        'has_groupby': False,
        'has_filter': False,
        'filter_after_join': False,
        'has_reuse_without_cache': False,
        'has_aggregation': False,
    }
    metrics = MetricsCalculator.calculate(analysis)

    assert metrics.cache_used is True
    # Cache should reduce time by 30%
    # Base time is 1.0, with cache it's 0.7
    assert metrics.time_simulated < 1.0

def test_metrics_reuse_without_cache():
    """Test metrics penalty for reuse without cache"""
    analysis = {
        'operations': [],
        'has_shuffle': False,
        'has_join': False,
        'has_broadcast': False,
        'has_cache': False,
        'has_groupby': False,
        'has_filter': False,
        'filter_after_join': False,
        'has_reuse_without_cache': True,
        'has_aggregation': False,
    }
    metrics = MetricsCalculator.calculate(analysis)

    # Should have time penalty (1.8x)
    assert metrics.time_simulated > 1.0

def test_metrics_filter_after_join_penalty():
    """Test metrics penalty for inefficient filter placement"""
    analysis = {
        'operations': ['filter', 'join'],
        'has_shuffle': True,
        'has_join': True,
        'has_broadcast': False,
        'has_cache': False,
        'has_groupby': False,
        'has_filter': True,
        'filter_after_join': True,
        'has_reuse_without_cache': False,
        'has_aggregation': False,
    }
    metrics = MetricsCalculator.calculate(analysis)

    # Should have additional penalty for filter after join
    assert metrics.time_simulated > 4.0

def test_metrics_aggregation():
    """Test metrics for aggregation"""
    analysis = {
        'operations': ['aggregation', 'groupby'],
        'has_shuffle': True,
        'has_join': False,
        'has_broadcast': False,
        'has_cache': False,
        'has_groupby': True,
        'has_filter': False,
        'filter_after_join': False,
        'has_reuse_without_cache': False,
        'has_aggregation': True,
    }
    metrics = MetricsCalculator.calculate(analysis)

    # Aggregation adds extra stage
    assert metrics.stages >= 3

def test_metrics_complex_query():
    """Test metrics for complex query with multiple operations"""
    analysis = {
        'operations': ['filter', 'join', 'groupby', 'aggregation'],
        'has_shuffle': True,
        'has_join': True,
        'has_broadcast': False,
        'has_cache': False,
        'has_groupby': True,
        'has_filter': True,
        'filter_after_join': False,
        'has_reuse_without_cache': False,
        'has_aggregation': True,
    }
    metrics = MetricsCalculator.calculate(analysis)

    assert metrics.shuffles >= 2  # Join + groupby
    assert metrics.stages >= 4
    assert metrics.time_simulated > 5.0
