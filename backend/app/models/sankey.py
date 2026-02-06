from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class JoinStep(BaseModel):
    """Parsed from physical plan"""
    join_type: str              # "SortMergeJoin", "BroadcastHashJoin"
    join_keys: List[str]        # ["user_id"]
    left_child: str             # dataset name or sub-plan ref
    right_child: str
    shuffle_partitions: int = 0
    exchange_type: str = "hashpartitioning"  # "hashpartitioning", "none" (broadcast)


class BucketGroup(BaseModel):
    partition_start: int
    partition_end: int
    label: str                  # "R0-R24"
    total_records: int = 0
    total_bytes: int = 0
    shuffle_read_bytes: int = 0
    shuffle_write_bytes: int = 0
    is_skewed: bool = False
    skew_ratio: float = 0.0     # max_task / median_task


class SankeyNode(BaseModel):
    id: str                     # "df_a_stage_0", "bucket_stage_0_0_24"
    type: str                   # "dataset" | "bucketGroup" | "exchange" | "result"
    label: str
    layer: int                  # 0=input, 1=exchange, 2=buckets, 3=output
    stageId: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)
    isSkewed: bool = False
    skewReason: Optional[str] = None
    partitionRange: Optional[List[int]] = None
    partitionCount: Optional[int] = None
    keys: Optional[List[str]] = None
    shufflePartitions: Optional[int] = None


class SankeyLink(BaseModel):
    id: str
    source: str                 # node id
    target: str
    value: int = 0              # sqrt-scaled for Recharts
    rawValue: int = 0           # original bytes for tooltip
    metrics: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)


class SankeyStage(BaseModel):
    id: str                     # "stage_0"
    label: str                  # "Stage 1: A ⋈ B → D"
    description: str = ""
    joinType: str = ""
    joinKey: str = ""
    shufflePartitions: int = 0
    metrics: Dict[str, Any] = Field(default_factory=dict)


class Recommendation(BaseModel):
    rule: str                   # "skew_detected", "broadcast_candidate", etc.
    severity: str               # "warning" | "info" | "critical"
    stageId: str
    message: str
    suggestion: str


class SankeySpec(BaseModel):
    specVersion: str = "spark-sankey/v1"
    meta: Dict[str, str] = Field(default_factory=dict)
    stages: List[SankeyStage] = Field(default_factory=list)
    nodes: List[SankeyNode] = Field(default_factory=list)
    links: List[SankeyLink] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
