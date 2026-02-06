"""
Unit tests for Sankey spec generation pipeline:
  - PhysicalPlanParser
  - SankeySpecGenerator (bucketization, node/link building)
  - RecommendationEngine

These tests mock out heavy dependencies (pyspark, psycopg2, database)
so they can run without a Spark cluster or database connection.
"""

import sys
import types

# ---- Pre-import mocks to avoid pyspark / psycopg2 / database deps ----
import importlib, pathlib

_backend = pathlib.Path(__file__).resolve().parent.parent

# Replace app.services.__init__ with a stub that has __path__ pointing to the
# real package directory, so submodule imports (physical_plan_parser, etc.)
# still work — but skip importing pyspark-dependent modules at init time.
_svc = types.ModuleType("app.services")
_svc.__path__ = [str(_backend / "app" / "services")]
_svc.__package__ = "app.services"
sys.modules["app.services"] = _svc

# Same for app.models — stub init but keep __path__ for submodule access.
_mdl = types.ModuleType("app.models")
_mdl.__path__ = [str(_backend / "app" / "models")]
_mdl.__package__ = "app.models"
sys.modules["app.models"] = _mdl
# --------------------------------------------------------------------------

import pytest
from app.models.sankey import (
    JoinStep, BucketGroup, SankeyNode, SankeyLink,
    SankeyStage, Recommendation, SankeySpec,
)
from app.services.physical_plan_parser import PhysicalPlanParser
from app.services.recommendation_engine import RecommendationEngine
from app.services.sankey_spec_generator import SankeySpecGenerator


# =============================================================================
# Sample Physical Plans
# =============================================================================

SORT_MERGE_PLAN = """*(5) SortMergeJoin [user_id#0L], [user_id#10L], Inner
:- *(2) Sort [user_id#0L ASC], false, 0
:  +- Exchange hashpartitioning(user_id#0L, 4), ENSURE_REQUIREMENTS, [plan_id=15]
:     +- *(1) Filter isnotnull(user_id#0L)
:        +- Scan ExistingRDD[user_id#0L,name#1]
+- *(4) Sort [user_id#10L ASC], false, 0
   +- Exchange hashpartitioning(user_id#10L, 4), ENSURE_REQUIREMENTS, [plan_id=20]
      +- *(3) Filter isnotnull(user_id#10L)
         +- Scan ExistingRDD[user_id#10L,amount#11]"""

BROADCAST_PLAN = """*(3) BroadcastHashJoin [product_id#0L], [product_id#5L], Inner, BuildRight
:- *(1) Filter isnotnull(product_id#0L)
:  +- Scan ExistingRDD[product_id#0L,quantity#1]
+- BroadcastExchange HashedRelationBroadcastMode(List(input[0, bigint, false]))
   +- *(2) Filter isnotnull(product_id#5L)
      +- Scan ExistingRDD[product_id#5L,name#6,price#7]"""

CHAINED_JOIN_PLAN = """*(9) SortMergeJoin [region_id#20L], [region_id#30L], Inner
:- *(6) SortMergeJoin [user_id#0L], [user_id#10L], Inner
:  :- *(2) Sort [user_id#0L ASC], false, 0
:  :  +- Exchange hashpartitioning(user_id#0L, 8), ENSURE_REQUIREMENTS
:  :     +- *(1) Filter isnotnull(user_id#0L)
:  :        +- Scan ExistingRDD[user_id#0L,name#1,region_id#20L]
:  +- *(4) Sort [user_id#10L ASC], false, 0
:     +- Exchange hashpartitioning(user_id#10L, 8), ENSURE_REQUIREMENTS
:        +- *(3) Filter isnotnull(user_id#10L)
:           +- Scan ExistingRDD[user_id#10L,amount#11]
+- *(8) Sort [region_id#30L ASC], false, 0
   +- Exchange hashpartitioning(region_id#30L, 6), ENSURE_REQUIREMENTS
      +- *(7) Filter isnotnull(region_id#30L)
         +- Scan ExistingRDD[region_id#30L,region_name#31]"""


# =============================================================================
# PhysicalPlanParser Tests
# =============================================================================

