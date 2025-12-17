import './ClusterView.css';

/**
 * ClusterView - Visualizes the cluster nodes and task execution
 */
function ClusterView({ nodes, currentState }) {
  if (!nodes || nodes.length === 0) {
    return null;
  }

  const renderCores = (node) => {
    const cores = [];
    const activeTasks = currentState?.tasksByNode[node.id]?.active || [];

    for (let i = 0; i < node.cores; i++) {
      const task = activeTasks[i];
      const isActive = !!task;

      cores.push(
        <div
          key={i}
          className={`core ${isActive ? 'core-active' : 'core-idle'}`}
          title={isActive ? `Running Task ${task.id} (Partition ${task.partition_id})` : 'Idle'}
        >
          {isActive && (
            <div className="core-task-indicator">
              <div className="task-spinner" />
            </div>
          )}
        </div>
      );
    }

    return cores;
  };

  return (
    <div className="cluster-view">
      <h4 className="cluster-title">Cluster: {nodes.length} Worker Nodes</h4>
      <div className="nodes-container">
        {nodes.map(node => {
          const nodeStats = currentState?.tasksByNode[node.id] || { active: [], completed: 0 };
          const isActive = nodeStats.active.length > 0;

          return (
            <div key={node.id} className={`node ${isActive ? 'node-active' : 'node-idle'}`}>
              <div className="node-header">
                <span className="node-name">{node.name}</span>
                <span className="node-status">
                  {nodeStats.active.length}/{node.cores} cores
                </span>
              </div>

              <div className="node-cores">
                {renderCores(node)}
              </div>

              <div className="node-stats">
                <div className="stat">
                  <span className="stat-label">Memory:</span>
                  <span className="stat-value">{node.memory_gb}GB</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Completed:</span>
                  <span className="stat-value">{nodeStats.completed}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ClusterView;
