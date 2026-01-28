"""
Shared pytest fixtures for Spark Playground Backend tests.

Provides:
- FastAPI test client (lazy-loaded to avoid database initialization)
- Puzzle data fixtures for v2 integration tests
- Service fixtures (ExecutorV2, SparkEventTracker, etc.)
"""

import pytest
from typing import Dict, Any
import os

from app.config import settings


# =============================================================================
# Configuration Overrides for Local Testing
# =============================================================================

# Override settings for local testing (localhost instead of Docker service names)
# These are applied before any tests run
os.environ.setdefault("SPARK_MASTER_URL", "spark://localhost:7077")
os.environ.setdefault("SPARK_HISTORY_SERVER_URL", "http://localhost:18080")
os.environ.setdefault("SPARK_ACTIVE_UI_URL", "http://localhost:4040")
os.environ.setdefault("MINIO_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:password@localhost:5432/spark_playground")

# Reload settings with test overrides
settings.__init__()

EVENT_WAIT_TIMEOUT = 5.0


# =============================================================================
# FastAPI Client (lazy-loaded)
# =============================================================================

@pytest.fixture
def client():
    """FastAPI test client - lazy import to avoid database initialization"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


# =============================================================================
# Puzzle Data Fixtures
# =============================================================================

@pytest.fixture
def group_fruits_puzzle() -> Dict[str, Any]:
    """Group fruits puzzle - tests basic sorting/ordering"""
    return {
        'puzzle_id': 'group_fruits',
        'input_data': {
            'fruits': [
                {"id": 1, "type": "apple", "color": "red"},
                {"id": 2, "type": "banana", "color": "yellow"},
                {"id": 3, "type": "apple", "color": "green"},
                {"id": 4, "type": "orange", "color": "orange"},
            ]
        },
        'expected_output': [
            {"id": 1, "type": "apple", "color": "red"},
            {"id": 3, "type": "apple", "color": "green"},
            {"id": 2, "type": "banana", "color": "yellow"},
            {"id": 4, "type": "orange", "color": "orange"},
        ],
        'correct_code': """
from pyspark.sql import SparkSession, DataFrame

def solve(spark: SparkSession, fruits: list[dict]) -> DataFrame:
    df = spark.createDataFrame(fruits)
    return df.orderBy('type')
""",
        'incorrect_code': """
from pyspark.sql import SparkSession, DataFrame

def solve(spark: SparkSession, fruits: list[dict]) -> DataFrame:
    df = spark.createDataFrame(fruits)
    return df.orderBy('color')
""",
    }


@pytest.fixture
def fast_join_puzzle() -> Dict[str, Any]:
    """Fast join puzzle - tests broadcast join optimization"""
    return {
        'puzzle_id': 'fast_join',
        'input_data': {
            'orders': [
                {"order_id": 1, "product_id": 101, "quantity": 5},
                {"order_id": 2, "product_id": 102, "quantity": 3},
                {"order_id": 3, "product_id": 101, "quantity": 2},
            ],
            'products': [
                {"product_id": 101, "name": "Widget", "price": 10.0},
                {"product_id": 102, "name": "Gadget", "price": 25.0},
            ]
        },
        'expected_output': [
            {"order_id": 1, "product_id": 101, "quantity": 5, "name": "Widget", "price": 10.0},
            {"order_id": 2, "product_id": 102, "quantity": 3, "name": "Gadget", "price": 25.0},
            {"order_id": 3, "product_id": 101, "quantity": 2, "name": "Widget", "price": 10.0},
        ],
        'optimal_code': """
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import broadcast

def solve(spark: SparkSession, orders: list[dict], products: list[dict]) -> DataFrame:
    orders_df = spark.createDataFrame(orders)
    products_df = spark.createDataFrame(products)
    return orders_df.join(broadcast(products_df), "product_id")
""",
        'suboptimal_code': """
from pyspark.sql import SparkSession, DataFrame

def solve(spark: SparkSession, orders: list[dict], products: list[dict]) -> DataFrame:
    orders_df = spark.createDataFrame(orders)
    products_df = spark.createDataFrame(products)
    return orders_df.join(products_df, "product_id")
""",
    }


@pytest.fixture
def filter_merge_puzzle() -> Dict[str, Any]:
    """Filter merge puzzle - tests filter pushdown optimization"""
    return {
        'puzzle_id': 'filter_merge',
        'input_data': {
            'transactions': [
                {"tx_id": 1, "amount": 100, "status": "completed"},
                {"tx_id": 2, "amount": 200, "status": "pending"},
                {"tx_id": 3, "amount": 150, "status": "completed"},
                {"tx_id": 4, "amount": 50, "status": "failed"},
                {"tx_id": 5, "amount": 300, "status": "completed"},
            ]
        },
        'expected_output': [
            {"tx_id": 1, "amount": 100, "status": "completed"},
            {"tx_id": 3, "amount": 150, "status": "completed"},
            {"tx_id": 5, "amount": 300, "status": "completed"},
        ],
        'optimal_code': """
from pyspark.sql import SparkSession, DataFrame

def solve(spark: SparkSession, transactions: list[dict]) -> DataFrame:
    df = spark.createDataFrame(transactions)
    return df.filter(df.status == "completed")
