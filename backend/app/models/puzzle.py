from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator
from .enums import Difficulty, ConceptTag
from .execution import ExecutorInfo

class PuzzleMetadata(BaseModel):
    """Basic puzzle information for listing"""
    id: str
    title: str
    description: str
    difficulty: Difficulty
    tags: List[ConceptTag]

class Puzzle(PuzzleMetadata):
    """Complete puzzle definition"""
    scenario: str = Field(description="Detailed scenario description")
    goal: str = Field(description="What the user needs to achieve")
    initial_data: Dict[str, Any] = Field(description="Input datasets")
    expected_output: Any = Field(description="Expected result (can be list or dict)")
    starter_code: Optional[str] = Field(default=None, description="Optional starter code")
    optimal_solution: str = Field(description="Reference optimal solution")
    visualization_config: Optional[Dict[str, Any]] = Field(default=None)

class SparkConfig(BaseModel):
    """Optional Spark configuration overrides from the frontend.

    All fields default to None — the executor falls back to settings.*
    when a field is not explicitly provided by the frontend.
    """
    shuffle_partitions: Optional[int] = Field(default=None, ge=1, le=200)
    executor_cores: Optional[int] = Field(default=None, ge=1, le=10)
    executor_memory: Optional[str] = Field(default=None)

    @validator("executor_memory")
    def validate_executor_memory(cls, v):
        if v is not None and v not in ("512m", "1g", "2g", "4g"):
            raise ValueError("executor_memory must be one of: 512m, 1g, 2g, 4g")
        return v


class RunRequest(BaseModel):
    """Request to run user code"""
    code: str = Field(description="User's Python/PySpark code")
    spark_config: Optional[SparkConfig] = Field(default=None, description="Optional Spark config overrides")

class MetricsResult(BaseModel):
    """Performance metrics from execution"""
    time_simulated: float = Field(description="Simulated execution time in seconds")
    shuffles: int = Field(description="Number of shuffle operations")
    stages: int = Field(description="Number of Spark stages")
    skew_detected: bool = Field(default=False, description="Whether data skew was detected")
    cache_used: bool = Field(default=False, description="Whether caching was used")
    broadcast_used: bool = Field(default=False, description="Whether broadcast join was used")

class RunResult(BaseModel):
    """Result of code execution"""
    correct: bool = Field(description="Whether output matches expected result")
    output: Optional[Any] = Field(description="Actual output from code execution")
    expected_output: Optional[Any] = Field(default=None, description="Expected output for comparison")
    user_code: Optional[str] = Field(default=None, description="The user code that was executed")
    metrics: MetricsResult
    stars: int = Field(ge=0, le=3, description="Star rating (0-3)")
    hint: Optional[str] = Field(default=None, description="Hint for improvement")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    execution_log: Optional[str] = Field(default=None, description="Execution logs")
    dag_structure: Optional[Dict[str, Any]] = Field(default=None, description="DAG structure from Spark query plan")
    physical_plan: Optional[str] = Field(default=None, description="Spark physical execution plan")
    logical_plan: Optional[str] = Field(default=None, description="Spark logical query plan")
    spark_ui_url: Optional[str] = Field(default=None, description="URL to Spark UI for this execution")
    execution_simulation: Optional[Any] = Field(default=None, description="Execution simulation data for Factory View visualization")
    stage_flow: Optional[Dict[str, Any]] = Field(default=None, description="Stage-by-stage execution flow for interactive visualization")
    cluster_config: Optional[Dict[str, Any]] = Field(default=None, description="Spark cluster configuration and resource information")
    executors_info: Optional[List[ExecutorInfo]] = Field(default=None, description="Spark executors information")
