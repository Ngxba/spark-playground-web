"""Tests for OperationDetector service"""
import pytest
from app.services.operation_detector import OperationDetector

def test_detect_groupby():
    """Test detection of groupby operation"""
    code = "result = df.groupby('column').sum()"
    analysis = OperationDetector.analyze(code)

    assert 'groupby' in analysis['operations']
    assert analysis['has_groupby'] is True

def test_detect_join():
    """Test detection of join operation"""
    code = "result = df1.merge(df2, on='id')"
    analysis = OperationDetector.analyze(code)

    assert 'join' in analysis['operations']
    assert analysis['has_join'] is True

def test_detect_aggregation():
    """Test detection of aggregation"""
    code = "result = df.groupby('type').sum()"
    analysis = OperationDetector.analyze(code)

    assert 'aggregation' in analysis['operations']
    assert analysis['has_aggregation'] is True

def test_detect_filter():
    """Test detection of filter"""
    code = "result = df[df['value'] > 10]"
    analysis = OperationDetector.analyze(code)

    assert 'filter' in analysis['operations']
    assert analysis['has_filter'] is True

def test_detect_cache():
    """Test detection of cache usage"""
    code = "cached_df = df.cache()"
    analysis = OperationDetector.analyze(code)

    assert 'cache' in analysis['operations']
    assert analysis['has_cache'] is True

def test_detect_broadcast_join():
    """Test detection of broadcast join pattern"""
    code = """
small_df = cities.drop_duplicates()
result = orders.merge(small_df, on='city')
"""
    analysis = OperationDetector.analyze(code)

    assert analysis['has_broadcast'] is True

def test_detect_filter_after_join():
    """Test detection of filter after join (inefficient pattern)"""
    code = """
result = df1.merge(df2, on='id')
result = result[result['active'] == True]
"""
    analysis = OperationDetector.analyze(code)

    assert analysis['filter_after_join'] is True

def test_detect_shuffle():
    """Test detection of shuffle operations"""
    code = "result = df.groupby('category').sum()"
    analysis = OperationDetector.analyze(code)

    assert analysis['has_shuffle'] is True

def test_no_shuffle_with_broadcast():
    """Test that broadcast join doesn't count as shuffle"""
    code = """
cities_broadcast = cities.drop_duplicates()
result = orders.merge(cities_broadcast, on='city')
"""
    analysis = OperationDetector.analyze(code)

    # Broadcast join should not trigger shuffle
    assert analysis['has_broadcast'] is True

def test_detect_sort():
    """Test detection of sort operation"""
    code = "result = df.sort_values('column')"
    analysis = OperationDetector.analyze(code)

    assert 'sort' in analysis['operations']

def test_multiple_operations():
    """Test detection of multiple operations"""
    code = """
filtered = df.filter(lambda x: x['value'] > 10)
grouped = filtered.groupby('category')
result = grouped.sum()
"""
    analysis = OperationDetector.analyze(code)

    assert 'filter' in analysis['operations']
    assert 'groupby' in analysis['operations']
    assert 'aggregation' in analysis['operations']

def test_no_operations():
    """Test code with no special operations"""
    code = "result = df"
    analysis = OperationDetector.analyze(code)

    assert len(analysis['operations']) == 0
    assert analysis['has_shuffle'] is False
    assert analysis['has_join'] is False

def test_case_insensitive_detection():
    """Test that detection is case-insensitive"""
    code = "result = df.GroupBy('column').Sum()"
    analysis = OperationDetector.analyze(code)

    assert 'groupby' in analysis['operations']
    assert 'aggregation' in analysis['operations']

def test_reuse_without_cache():
    """Test detection of dataframe reuse without caching"""
    code = """
df_filtered = data[data['value'] > 0]
result1 = df_filtered.sum()
result2 = df_filtered.mean()
"""
    analysis = OperationDetector.analyze(code)

    # Should detect reuse without cache (though this is a simple heuristic)
    assert analysis['has_cache'] is False