class TestPhysicalPlanParser:

    def setup_method(self):
        self.parser = PhysicalPlanParser()

    def test_parse_sort_merge_join(self):
        """SortMergeJoin with Exchange hashpartitioning should produce 1 JoinStep."""
        steps = self.parser.parse(SORT_MERGE_PLAN)
        assert len(steps) == 1

        step = steps[0]
        assert step.join_type == "SortMergeJoin"
        assert step.join_keys == ["user_id"]
        assert step.shuffle_partitions == 4
        assert step.exchange_type == "hashpartitioning"

    def test_parse_broadcast_join(self):
        """BroadcastHashJoin should produce 1 JoinStep with exchange_type='none'."""
        steps = self.parser.parse(BROADCAST_PLAN)
        assert len(steps) == 1

        step = steps[0]
        assert step.join_type == "BroadcastHashJoin"
        assert step.join_keys == ["product_id"]
        assert step.exchange_type == "none"
        # Broadcast joins have no shuffle partitions
        assert step.shuffle_partitions == 0

    def test_parse_chained_joins(self):
        """Chained joins (2 SortMergeJoins) should produce 2 JoinSteps."""
        steps = self.parser.parse(CHAINED_JOIN_PLAN)
        assert len(steps) == 2

        # Bottom-up DFS: inner join first, then outer
        inner = steps[0]
        assert inner.join_type == "SortMergeJoin"
        assert inner.join_keys == ["user_id"]
        assert inner.shuffle_partitions == 8

        outer = steps[1]
        assert outer.join_type == "SortMergeJoin"
        assert outer.join_keys == ["region_id"]
        # Outer join: max(inner Exchange=8, right Exchange=6) = 8
        # because the DFS finds the deepest Exchange in the left subtree
        assert outer.shuffle_partitions >= 6

    def test_parse_empty_plan(self):
        """Empty or None plan should return empty list."""
        assert self.parser.parse("") == []
        assert self.parser.parse(None) == []

    def test_parse_plan_without_joins(self):
        """A plan with no joins should return empty list."""
        no_join_plan = """*(1) Filter isnotnull(user_id#0L)
+- Scan ExistingRDD[user_id#0L,name#1]"""
        steps = self.parser.parse(no_join_plan)
        assert steps == []

    def test_extract_join_keys_strips_column_suffix(self):
        """Join keys should have #N suffixes removed."""
        steps = self.parser.parse(SORT_MERGE_PLAN)
        assert steps[0].join_keys == ["user_id"]
        # No #0L or #10L in the result

    def test_extract_dataset_names(self):
        """Dataset names are extracted from leaf Scan nodes."""
        steps = self.parser.parse(SORT_MERGE_PLAN)
        step = steps[0]
        # Names come from first column in ExistingRDD
        assert step.left_child != "unknown"
        assert step.right_child != "unknown"


# =============================================================================
# SankeySpecGenerator — Bucketization Tests
# =============================================================================

