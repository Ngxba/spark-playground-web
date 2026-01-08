import './ClusterView.css';

/**
 * ClusterView - Visualizes the cluster nodes and task execution
 */
function ClusterView({ nodes, currentState, stages }) {
  if (!nodes || nodes.length === 0) {
    return null;
  }

  const renderCoresWithQueue = (node) => {
    const activeTasks = currentState?.tasksByNode[node.id]?.active || [];
    const completedTaskIds = currentState?.completedTasks?.map(t => t.id) || [];

    // Calculate queued tasks for this node from all stages
    let queuedTasks = [];
    if (stages) {
      stages.forEach(stage => {
        const nodeTasks = stage.tasks.filter(task => task.node_id === node.id);
        nodeTasks.forEach(task => {
          // Task is queued if it's not active and not completed
          if (!activeTasks.some(at => at.id === task.id) && !completedTaskIds.includes(task.id)) {
            queuedTasks.push(task);
          }
        });
      });
    }

    // Render cores
    const cores = [];
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
              <div className="core-task-id">P{task.partition_id}</div>
              <div className="task-spinner" />
            </div>
          )}
        </div>
      );
    }

    // Show queue if there are waiting tasks
    if (queuedTasks.length > 0) {
      return (
        <div className="cores-with-queue">
          <div className="node-cores">{cores}</div>
          <div className="task-queue">
            <div className="queue-label">Queue ({queuedTasks.length} waiting)</div>
            <div className="queue-items">
              {queuedTasks.slice(0, 4).map(task => (
                <div key={task.id} className="queue-item" title={`Partition ${task.partition_id} waiting`}>
                  P{task.partition_id}
                </div>
              ))}
              {queuedTasks.length > 4 && (
                <div className="queue-more">+{queuedTasks.length - 4} more</div>
              )}
            </div>
          </div>
        </div>
      );
    }

    return <div className="node-cores">{cores}</div>;
  };

  return (
    <div className="cluster-view">
      <h4 className="cluster-title">[A3.1] 💻 Cluster: {nodes.length} Worker Nodes</h4>
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

              {renderCoresWithQueue(node)}

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
