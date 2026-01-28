from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Task(BaseModel):
    """Represents a single task in a stage"""
    id: int = Field(description="Task ID")
    partition_id: int = Field(description="Partition this task processes")
    node_id: int = Field(description="Node/executor this task runs on")
    core_id: int = Field(description="Core ID within the node")
    start_time: float = Field(description="Start time in seconds from execution start")
    end_time: float = Field(description="End time in seconds from execution start")
    duration: float = Field(description="Duration in seconds")
    status: str = Field(default="completed", description="Task status: queued, running, completed, failed")

class Partition(BaseModel):
    """Represents a data partition"""
    id: int = Field(description="Partition ID")
    size_mb: float = Field(description="Approximate size in MB")
    records_count: int = Field(description="Approximate number of records")
    data_preview: Optional[List[Dict[str, Any]]] = Field(default=None, description="Sample data from partition")

    # Lineage tracking fields
    stage_id: int = Field(description="Stage this partition belongs to")
    parent_partitions: List[int] = Field(default_factory=list, description="Parent partition IDs for lineage tracking")
    child_partitions: List[int] = Field(default_factory=list, description="Child partition IDs for lineage tracking")

class Shuffle(BaseModel):
    """Represents a shuffle operation between stages"""
    from_stage_id: int = Field(description="Source stage ID")
    to_stage_id: int = Field(description="Destination stage ID")
    data_volume_mb: float = Field(description="Total data volume shuffled in MB")
    from_partitions: int = Field(description="Number of partitions in source")
    to_partitions: int = Field(description="Number of partitions in destination")
    start_time: float = Field(description="Shuffle start time")
    end_time: float = Field(description="Shuffle end time")

    # Partition mapping for visualization
    partition_mapping: Dict[int, List[int]] = Field(
        default_factory=dict,
        description="Maps source partition IDs to dest partition IDs {source: [dest1, dest2]}"
    )

class Stage(BaseModel):
    """Represents a Spark execution stage"""
    id: int = Field(description="Stage ID")
    name: str = Field(description="Stage name/description (e.g., 'Scan + Project', 'HashAggregate')")
    operation_type: str = Field(description="Operation type: scan, filter, join, aggregate, shuffle, etc.")
    start_time: float = Field(description="Stage start time in seconds")
    end_time: float = Field(description="Stage end time in seconds")
    tasks: List[Task] = Field(description="Tasks in this stage")
    dependencies: List[int] = Field(default_factory=list, description="IDs of stages this depends on")
    parallelism: int = Field(description="Number of parallel tasks")
    status: str = Field(default="completed", description="Stage status: pending, running, completed")

class Node(BaseModel):
    """Represents a worker node in the cluster"""
    id: int = Field(description="Node ID")
    name: str = Field(description="Node name (e.g., 'Worker 1')")
    cores: int = Field(description="Number of CPU cores")
    memory_gb: float = Field(description="Available memory in GB")
    assigned_tasks: List[int] = Field(default_factory=list, description="IDs of tasks assigned to this node")

class ExecutorInfo(BaseModel):
    id: str = Field(description="Node ID")
    host: str = Field(description="Host Address")
    port: int = Field(description="Port use")
    cores: int = Field(description="Number of CPU cores")
    memory_mb: float = Field(description="Available memory in MB")
    memory_overhead_mb: float = Field(description="Memory overhead in MB")

class SimulationEvent(BaseModel):
    """Timeline event for animation"""
    time: float = Field(description="Event timestamp in seconds")
    event_type: str = Field(description="Event type: stage_start, stage_end, task_start, task_end, shuffle_start, shuffle_end")
    stage_id: Optional[int] = Field(default=None, description="Related stage ID")
    task_id: Optional[int] = Field(default=None, description="Related task ID")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional event details")

class ExecutionSimulation(BaseModel):
    """Complete execution simulation data"""
    total_duration: float = Field(description="Total execution time in seconds")
    partition_count: int = Field(description="Total number of partitions")
    node_count: int = Field(description="Number of worker nodes")
    cores_per_node: int = Field(description="CPU cores per node")
    total_cores: int = Field(description="Total CPU cores available")

    stages: List[Stage] = Field(description="Execution stages")
    partitions: List[Partition] = Field(description="Data partitions")
    shuffles: List[Shuffle] = Field(default_factory=list, description="Shuffle operations")
    nodes: List[Node] = Field(description="Worker nodes")
    events: List[SimulationEvent] = Field(description="Timeline events for animation")

    metrics: Dict[str, Any] = Field(default_factory=dict, description="Summary metrics")