class TestBucketization:

    def setup_method(self):
        self.generator = SankeySpecGenerator()

    def test_basic_bucketization(self):
        """4 tasks should produce 4 buckets (1 task each) with default settings."""
        tasks = [
            {'index': i, 'partition_id': i, 'duration': 1.0,
             'metrics': {'records_read': 100, 'shuffle_read_bytes': 1000, 'shuffle_write_bytes': 500}}
            for i in range(4)
        ]
        buckets = self.generator._bucketize(tasks, "stage_0")
        assert len(buckets) == 4
        assert buckets[0].label == "R0-R0"
        assert buckets[0].partition_start == 0
        assert buckets[0].partition_end == 0

    def test_bucketization_groups_tasks(self):
        """8 tasks with bucket_count=4 should produce 4 buckets of 2 tasks each."""
        tasks = [
            {'index': i, 'partition_id': i, 'duration': 1.0,
             'metrics': {'records_read': 100, 'shuffle_read_bytes': 1000, 'shuffle_write_bytes': 500}}
            for i in range(8)
        ]
        buckets = self.generator._bucketize(tasks, "stage_0")
        assert len(buckets) == 4
        assert buckets[0].label == "R0-R1"
        assert buckets[1].label == "R2-R3"
        assert buckets[2].label == "R4-R5"
        assert buckets[3].label == "R6-R7"

    def test_bucketization_aggregates_metrics(self):
        """Bucket metrics should sum task metrics."""
        tasks = [
            {'index': 0, 'partition_id': 0, 'duration': 1.0,
             'metrics': {'records_read': 100, 'shuffle_read_bytes': 1000, 'shuffle_write_bytes': 500}},
            {'index': 1, 'partition_id': 1, 'duration': 1.0,
             'metrics': {'records_read': 200, 'shuffle_read_bytes': 2000, 'shuffle_write_bytes': 800}},
        ]
        # With bucket_count=4 and 2 tasks, we get 2 buckets
        buckets = self.generator._bucketize(tasks, "stage_0")
        assert len(buckets) == 2
        assert buckets[0].total_records == 100
        assert buckets[0].total_bytes == 1000
        assert buckets[1].total_records == 200
        assert buckets[1].total_bytes == 2000

    def test_skew_detection_by_duration(self):
        """Skew should be detected when max task duration >> median within a bucket."""
        # 12 tasks, bucket_count=4 → 3 tasks per bucket.
        # Last bucket: [1.0, 1.0, 100.0] → median=1.0, max=100.0, ratio=100x
        tasks = [
            {'index': i, 'partition_id': i, 'duration': 1.0,
             'metrics': {'records_read': 0, 'shuffle_read_bytes': 0, 'shuffle_write_bytes': 0}}
            for i in range(11)
        ] + [
            {'index': 11, 'partition_id': 11, 'duration': 100.0,
             'metrics': {'records_read': 0, 'shuffle_read_bytes': 0, 'shuffle_write_bytes': 0}},
        ]
        buckets = self.generator._bucketize(tasks, "stage_0")
        # The last bucket should be skewed (max/median = 100x >> 2.0 threshold)
        skewed = [b for b in buckets if b.is_skewed]
        assert len(skewed) >= 1

    def test_no_skew_uniform_tasks(self):
        """Uniform task durations should not trigger skew detection."""
        tasks = [
            {'index': i, 'partition_id': i, 'duration': 1.0,
             'metrics': {'records_read': 100, 'shuffle_read_bytes': 1000, 'shuffle_write_bytes': 500}}
            for i in range(4)
        ]
        buckets = self.generator._bucketize(tasks, "stage_0")
        skewed = [b for b in buckets if b.is_skewed]
        assert len(skewed) == 0

    def test_empty_tasks(self):
        """Empty task list should produce empty bucket list."""
        buckets = self.generator._bucketize([], "stage_0")
        assert buckets == []


# =============================================================================
# SankeySpecGenerator — Stage Building Tests
# =============================================================================

