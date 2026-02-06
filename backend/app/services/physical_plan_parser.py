"""
Parse Spark physical plan string into structured JoinStep objects.

Handles:
  - SortMergeJoin [key1, key2], [key1, key2], Inner
  - BroadcastHashJoin [key], [key], Inner, BuildRight
  - BroadcastNestedLoopJoin ... (cross join)
  - Exchange hashpartitioning(key, N)
  - Scan ExistingRDD / InMemoryRelation / FileScan
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

from app.models.sankey import JoinStep


@dataclass
class PlanNode:
    """A node in the parsed plan tree."""
    line: str
    depth: int
    children: list = field(default_factory=list)


class PhysicalPlanParser:

    # Patterns
    _JOIN_RE = re.compile(
        r'(SortMergeJoin|BroadcastHashJoin|BroadcastNestedLoopJoin)'
        r'\s*\[([^\]]*)\]'   # first key list
        r'(?:,\s*\[([^\]]*)\])?'  # optional second key list
        r'(?:,\s*(\w+))?',        # join type (Inner, LeftOuter, etc.)
        re.IGNORECASE,
    )

    _EXCHANGE_RE = re.compile(
        r'Exchange\s+hashpartitioning\(([^)]+)\)',
        re.IGNORECASE,
    )

    _SCAN_RE = re.compile(
        r'(?:Scan\s+ExistingRDD|InMemoryRelation|FileScan\s+\w+)\s*\[([^\]]*)\]',
        re.IGNORECASE,
    )

    _DATASET_NAME_RE = re.compile(
        r'(?:Scan\s+ExistingRDD|InMemoryRelation|FileScan\s+\w+)\s*\[([^\]]*)\]',
        re.IGNORECASE,
    )

    # ------------------------------------------------------------------ public

    def parse(self, physical_plan: str) -> List[JoinStep]:
        """Main entry point — parse a physical plan string into JoinSteps."""
        if not physical_plan:
            return []

        root = self._tokenize_plan(physical_plan)
        if root is None:
            return []

        joins = self._find_joins(root)
        return joins

    # ----------------------------------------------------------- tokenisation

    def _tokenize_plan(self, plan: str) -> Optional[PlanNode]:
        """Convert indented text into a tree of PlanNode objects."""
        lines = plan.strip().split('\n')
        if not lines:
            return None

        nodes: List[Tuple[int, PlanNode]] = []
        for raw_line in lines:
            stripped = raw_line.lstrip()
            if not stripped:
                continue

            # Compute depth from the indentation characters
            depth = self._compute_depth(raw_line)
            nodes.append((depth, PlanNode(line=stripped, depth=depth)))

        if not nodes:
            return None

        # Build tree: each node's children are subsequent nodes at depth+1
        # that appear before the next node at the same or shallower depth.
        root = PlanNode(line="ROOT", depth=-1)
        stack: List[PlanNode] = [root]

        for depth, node in nodes:
            # Pop stack until we find a parent whose depth < this node's depth
            while len(stack) > 1 and stack[-1].depth >= depth:
                stack.pop()
            stack[-1].children.append(node)
            stack.append(node)

        return root

    def _compute_depth(self, line: str) -> int:
        """
        Compute logical depth from Spark plan indentation.

        Spark uses tree-drawing characters (:, +, -, |, spaces) as prefix.
        The depth is determined by the character position where the actual
        content (non-tree-drawing) starts.

        Examples:
          *(5) SortMergeJoin...              → position 0 → depth 0
          :- *(2) Sort...                    → position 3 → depth 1
          :  +- Exchange...                  → position 6 → depth 2
          :     +- *(1) Filter...            → position 9 → depth 3
          :        +- Scan ExistingRDD...    → position 12 → depth 4
          +- *(4) Sort...                    → position 3 → depth 1
             +- Exchange...                  → position 6 → depth 2
        """
        # Find position of first non-tree-drawing character
        i = 0
        while i < len(line) and line[i] in ' :|-+':
            i += 1

        # Spark typically uses ~3 chars per indent level
        return i // 3

    # --------------------------------------------------------- join extraction

    def _find_joins(self, root: PlanNode) -> List[JoinStep]:
        """DFS to find join operators and their children."""
        results: List[JoinStep] = []
        self._dfs_joins(root, results)
        return results

    def _dfs_joins(self, node: PlanNode, results: List[JoinStep]):
        """Depth-first walk collecting JoinSteps (bottom-up: children first)."""
        for child in node.children:
            self._dfs_joins(child, results)

        match = self._JOIN_RE.search(node.line)
        if match:
            join_step = self._build_join_step(match, node)
            if join_step:
                results.append(join_step)

    def _build_join_step(self, match: re.Match, node: PlanNode) -> Optional[JoinStep]:
        """Build a JoinStep from a regex match and its child subtrees."""
        join_type = match.group(1)
        keys = self._extract_join_keys(match.group(2))

        # Determine if broadcast (no shuffle on one side)
        is_broadcast = 'broadcast' in join_type.lower()

        # Get the two child branches
        left_child_node = node.children[0] if len(node.children) > 0 else None
        right_child_node = node.children[1] if len(node.children) > 1 else None

        left_name = self._extract_dataset_name(left_child_node) if left_child_node else "unknown_left"
        right_name = self._extract_dataset_name(right_child_node) if right_child_node else "unknown_right"

        # Extract shuffle partitions from Exchange nodes
        shuffle_partitions = 0
        exchange_type = "none" if is_broadcast else "hashpartitioning"

        if not is_broadcast:
            left_parts = self._extract_shuffle_partitions(left_child_node) if left_child_node else 0
            right_parts = self._extract_shuffle_partitions(right_child_node) if right_child_node else 0
            shuffle_partitions = max(left_parts, right_parts)

        return JoinStep(
            join_type=join_type,
            join_keys=keys,
            left_child=left_name,
            right_child=right_name,
            shuffle_partitions=shuffle_partitions,
            exchange_type=exchange_type,
        )

    # ---------------------------------------------------------------- helpers

    def _extract_join_keys(self, keys_str: str) -> List[str]:
        """Parse 'key1#0L, key2#10L' → ['key1', 'key2']."""
        if not keys_str:
            return []
        keys = []
        for part in keys_str.split(','):
            part = part.strip()
            # Remove Spark column suffix like #0L, #10
            clean = re.sub(r'#\d+\w*', '', part).strip()
            if clean:
                keys.append(clean)
        return keys

    def _extract_shuffle_partitions(self, node: PlanNode) -> int:
        """
        Search subtree for Exchange hashpartitioning(..., N) → N.
        """
        if node is None:
            return 0

        match = self._EXCHANGE_RE.search(node.line)
        if match:
            # Parse the partition count from hashpartitioning(key, N)
            args = match.group(1)
            # Last numeric token is the partition count
            nums = re.findall(r'\b(\d+)\b', args)
            if nums:
                return int(nums[-1])

        # Recurse into children
        for child in node.children:
            result = self._extract_shuffle_partitions(child)
            if result > 0:
                return result

        return 0

    def _extract_dataset_name(self, node: PlanNode) -> str:
        """
        Walk down a subtree to find the leaf Scan/InMemoryRelation node
        and extract a meaningful dataset name from its column names.
        """
        if node is None:
            return "unknown"

        # Check current node
        name = self._try_extract_name(node.line)
        if name:
            return name

        # DFS into children
        for child in node.children:
            name = self._extract_dataset_name(child)
            if name and name != "unknown":
                return name

        return "unknown"

    def _try_extract_name(self, line: str) -> Optional[str]:
        """Try to extract a dataset name from a plan line."""
        # Match Scan ExistingRDD[col1#0, col2#1]
        match = self._SCAN_RE.search(line)
        if match:
            cols_str = match.group(1)
            # Take the first column name (without the # suffix) as a hint
            cols = [re.sub(r'#\d+\w*', '', c.strip()) for c in cols_str.split(',')]
            if cols:
                # Use first column as a dataset identifier heuristic
                return cols[0]
        return None
