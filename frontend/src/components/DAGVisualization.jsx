import { useMemo, memo } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  Handle,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import './DAGVisualization.css';

// Custom node component with handles
function OperationNode({ data }) {
  const getNodeStyle = () => {
    const operation = data.operation?.toLowerCase() || '';

    if (operation.includes('broadcast')) {
      return 'dag-node broadcast';
    } else if (operation.includes('exchange') || operation.includes('shuffle')) {
      return 'dag-node shuffle';
    } else if (operation.includes('filter') || operation.includes('project')) {
      return 'dag-node filter';
    } else if (operation.includes('aggregate') || operation.includes('join')) {
      return 'dag-node aggregate';
    }
    return 'dag-node default';
  };

  return (
    <div className={getNodeStyle()}>
      <Handle type="target" position={Position.Left} />
      <div className="node-header">{data.operation || 'Operation'}</div>
      {data.details && <div className="node-details">{data.details}</div>}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

const nodeTypes = {
  operation: OperationNode,
};

function DAGVisualization({ nodes, edges }) {
  // Debug logging at component entry
  console.log('=== DAGVisualization CALLED ===');
  console.log('Received nodes:', nodes);
  console.log('Received edges:', edges);

  // Convert nodes to ReactFlow format with hierarchical layout (memoized)
  const convertedNodes = useMemo(() => {
    console.log('Converting nodes to ReactFlow format');

    // Group nodes by depth for better layout
    const nodesByDepth = {};
    nodes.forEach(node => {
      const depth = node.depth || 0;
      if (!nodesByDepth[depth]) {
        nodesByDepth[depth] = [];
      }
      nodesByDepth[depth].push(node);
    });

    // Calculate positions in a left-to-right hierarchical layout (like Airflow)
    // First pass: determine max depth for centering
    const maxDepth = Math.max(...nodes.map(n => n.depth || 0));

    return nodes.map((node) => {
      const depth = node.depth || 0;
      const nodesAtDepth = nodesByDepth[depth];
      const indexAtDepth = nodesAtDepth.indexOf(node);
      const totalAtDepth = nodesAtDepth.length;

      // Horizontal position: evenly space across available width
      // Use larger spacing for better readability
      const horizontalSpacing = 350;
      const x = 50 + depth * horizontalSpacing;

      // Vertical position: center nodes at same depth
      const verticalSpacing = 150;
      const canvasHeight = 400; // Approximate canvas height

      // Calculate starting Y to center the group of nodes at this depth
      const groupHeight = (totalAtDepth - 1) * verticalSpacing;
      const startY = (canvasHeight - groupHeight) / 2;
      const y = startY + indexAtDepth * verticalSpacing;

      return {
        id: String(node.id),
        type: 'operation',
        position: { x, y },
        data: {
          operation: node.operation || 'Unknown',
          details: node.details || '',
        },
      };
    });
  }, [nodes]);

  // Convert edges to ReactFlow format (memoized)
  const convertedEdges = useMemo(() => {
    console.log('Converting edges to ReactFlow format');

    // Create a set of valid node IDs for validation
    const validNodeIds = new Set(nodes.map(n => String(n.id)));

    // Filter and convert edges, only including those with valid source/target
    return edges
      .filter(edge => {
        const sourceId = String(edge.from);
        const targetId = String(edge.to);
        const isValid = validNodeIds.has(sourceId) && validNodeIds.has(targetId);

        if (!isValid) {
          console.warn(`Skipping invalid edge: ${sourceId} -> ${targetId}`);
        }

        return isValid;
      })
      .map((edge, i) => ({
        id: `e${edge.from}-${edge.to}-${i}`,
        source: String(edge.from),
        target: String(edge.to),
        type: 'default',
        animated: false,
        style: { stroke: '#667eea', strokeWidth: 2 },
        markerEnd: {
          type: 'arrowclosed',
          color: '#667eea',
        },
      }));
  }, [nodes, edges]);

  // No need for state hooks since we want a static, non-interactive display

  if (!nodes || nodes.length === 0) {
    console.warn('DAGVisualization: No nodes provided', { nodes, edges });
    return (
      <div className="dag-empty">
        <div className="empty-icon">📊</div>
        <p><strong>No DAG data available</strong></p>
        <p className="empty-hint">
          The query execution plan doesn't contain enough information to visualize.
          Try running a more complex query (e.g., with joins or aggregations).
        </p>
        <details>
          <summary>Debug Info</summary>
          <pre>{JSON.stringify({ nodes, edges }, null, 2)}</pre>
        </details>
      </div>
    );
  }

  console.log('About to render ReactFlow component');

  return (
    <div className="dag-visualization-container">
      <div style={{ height: '100%', width: '100%' }}>
        <ReactFlow
          nodes={convertedNodes}
          edges={convertedEdges}
          nodeTypes={nodeTypes}
          nodesDraggable={false}
          nodesConnectable={false}
          nodesFocusable={false}
          edgesFocusable={false}
          elementsSelectable={false}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          attributionPosition="bottom-right"
        >
        <Controls />
        <MiniMap
          nodeStrokeColor={(n) => {
            const operation = n.data.operation?.toLowerCase() || '';
            if (operation.includes('broadcast')) return '#28a745';
            if (operation.includes('shuffle')) return '#ffc107';
            if (operation.includes('filter')) return '#17a2b8';
            return '#667eea';
          }}
          nodeColor={(n) => {
            const operation = n.data.operation?.toLowerCase() || '';
            if (operation.includes('broadcast')) return '#d4edda';
            if (operation.includes('shuffle')) return '#fff3cd';
            if (operation.includes('filter')) return '#d1ecf1';
            return '#e8eaff';
          }}
          nodeBorderRadius={6}
        />
        <Background color="#aaa" gap={16} />
      </ReactFlow>
      </div>
    </div>
  );
}

// Memoize the component to prevent unnecessary re-renders
export default memo(DAGVisualization);