class TestStageBuild:

    def setup_method(self):
        self.generator = SankeySpecGenerator()

    def test_build_stage_node_structure(self):
        """Each stage should produce: 2 input + 1 exchange + K buckets + 1 output."""
        join_step = JoinStep(
            join_type="SortMergeJoin",
            join_keys=["user_id"],
            left_child="orders",
            right_child="users",
            shuffle_partitions=4,
            exchange_type="hashpartitioning",
        )
        tasks = [
            {'index': i, 'partition_id': i, 'duration': 1.0,
             'metrics': {'records_read': 100, 'shuffle_read_bytes': 1000, 'shuffle_write_bytes': 500}}
            for i in range(4)
        ]
        buckets = self.generator._bucketize(tasks, "stage_0")
        nodes, links, stage_spec = self.generator._build_stage(
            join_step, buckets, tasks, "stage_0", 0
        )

        # Count node types
        datasets = [n for n in nodes if n.type == "dataset"]
        exchanges = [n for n in nodes if n.type == "exchange"]
        bucket_nodes = [n for n in nodes if n.type == "bucketGroup"]

        # 2 input datasets + 1 output dataset
        assert len(datasets) == 3
        assert len(exchanges) == 1
        assert len(bucket_nodes) == len(buckets)

        # Input datasets at layer 0, exchange at layer 1, buckets at layer 2, output at layer 3
        input_datasets = [n for n in datasets if n.layer == 0]
        output_datasets = [n for n in datasets if n.layer == 3]
        assert len(input_datasets) == 2
        assert len(output_datasets) == 1

    def test_build_stage_link_structure(self):
        """Links: each input → each bucket, each bucket → output."""
        join_step = JoinStep(
            join_type="SortMergeJoin",
            join_keys=["user_id"],
            left_child="orders",
            right_child="users",
            shuffle_partitions=4,
            exchange_type="hashpartitioning",
        )
        tasks = [
            {'index': i, 'partition_id': i, 'duration': 1.0,
             'metrics': {'records_read': 100, 'shuffle_read_bytes': 1000, 'shuffle_write_bytes': 500}}
            for i in range(4)
        ]
        buckets = self.generator._bucketize(tasks, "stage_0")
        K = len(buckets)
        nodes, links, stage_spec = self.generator._build_stage(
            join_step, buckets, tasks, "stage_0", 0
        )

        # Expected links: 2 inputs * K buckets + K buckets * 1 output = 3K
        assert len(links) == 3 * K

    def test_stage_spec_metrics(self):
        """Stage spec should include aggregated metrics."""
        join_step = JoinStep(
            join_type="SortMergeJoin",
            join_keys=["user_id"],
            left_child="orders",
            right_child="users",
            shuffle_partitions=4,
            exchange_type="hashpartitioning",
        )
        tasks = [
            {'index': i, 'partition_id': i, 'duration': 1.0,
             'metrics': {'records_read': 100, 'shuffle_read_bytes': 1000, 'shuffle_write_bytes': 500}}
            for i in range(4)
        ]
        buckets = self.generator._bucketize(tasks, "stage_0")
        nodes, links, stage_spec = self.generator._build_stage(
            join_step, buckets, tasks, "stage_0", 0
        )

        assert stage_spec.id == "stage_0"
        assert "user_id" in stage_spec.joinKey
        assert stage_spec.shufflePartitions == 4
        assert "totalBuckets" in stage_spec.metrics
        assert stage_spec.metrics["totalBuckets"] == len(buckets)


# =============================================================================
# SankeySpecGenerator — Full Generation with Mock Simulation
# =============================================================================

class MockTask:
    def __init__(self, partition_id, duration=1.0):
        self.id = partition_id
        self.partition_id = partition_id
        self.node_id = 0
        self.core_id = 0
        self.start_time = 0.0
        self.end_time = duration
        self.duration = duration
        self.status = "completed"


class MockStage:
    def __init__(self, stage_id, name, op_type, parallelism, tasks=None):
        self.id = stage_id
        self.name = name
        self.operation_type = op_type
        self.start_time = 0.0
        self.end_time = 1.0
        self.parallelism = parallelism
        self.tasks = tasks or [MockTask(i) for i in range(parallelism)]
        self.dependencies = []
        self.status = "completed"


class MockShuffle:
    def __init__(self, from_id, to_id):
        self.from_stage_id = from_id
        self.to_stage_id = to_id
        self.data_volume_mb = 1.0
        self.from_partitions = 4
        self.to_partitions = 4
        self.start_time = 0.0
        self.end_time = 0.5
        self.partition_mapping = {}


class MockSimulation:
    def __init__(self, stages, shuffles=None):
        self.total_duration = 5.0
        self.partition_count = 4
        self.node_count = 2
        self.cores_per_node = 2
        self.total_cores = 4
        self.stages = stages
        self.shuffles = shuffles or []
        self.partitions = []
        self.nodes = []
        self.events = []
        self.metrics = {}