""",
    }


@pytest.fixture
def aggregation_puzzle() -> Dict[str, Any]:
    """Aggregation puzzle - tests groupBy and aggregate operations"""
    return {
        'puzzle_id': 'total_output',
        'input_data': {
            'sales': [
                {"category": "Electronics", "amount": 100},
                {"category": "Clothing", "amount": 50},
                {"category": "Electronics", "amount": 200},
                {"category": "Food", "amount": 30},
                {"category": "Clothing", "amount": 75},
            ]
        },
        'expected_output': [
            {"category": "Clothing", "total": 125},
            {"category": "Electronics", "total": 300},
            {"category": "Food", "total": 30},
        ],
        'correct_code': """
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import sum as spark_sum

def solve(spark: SparkSession, sales: list[dict]) -> DataFrame:
    df = spark.createDataFrame(sales)
    return df.groupBy("category").agg(spark_sum("amount").alias("total")).orderBy("category")
""",
    }


@pytest.fixture
def cache_puzzle() -> Dict[str, Any]:
    """Cache puzzle - tests DataFrame caching"""
    return {
        'puzzle_id': 'cache_puzzle',
        'input_data': {
            'data': [
                {"id": 1, "value": 10, "category": "A"},
                {"id": 2, "value": 20, "category": "B"},
                {"id": 3, "value": 15, "category": "A"},
                {"id": 4, "value": 25, "category": "B"},
            ]
        },
        'expected_output': {
            'counts': [
                {"category": "A", "count": 2},
                {"category": "B", "count": 2},
            ],
            'sums': [
                {"category": "A", "total": 25},
                {"category": "B", "total": 45},
            ],
        },
        'optimal_code': """
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import count as spark_count, sum as spark_sum

def solve(spark: SparkSession, data: list[dict]) -> DataFrame:
    df = spark.createDataFrame(data)
    cached = df.cache()
    # Note: This puzzle returns dict, not compatible with V2 single DataFrame return
    counts = cached.groupBy("category").agg(spark_count("*").alias("count")).orderBy("category").collect()
    sums = cached.groupBy("category").agg(spark_sum("value").alias("total")).orderBy("category").collect()
    return {
        'counts': [row.asDict() for row in counts],
        'sums': [row.asDict() for row in sums]
    }
""",
    }


@pytest.fixture
def complex_etl_puzzle() -> Dict[str, Any]:
    """Complex ETL puzzle - tests multi-stage transformations"""
    return {
        'puzzle_id': 'complex_etl',
        'input_data': {
            'users': [
                {"user_id": 1, "name": "Alice", "age": 30},
                {"user_id": 2, "name": "Bob", "age": 25},
                {"user_id": 3, "name": "Charlie", "age": 35},
            ],
            'purchases': [
                {"user_id": 1, "item": "Book", "price": 15.0},
                {"user_id": 1, "item": "Pen", "price": 2.0},
                {"user_id": 2, "item": "Notebook", "price": 8.0},
                {"user_id": 3, "item": "Book", "price": 15.0},
                {"user_id": 3, "item": "Pencil", "price": 1.0},
            ]
        },
        'expected_output': [
            {"user_id": 1, "name": "Alice", "total_spent": 17.0},
            {"user_id": 3, "name": "Charlie", "total_spent": 16.0},
        ],
        'correct_code': """
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import sum as spark_sum

def solve(spark: SparkSession, users: list[dict], purchases: list[dict]) -> DataFrame:
    users_df = spark.createDataFrame(users)
    purchases_df = spark.createDataFrame(purchases)

    # Filter adults (age >= 30)
    adults = users_df.filter(users_df.age >= 30)

    # Aggregate purchases
    user_spending = purchases_df.groupBy("user_id").agg(spark_sum("price").alias("total_spent"))

    # Join and select
    result = adults.join(user_spending, "user_id").select("user_id", "name", "total_spent")
    return result.orderBy("user_id")
""",
    }


# =============================================================================
# Service Fixtures
# =============================================================================

@pytest.fixture
def executor():
    """Create ExecutorV2 instance"""
    from app.services.executor_v2 import ExecutorV2
    return ExecutorV2(timeout_seconds=60)


@pytest.fixture
def event_tracker():
    """Create SparkEventTracker using settings"""
    from app.services.spark_event_tracker import SparkEventTracker
    return SparkEventTracker()  # Uses settings defaults


@pytest.fixture
def execution_simulator(event_tracker):
    """Create ExecutionSimulatorV2 with real event tracker"""
    from app.services.execution_simulator_v2 import ExecutionSimulatorV2
    return ExecutionSimulatorV2(event_tracker)


@pytest.fixture
def judge():
    """Create JudgeV2 for full integration testing"""
    from app.services.judge_v2 import JudgeV2
    return JudgeV2()


@pytest.fixture
def operation_detector():
    """Create OperationDetector"""
    from app.services.operation_detector import OperationDetector
    return OperationDetector()


@pytest.fixture
def hint_generator():
    """Create HintGenerator"""
    from app.services.hint_generator import HintGenerator
    return HintGenerator()


# =============================================================================
# Legacy Fixtures (for backward compatibility)
# =============================================================================

@pytest.fixture
def sample_code_valid():
    """Valid code for testing"""
    return "result = fruits.sort_values('type')"


@pytest.fixture
def sample_code_error():
    """Code with syntax error"""
    return "result = fruits.sort_values('type'"


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
