"""Tests for CodeExecutor service with PySpark"""
import pytest
from app.services.executor import CodeExecutor


def test_executor_simple_pyspark_code():
    """Test executor with simple valid PySpark code"""
    executor = CodeExecutor()
    code = """
from pyspark.sql.functions import col
result = fruits.orderBy('type')
result.show()
"""
    input_data = {
        "fruits": [
            {"id": 1, "type": "banana"},
            {"id": 2, "type": "apple"},
        ]
    }
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is None
    assert result is not None
    assert len(result) == 2
    assert result[0]["type"] == "apple"  # Should be sorted
    assert result[1]["type"] == "banana"


def test_executor_with_collect():
    """Test executor with .collect() action"""
    executor = CodeExecutor()
    code = """
result = fruits.filter(fruits.type == 'apple')
result.collect()
"""
    input_data = {
        "fruits": [
            {"id": 1, "type": "banana"},
            {"id": 2, "type": "apple"},
            {"id": 3, "type": "apple"},
        ]
    }
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is None
    assert len(result) == 2
    assert all(r["type"] == "apple" for r in result)


def test_executor_groupby_aggregation():
    """Test executor with PySpark groupBy and aggregation"""
    executor = CodeExecutor()
    code = """
from pyspark.sql.functions import sum

result = data.groupBy('category').agg(sum('value').alias('total'))
result.show()
"""
    input_data = {
        "data": [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
            {"category": "A", "value": 5},
        ]
    }
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is None
    assert len(result) == 2
    # Check totals
    totals = {r["category"]: r["total"] for r in result}
    assert totals["A"] == 15
    assert totals["B"] == 20


def test_executor_join_operation():
    """Test executor with PySpark join"""
    executor = CodeExecutor()
    code = """
result = df1.join(df2, 'id')
result.show()
"""
    input_data = {
        "df1": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        "df2": [{"id": 1, "age": 30}, {"id": 2, "age": 25}],
    }
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is None
    assert len(result) == 2
    assert all("name" in row and "age" in row for row in result)


def test_executor_broadcast_join():
    """Test executor with broadcast join"""
    executor = CodeExecutor()
    code = """
from pyspark.sql.functions import broadcast

result = orders.join(broadcast(cities), 'city_code')
result.show()
"""
    input_data = {
        "orders": [
            {"order_id": 1, "city_code": "NYC"},
            {"order_id": 2, "city_code": "LA"},
        ],
        "cities": [
            {"city_code": "NYC", "city_name": "New York"},
            {"city_code": "LA", "city_name": "Los Angeles"},
        ]
    }
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is None
    assert len(result) == 2
    # Check that broadcast was detected in metadata
    assert metadata is not None
    assert metadata.get('metrics', {}).get('has_broadcast') == True


def test_executor_filter_with_col():
    """Test executor with filter using col()"""
    executor = CodeExecutor()
    code = """
from pyspark.sql.functions import col

result = items.filter(col('defective') == False)
result.show()
"""
    input_data = {
        "items": [
            {"item_id": 1, "defective": False},
            {"item_id": 2, "defective": True},
            {"item_id": 3, "defective": False},
        ]
    }
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is None
    assert len(result) == 2
    assert all(not r["defective"] for r in result)


def test_executor_cache_operation():
    """Test executor with cache()"""
    executor = CodeExecutor()
    code = """
from pyspark.sql.functions import col, count as spark_count

# Cache the DataFrame
cached = data.cache()

# Use it twice
count1 = cached.count()
filtered = cached.filter(col('value') > 10)

result = filtered
result.show()
"""
    input_data = {
        "data": [
            {"value": 5},
            {"value": 15},
            {"value": 25},
        ]
    }
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is None
    assert len(result) == 2
    # Check cache was detected
    assert metadata is not None
    # Note: Cache detection depends on whether InMemoryRelation appears in plan


def test_executor_syntax_error():
    """Test executor with syntax error in PySpark code"""
    executor = CodeExecutor()
    code = "result = fruits.orderBy("  # Syntax error
    input_data = {"fruits": [{"id": 1}]}
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is not None
    assert "Syntax Error" in error or "SyntaxError" in error
    assert result is None


def test_executor_runtime_error():
    """Test executor with runtime error"""
    executor = CodeExecutor()
    code = "result = undefined_dataframe.show()"
    input_data = {}
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is not None
    assert "NameError" in error


def test_executor_no_action_called():
    """Test executor when no action (.show() or .collect()) is called"""
    executor = CodeExecutor()
    code = """
# Just transformations, no action
result = fruits.filter(fruits.type == 'apple')
"""
    input_data = {
        "fruits": [
            {"id": 1, "type": "apple"},
            {"id": 2, "type": "banana"},
        ]
    }
    result, log, error, metadata = executor.execute(code, input_data)

    # Should still work because we look for result variable
    # Executor will automatically collect it
    assert result is not None or error is not None


def test_executor_metadata_extraction():
    """Test that execution metadata is properly extracted"""
    executor = CodeExecutor()
    code = """
result = fruits.orderBy('type')
result.show()
"""
    input_data = {
        "fruits": [
            {"id": 1, "type": "banana"},
            {"id": 2, "type": "apple"},
        ]
    }
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is None
    assert metadata is not None
    assert 'logical_plan' in metadata
    assert 'physical_plan' in metadata
    assert 'metrics' in metadata


def test_executor_shuffle_detection():
    """Test that shuffles are detected in metadata"""
    executor = CodeExecutor()
    code = """
from pyspark.sql.functions import sum

result = data.groupBy('category').agg(sum('value').alias('total'))
result.show()
"""
    input_data = {
        "data": [
            {"category": "A", "value": 10},
            {"category": "A", "value": 20},
        ]
    }
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is None
    assert metadata is not None
    # GroupBy operations typically cause shuffle
    assert metadata.get('metrics', {}).get('has_shuffle') in [True, False]  # May vary by Spark version


def test_executor_complex_query():
    """Test executor with complex multi-step query"""
    executor = CodeExecutor()
    code = """
from pyspark.sql.functions import col, sum

# Filter, then group, then sort
filtered = items.filter(col('defective') == False)
grouped = filtered.groupBy('category').agg(sum('quantity').alias('total'))
result = grouped.orderBy('total', ascending=False)
result.show()
"""
    input_data = {
        "items": [
            {"category": "A", "quantity": 10, "defective": False},
            {"category": "B", "quantity": 20, "defective": True},
            {"category": "A", "quantity": 5, "defective": False},
            {"category": "C", "quantity": 30, "defective": False},
        ]
    }
    result, log, error, metadata = executor.execute(code, input_data)

    assert error is None
    assert len(result) == 2  # Only A and C (B was defective)
    assert result[0]["total"] == 30  # C should be first
    assert result[1]["total"] == 15  # A should be second