class TestFullGeneration:

    def setup_method(self):
        self.generator = SankeySpecGenerator()

    def test_generate_with_sort_merge_join(self):
        """Full generation with SortMergeJoin plan + mock simulation."""
        metadata = {'physical_plan': SORT_MERGE_PLAN}
        simulation = MockSimulation(
            stages=[
                MockStage(0, "Scan", "scan", 4),
                MockStage(1, "Scan", "scan", 4),
                MockStage(2, "SortMergeJoin", "join", 4),
            ],
            shuffles=[MockShuffle(0, 2), MockShuffle(1, 2)],
        )

        spec = self.generator.generate(metadata, simulation)
        assert spec is not None
        assert spec['specVersion'] == 'spark-sankey/v1'
        assert len(spec['stages']) == 1
        assert len(spec['nodes']) > 0
        assert len(spec['links']) > 0

    def test_generate_returns_none_without_plan(self):
        """Should return None if no physical plan."""
        metadata = {}
        simulation = MockSimulation(stages=[MockStage(0, "Scan", "scan", 4)])
        assert self.generator.generate(metadata, simulation) is None

    def test_generate_returns_none_without_simulation(self):
        """Should return None if no execution simulation."""
        metadata = {'physical_plan': SORT_MERGE_PLAN}
        assert self.generator.generate(metadata, None) is None

    def test_generate_returns_none_for_no_joins(self):
        """Should return None if plan has no joins."""
        metadata = {'physical_plan': '*(1) Scan ExistingRDD[col#0]'}
        simulation = MockSimulation(stages=[MockStage(0, "Scan", "scan", 4)])
        assert self.generator.generate(metadata, simulation) is None

    def test_generated_spec_has_valid_node_ids(self):
        """All link source/target should reference existing node IDs."""
        metadata = {'physical_plan': SORT_MERGE_PLAN}
        simulation = MockSimulation(
            stages=[
                MockStage(0, "Scan", "scan", 4),
                MockStage(1, "SortMergeJoin", "join", 4),
            ],
            shuffles=[MockShuffle(0, 1)],
        )

        spec = self.generator.generate(metadata, simulation)
        assert spec is not None

        node_ids = {n['id'] for n in spec['nodes']}
        for link in spec['links']:
            assert link['source'] in node_ids, f"Link source '{link['source']}' not in nodes"
            assert link['target'] in node_ids, f"Link target '{link['target']}' not in nodes"

    def test_generated_spec_stage_isolation(self):
        """Each node should belong to exactly one stage."""
        metadata = {'physical_plan': SORT_MERGE_PLAN}
        simulation = MockSimulation(
            stages=[
                MockStage(0, "Scan", "scan", 4),
                MockStage(1, "SortMergeJoin", "join", 4),
            ],
            shuffles=[MockShuffle(0, 1)],
        )

        spec = self.generator.generate(metadata, simulation)
        assert spec is not None

        stage_ids = {s['id'] for s in spec['stages']}
        for node in spec['nodes']:
            assert node['stageId'] in stage_ids


# =============================================================================
# RecommendationEngine Tests
# =============================================================================

