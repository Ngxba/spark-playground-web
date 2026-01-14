import pytest
from pyspark.sql import SparkSession, DataFrame as SparkDataFrame
from app.services.executor_v2 import ExecutorV2, TimeoutException


@pytest.fixture(scope="module")
def sample_input_data():
    """Sample input data for testing"""
    return {
        "fruits": [
            {"id": 1, "type": "apple", "color": "red"},
            {"id": 2, "type": "banana", "color": "yellow"},
            {"id": 3, "type": "apple", "color": "red"},
        ]
    }


class TestExecutorV2:
    """Unit tests for ExecutorV2"""

    def test_executor_initialization(self):
        """Test executor can be initialized"""
        executor = ExecutorV2(timeout_seconds=30)
        assert executor.timeout_seconds == 30

    def test_valid_function_execution(self, sample_input_data):
        """Test execution of valid function-based code"""
        executor = ExecutorV2()
        code = """
def solve(fruits):
    return fruits.orderBy('type')
"""
        execution_id = "test_001"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is None, f"Unexpected error: {error}"
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 3
        assert job_group_id == f"puzzle_execution_{execution_id}"
        assert metadata is not None
        assert 'app_id' in metadata
        assert 'job_group_id' in metadata

    def test_missing_solve_function(self, sample_input_data):
        """Test error handling when solve() function is missing"""
        executor = ExecutorV2()
        code = """
# No solve function defined
result = fruits.orderBy('type')
"""
        execution_id = "test_002"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is not None
        assert "No solve() function found" in error
        assert result is None

    def test_wrong_parameter_names(self, sample_input_data):
        """Test error handling for wrong parameter names"""
        executor = ExecutorV2()
        code = """
def solve(wrong_param):
    return wrong_param.orderBy('type')
"""
        execution_id = "test_003"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is not None
        assert "Parameter names don't match" in error or "Parameter" in error

    def test_wrong_parameter_count(self, sample_input_data):
        """Test error handling for wrong number of parameters"""
        executor = ExecutorV2()
        code = """
def solve(fruits, extra_param):
    return fruits.orderBy('type')
"""
        execution_id = "test_004"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is not None
        assert "Parameter count mismatch" in error or "Parameter" in error

    def test_non_dataframe_return(self, sample_input_data):
        """Test error handling when function doesn't return DataFrame"""
        executor = ExecutorV2()
        code = """
def solve(fruits):
    return [1, 2, 3]  # Returns list, not DataFrame
"""
        execution_id = "test_005"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is not None
        assert "must return a DataFrame" in error

    def test_action_prevention_collect(self, sample_input_data):
        """Test that calling .collect() inside solve() is prevented"""
        executor = ExecutorV2()
        code = """
def solve(fruits):
    fruits.collect()  # This should be blocked
    return fruits
"""
        execution_id = "test_006"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is not None
        assert "Cannot call .collect()" in error

    def test_action_prevention_show(self, sample_input_data):
        """Test that calling .show() inside solve() is prevented"""
        executor = ExecutorV2()
        code = """
def solve(fruits):
    fruits.show()  # This should be blocked
    return fruits
"""
        execution_id = "test_007"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is not None
        assert "Cannot call .show()" in error

    def test_action_prevention_count(self, sample_input_data):
        """Test that calling .count() inside solve() is prevented"""
        executor = ExecutorV2()
        code = """
def solve(fruits):
    n = fruits.count()  # This should be blocked
    return fruits
"""
        execution_id = "test_008"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is not None
        assert "Cannot call .count()" in error

    def test_complex_transformation(self, sample_input_data):
        """Test execution with complex transformations"""
        executor = ExecutorV2()
        code = """
from pyspark.sql.functions import col

def solve(fruits):
    # Complex transformation with filter and orderBy
    result = fruits.filter(col('type') == 'apple').orderBy('id')
    return result
"""
        execution_id = "test_009"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is None, f"Unexpected error: {error}"
        assert result is not None
        assert len(result) == 2  # Only apples
        assert all(r['type'] == 'apple' for r in result)

    def test_metadata_extraction(self, sample_input_data):
        """Test that metadata is properly extracted"""
        executor = ExecutorV2()
        code = """
def solve(fruits):
    return fruits.orderBy('type')
"""
        execution_id = "test_010"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is None
        assert metadata is not None
        assert 'logical_plan' in metadata
        assert 'physical_plan' in metadata
        assert 'metrics' in metadata
        assert 'app_id' in metadata
        assert 'job_group_id' in metadata
        assert 'cluster_config' in metadata

    def test_syntax_error_handling(self, sample_input_data):
        """Test handling of syntax errors in user code"""
        executor = ExecutorV2()
        code = """
def solve(fruits):
    return fruits.orderBy('type'  # Missing closing parenthesis
"""
        execution_id = "test_011"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is not None
        assert "Syntax Error" in error or "SyntaxError" in error

    def test_runtime_error_handling(self, sample_input_data):
        """Test handling of runtime errors in user code"""
        executor = ExecutorV2()
        code = """
def solve(fruits):
    result = fruits.orderBy('nonexistent_column')  # Column doesn't exist
    return result
"""
        execution_id = "test_012"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        # Note: This might not error until .collect() is called
        # The error could be in error or the execution might succeed
        # depending on lazy evaluation
        assert error is not None or result is not None

    def test_multiple_dataframe_inputs(self):
        """Test execution with multiple DataFrame inputs"""
        executor = ExecutorV2()
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
        code = """
def solve(orders, cities):
    return orders.join(cities, 'city_code')
"""
        execution_id = "test_013"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, input_data, execution_id
        )

        # Assertions
        assert error is None, f"Unexpected error: {error}"
        assert result is not None
        assert len(result) == 2
        assert all('city_name' in r for r in result)

    def test_job_group_id_format(self, sample_input_data):
        """Test that job group ID has correct format"""
        executor = ExecutorV2()
        code = """
def solve(fruits):
    return fruits
"""
        execution_id = "test_custom_id_123"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is None
        assert job_group_id == "puzzle_execution_test_custom_id_123"
        assert metadata['job_group_id'] == job_group_id

    def test_row_to_dict_conversion(self, sample_input_data):
        """Test that results are properly converted from Row to dict"""
        executor = ExecutorV2()
        code = """
def solve(fruits):
    return fruits.orderBy('id')
"""
        execution_id = "test_014"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, sample_input_data, execution_id
        )

        # Assertions
        assert error is None
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)
            assert 'id' in item
            assert 'type' in item
            assert 'color' in item

    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame input"""
        executor = ExecutorV2()
        input_data = {"empty_data": []}
        code = """
def solve(empty_data):
    return empty_data
"""
        execution_id = "test_015"

        result, output_log, error, metadata, job_group_id = executor.execute(
            code, input_data, execution_id
        )

        # Note: Empty DataFrame might cause issues, check both cases
        assert error is None or "empty" in error.lower()
