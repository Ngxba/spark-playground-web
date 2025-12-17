from typing import Dict, Optional, List


class OperationDetector:
    """
    Analyzes Spark execution metadata to detect operations and patterns.
    Uses real Spark query plans instead of regex pattern matching.
    """

    @staticmethod
    def analyze_from_metadata(execution_metadata: Optional[Dict]) -> Dict[str, any]:
        """
        Analyze Spark execution metadata to detect operations and patterns.
        This uses REAL Spark query plans, not regex on code strings.

        Args:
            execution_metadata: Dictionary containing logical_plan, physical_plan, and metrics
                                from executor._extract_execution_metadata()

        Returns:
            Dict with detected operations and optimization patterns
        """
        if not execution_metadata or not execution_metadata.get('metrics'):
            # Fallback to empty analysis if no metadata
            return OperationDetector._empty_analysis()

        logical_plan = execution_metadata.get('logical_plan', '')
        physical_plan = execution_metadata.get('physical_plan', '')
        metrics = execution_metadata.get('metrics', {})

        operations = []

        # Detect operations from physical plan
        if metrics.get('has_aggregation'):
            operations.append('aggregation')
        if metrics.get('has_filter'):
            operations.append('filter')
        if metrics.get('has_sort'):
            operations.append('sort')
        if 'Join' in physical_plan:
            operations.append('join')
        if 'Aggregate' in physical_plan or 'GroupBy' in logical_plan:
            operations.append('groupby')
        if 'cache' in logical_plan.lower() or 'InMemoryRelation' in physical_plan:
            operations.append('cache')

        # Detect broadcast join
        has_broadcast = metrics.get('has_broadcast', False)

        # Detect shuffles (Exchange operations)
        has_shuffle = metrics.get('has_shuffle', False)
        num_shuffles = metrics.get('num_exchanges', 0)

        # Detect filter pushdown optimization
        filter_pushdown_applied = metrics.get('filter_pushdown_applied', False)

        # Detect inefficient patterns

        # 1. Filter after join (no pushdown)
        filter_after_join = False
        if 'Join' in physical_plan and 'Filter' in physical_plan:
            # If filter appears AFTER join in physical plan, it wasn't pushed down
            join_idx = physical_plan.find('Join')
            filter_idx = physical_plan.find('Filter')
            if filter_idx < join_idx:  # Filter comes before join in plan tree
                filter_after_join = False  # Good! Filter was pushed down
            else:
                filter_after_join = True  # Bad! Filter after join

        # 2. Join without broadcast (could cause shuffle)
        join_without_broadcast = False
        if 'Join' in physical_plan and not has_broadcast:
            # Check if it's a SortMergeJoin (requires shuffle)
            if 'SortMergeJoin' in physical_plan:
                join_without_broadcast = True

        # 3. Multiple aggregations without cache
        has_reuse_without_cache = False
        if 'cache' not in operations:
            # Count aggregate operations
            agg_count = logical_plan.count('Aggregate')
            if agg_count > 1:
                has_reuse_without_cache = True

        # Estimate execution stages
        estimated_stages = metrics.get('estimated_stages', 1)

        # Calculate performance score (0-3 stars)
        performance_score = OperationDetector._calculate_performance_score(
            has_broadcast=has_broadcast,
            has_shuffle=has_shuffle,
            num_shuffles=num_shuffles,
            filter_pushdown_applied=filter_pushdown_applied,
            has_cache='cache' in operations,
            join_without_broadcast=join_without_broadcast,
            filter_after_join=filter_after_join
        )

        return {
            'operations': operations,
            'has_shuffle': has_shuffle,
            'num_shuffles': num_shuffles,
            'has_join': 'join' in operations,
            'has_broadcast': has_broadcast,
            'has_cache': 'cache' in operations,
            'has_groupby': 'groupby' in operations,
            'has_filter': 'filter' in operations,
            'has_aggregation': 'aggregation' in operations,
            'filter_after_join': filter_after_join,
            'filter_pushdown_applied': filter_pushdown_applied,
            'join_without_broadcast': join_without_broadcast,
            'has_reuse_without_cache': has_reuse_without_cache,
            'estimated_stages': estimated_stages,
            'performance_score': performance_score,
            'logical_plan': logical_plan,
            'physical_plan': physical_plan,
        }

    @staticmethod
    def _calculate_performance_score(
        has_broadcast: bool,
        has_shuffle: bool,
        num_shuffles: int,
        filter_pushdown_applied: bool,
        has_cache: bool,
        join_without_broadcast: bool,
        filter_after_join: bool
    ) -> int:
        """
        Calculate performance score from 0-3 stars based on optimizations.

        3 stars: Optimal (broadcast join, filter pushdown, minimal shuffles)
        2 stars: Good (some optimizations applied)
        1 star: Poor (inefficient patterns detected)
        0 stars: Very poor (multiple inefficiencies)
        """
        score = 3  # Start with perfect score

        # Deduct for inefficiencies
        if join_without_broadcast:
            score -= 1  # Not using broadcast for joins

        if num_shuffles > 2:
            score -= 1  # Too many shuffles

        if filter_after_join:
            score -= 1  # Filter not pushed down

        # Bonus for good practices
        if has_broadcast and 'join' in str(join_without_broadcast):
            score = min(3, score + 0.5)  # Bonus for using broadcast

        if filter_pushdown_applied:
            score = min(3, score + 0.5)  # Bonus for filter pushdown

        return max(0, int(score))

    @staticmethod
    def _empty_analysis() -> Dict[str, any]:
        """Return empty analysis when no metadata available"""
        return {
            'operations': [],
            'has_shuffle': False,
            'num_shuffles': 0,
            'has_join': False,
            'has_broadcast': False,
            'has_cache': False,
            'has_groupby': False,
            'has_filter': False,
            'has_aggregation': False,
            'filter_after_join': False,
            'filter_pushdown_applied': False,
            'join_without_broadcast': False,
            'has_reuse_without_cache': False,
            'estimated_stages': 0,
            'performance_score': 0,
            'logical_plan': None,
            'physical_plan': None,
        }

    @staticmethod
    def extract_dag_structure(physical_plan: str) -> Dict[str, any]:
        """
        Extract DAG structure from physical plan for visualization.
        Enhanced to handle various Spark plan formats.

        Returns:
            Dictionary with nodes (operations) and edges (data flow)
        """
        if not physical_plan or not physical_plan.strip():
            return {'nodes': [], 'edges': []}

        nodes = []
        edges = []
        node_id = 0

        # Parse physical plan line by line
        lines = physical_plan.split('\n')
        node_stack = []
        prev_depth = -1

        for line in lines:
            if not line.strip():
                continue

            # Calculate indentation depth
            stripped = line.lstrip()
            indent_chars = len(line) - len(stripped)

            # Normalize indentation (every 2-3 spaces = 1 level)
            depth = indent_chars // 3

            # Extract operation name (remove prefixes like *(1), +-, etc.)
            operation_line = stripped.lstrip('+*-() ').strip()

            if not operation_line:
                continue

            # Extract operation name before parentheses or brackets
            operation = operation_line.split('(')[0].split('[')[0].strip()

            # Extract details from parentheses/brackets
            details = None
            if '(' in operation_line:
                details_start = operation_line.find('(')
                details_end = operation_line.find(')', details_start)
                if details_end > details_start:
                    details = operation_line[details_start+1:details_end]
            elif '[' in operation_line:
                details_start = operation_line.find('[')
                details_end = operation_line.find(']', details_start)
                if details_end > details_start:
                    details = operation_line[details_start+1:details_end]

            # Clean up details for learner-friendly display
            if details:
                details = OperationDetector._clean_details_for_display(details)

            # Create node
            node = {
                'id': node_id,
                'operation': operation,
                'details': details[:50] if details else None,  # Limit details length
                'depth': depth,
                'label': operation
            }
            nodes.append(node)

            # Create edge from parent based on depth
            if depth > 0 and node_stack:
                # Find parent at previous depth level
                for i in range(len(node_stack) - 1, -1, -1):
                    if node_stack[i]['depth'] < depth:
                        parent = node_stack[i]
                        edges.append({
                            'from': parent['id'],
                            'to': node_id
                        })
                        break

                # Clean stack of nodes at same or deeper depth
                node_stack = [n for n in node_stack if n['depth'] < depth]

            # Add current node to stack
            node_stack.append({'id': node_id, 'depth': depth})
            node_id += 1
            prev_depth = depth

        # If we have nodes but no edges, create linear flow
        if len(nodes) > 1 and len(edges) == 0:
            for i in range(len(nodes) - 1):
                edges.append({
                    'from': nodes[i]['id'],
                    'to': nodes[i + 1]['id']
                })

        return {
            'nodes': nodes,
            'edges': edges
        }

    @staticmethod
    def _clean_details_for_display(details: str) -> str:
        """
        Clean up Spark's internal details for learner-friendly display.

        Removes internal attribute IDs and makes details more readable.
        Examples:
        - 'color#152,id#153L,type#154' -> 'Columns: color, id, type'
        - 'type#154 ASC NULLS FIRST' -> 'Sort by: type (ascending)'
        - 'type#154 ASC NULLS FIRST, 4' -> 'Sort by: type (ascending), 4 partitions'
        """
        import re

        if not details:
            return details

        # Remove attribute IDs (e.g., #152, #153L)
        cleaned = re.sub(r'#\d+L?', '', details)

        # Handle column lists (e.g., "color,id,type")
        if ',' in cleaned and 'ASC' not in cleaned and 'DESC' not in cleaned:
            # Split and clean up column names
            columns = [col.strip() for col in cleaned.split(',')]
            # Remove empty strings and deduplicate
            columns = [col for col in columns if col]
            if columns:
                return f"Columns: {', '.join(columns)}"

        # Handle sort operations
        if 'ASC' in cleaned or 'DESC' in cleaned:
            # Extract column and direction
            parts = cleaned.split()
            if len(parts) >= 2:
                column = parts[0].strip()
                direction = 'ascending' if 'ASC' in parts[1] else 'descending'
                result = f"Sort by: {column} ({direction})"

                # Check for partition count
                if ',' in cleaned:
                    try:
                        partition_part = cleaned.split(',')[-1].strip()
                        if partition_part.isdigit():
                            result += f", {partition_part} partitions"
                    except:
                        pass

                return result

        # Clean up common patterns
        cleaned = cleaned.replace('NULLS FIRST', '').replace('NULLS LAST', '')
        cleaned = cleaned.strip().strip(',').strip()

        return cleaned if cleaned else None

    @staticmethod
    def create_simple_dag_from_operations(operations: List[str]) -> Dict[str, any]:
        """
        Create a simple linear DAG when physical plan parsing fails.

        Args:
            operations: List of operation names (e.g., ['filter', 'sort', 'aggregation'])

        Returns:
            Dictionary with nodes and edges in a linear flow
        """
        if not operations:
            return {'nodes': [], 'edges': []}

        nodes = []
        edges = []

        for i, op in enumerate(operations):
            nodes.append({
                'id': i,
                'operation': op.capitalize(),
                'details': None,
                'depth': i,
                'label': op.capitalize()
            })

            if i > 0:
                edges.append({
                    'from': i - 1,
                    'to': i
                })

        return {
            'nodes': nodes,
            'edges': edges
        }