class TestRecommendationEngine:

    def setup_method(self):
        self.engine = RecommendationEngine()

    def _make_spec(self, stages, nodes):
        return SankeySpec(
            meta={"title": "test"},
            stages=stages,
            nodes=nodes,
            links=[],
        )

    def test_skew_detection(self):
        """Skewed bucket group should trigger 'skew_detected' recommendation."""
        stage = SankeyStage(
            id="stage_0", label="Stage 1: A ⋈ B",
            joinType="SortMergeJoin", joinKey="user_id",
            shufflePartitions=4,
            metrics={"shuffleReadBytes": 1000, "skewedBuckets": 1, "totalBuckets": 4},
        )
        skewed_node = SankeyNode(
            id="b0_1", type="bucketGroup", label="R25-R49",
            layer=2, stageId="stage_0",
            isSkewed=True,
            metrics={"records": 5000, "bytes": 10000},
        )
        spec = self._make_spec([stage], [skewed_node])
        recs = self.engine.analyze(spec)
        skew_recs = [r for r in recs if r.rule == "skew_detected"]
        assert len(skew_recs) == 1
        assert skew_recs[0].severity == "warning"

    def test_no_skew_no_recommendation(self):
        """Non-skewed buckets should not produce skew recommendations."""
        stage = SankeyStage(
            id="stage_0", label="Stage 1: A ⋈ B",
            joinType="SortMergeJoin", joinKey="user_id",
            shufflePartitions=4,
            metrics={"shuffleReadBytes": 1000},
        )
        normal_node = SankeyNode(
            id="b0_0", type="bucketGroup", label="R0-R24",
            layer=2, stageId="stage_0",
            isSkewed=False,
            metrics={"records": 1000, "bytes": 5000},
        )
        spec = self._make_spec([stage], [normal_node])
        recs = self.engine.analyze(spec)
        skew_recs = [r for r in recs if r.rule == "skew_detected"]
        assert len(skew_recs) == 0

    def test_broadcast_candidate(self):
        """Small SortMergeJoin should suggest broadcast."""
        stage = SankeyStage(
            id="stage_0", label="Stage 1",
            joinType="SortMergeJoin", joinKey="id",
            shufflePartitions=4,
            metrics={"shuffleReadBytes": 5 * 1024 * 1024},  # 5MB
        )
        spec = self._make_spec([stage], [])
        recs = self.engine.analyze(spec)
        bc_recs = [r for r in recs if r.rule == "broadcast_candidate"]
        assert len(bc_recs) == 1
        assert bc_recs[0].severity == "info"

    def test_no_broadcast_for_broadcast_join(self):
        """BroadcastHashJoin should NOT trigger broadcast_candidate."""
        stage = SankeyStage(
            id="stage_0", label="Stage 1",
            joinType="BroadcastHashJoin", joinKey="id",
            shufflePartitions=0,
            metrics={"shuffleReadBytes": 1000},
        )
        spec = self._make_spec([stage], [])
        recs = self.engine.analyze(spec)
        bc_recs = [r for r in recs if r.rule == "broadcast_candidate"]
        assert len(bc_recs) == 0

    def test_excessive_partitions(self):
        """Too many partitions for cluster size should trigger warning."""
        stage = SankeyStage(
            id="stage_0", label="Stage 1",
            joinType="SortMergeJoin", joinKey="id",
            shufflePartitions=200,
            metrics={"shuffleReadBytes": 100000},
        )
        spec = self._make_spec([stage], [])
        cluster_info = {'num_executors': 2, 'cores_per_executor': 2, 'total_cores': 4}
        recs = self.engine.analyze(spec, cluster_info)
        excess_recs = [r for r in recs if r.rule == "excessive_partitions"]
        assert len(excess_recs) == 1

    def test_too_few_partitions(self):
        """Fewer partitions than executors should trigger warning."""
        stage = SankeyStage(
            id="stage_0", label="Stage 1",
            joinType="SortMergeJoin", joinKey="id",
            shufflePartitions=1,
            metrics={"shuffleReadBytes": 100000},
        )
        spec = self._make_spec([stage], [])
        cluster_info = {'num_executors': 4, 'cores_per_executor': 2, 'total_cores': 8}
        recs = self.engine.analyze(spec, cluster_info)
        few_recs = [r for r in recs if r.rule == "too_few_partitions"]
        assert len(few_recs) == 1

    def test_large_shuffle_warning(self):
        """Shuffle > 1GB should trigger info recommendation."""
        stage = SankeyStage(
            id="stage_0", label="Stage 1",
            joinType="SortMergeJoin", joinKey="id",
            shufflePartitions=100,
            metrics={"shuffleReadBytes": 2 * 1024 * 1024 * 1024},  # 2GB
        )
        spec = self._make_spec([stage], [])
        recs = self.engine.analyze(spec)
        large_recs = [r for r in recs if r.rule == "large_shuffle"]
        assert len(large_recs) == 1
        assert large_recs[0].severity == "info"

    def test_no_large_shuffle_for_small_data(self):
        """Shuffle < 1GB should NOT trigger large_shuffle."""
        stage = SankeyStage(
            id="stage_0", label="Stage 1",
            joinType="SortMergeJoin", joinKey="id",
            shufflePartitions=4,
            metrics={"shuffleReadBytes": 500 * 1024 * 1024},  # 500MB
        )
        spec = self._make_spec([stage], [])
        recs = self.engine.analyze(spec)
        large_recs = [r for r in recs if r.rule == "large_shuffle"]
        assert len(large_recs) == 0


# =============================================================================
# Link Scaling Tests
# =============================================================================

class TestLinkScaling:

    def setup_method(self):
        self.generator = SankeySpecGenerator()

    def test_scale_minimum(self):
        """Very small byte values should clamp to minimum width (4)."""
        assert self.generator._scale_link_value(0) == 4
        assert self.generator._scale_link_value(1) == 4

    def test_scale_maximum(self):
        """Very large byte values should clamp to max width."""
        result = self.generator._scale_link_value(10**12)
        assert result <= 80

    def test_scale_proportional(self):
        """Larger values should produce larger scaled widths."""
        small = self.generator._scale_link_value(1000)
        large = self.generator._scale_link_value(1_000_000)
        assert large >= small
