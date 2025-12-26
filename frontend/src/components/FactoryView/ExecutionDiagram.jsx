import { useState } from 'react';
import './ExecutionDiagram.css';

/**
 * ExecutionDiagram - Detailed visualization showing:
 * - Partitions within each stage
 * - Executor assignment for each partition/task
 * - Shuffle boundaries and redistribution
 * - Cache indicators
 */
function ExecutionDiagram({ simulationData, currentState }) {
  const [hoveredPartition, setHoveredPartition] = useState(null);
  const [hoveredTask, setHoveredTask] = useState(null);

  if (!simulationData) return null;

  const { stages, partitions, shuffles, nodes } = simulationData;

  // Group partitions by stage
  const partitionsByStage = {};
  partitions.forEach(partition => {
    if (!partitionsByStage[partition.stage_id]) {
      partitionsByStage[partition.stage_id] = [];
    }
    partitionsByStage[partition.stage_id].push(partition);
  });

  // Get task for a partition
  const getTaskForPartition = (partitionId) => {
    for (const stage of stages) {
      const task = stage.tasks.find(t => t.partition_id === partitionId);
      if (task) return task;
    }
    return null;
  };

  // Get executor (node) for a task
  const getExecutorForTask = (task) => {
    if (!task) return null;
    return nodes.find(n => n.id === task.node_id);
  };

  // Check if task is currently active
  const isTaskActive = (task) => {
    if (!currentState || !task) return false;
    return currentState.activeTasks?.some(t => t.id === task.id);
  };

  // Check if task is completed
  const isTaskCompleted = (task) => {
    if (!currentState || !task) return false;
    return currentState.completedTasks?.some(t => t.id === task.id);
  };

  // Get shuffle between stages
  const getShuffleBetween = (fromStageId, toStageId) => {
    return shuffles?.find(s => s.from_stage_id === fromStageId && s.to_stage_id === toStageId);
  };

  // Render a partition box
  const renderPartition = (partition, stage) => {
    const task = getTaskForPartition(partition.id);
    const executor = getExecutorForTask(task);
    const isActive = isTaskActive(task);
    const isCompleted = isTaskCompleted(task);
    const isHovered = hoveredPartition === partition.id;

    let status = 'pending';
    if (isCompleted) status = 'completed';
    else if (isActive) status = 'active';

    return (
      <div
        key={partition.id}
        className={`partition-box partition-${status} ${isHovered ? 'partition-hovered' : ''}`}
        onMouseEnter={() => setHoveredPartition(partition.id)}
        onMouseLeave={() => setHoveredPartition(null)}
      >
        <div className="partition-header">
          <span className="partition-id">P{partition.id}</span>
          {isActive && <span className="partition-indicator">⚡</span>}
          {isCompleted && <span className="partition-indicator">✓</span>}
        </div>
        <div className="partition-info">
          <div className="partition-detail">
            <span className="detail-label">Size:</span>
            <span className="detail-value">{partition.size_mb}MB</span>
          </div>
          <div className="partition-detail">
            <span className="detail-label">Records:</span>
            <span className="detail-value">{partition.records_count}</span>
          </div>
          {executor && (
            <div className="partition-executor">
              <span className="executor-label">📍 Executor:</span>
              <span className="executor-name">{executor.name}</span>
              <span className="executor-core">Core {task.core_id}</span>
            </div>
          )}
        </div>

        {/* Show parent/child connections on hover */}
        {isHovered && (
          <div className="partition-lineage">
            {partition.parent_partitions.length > 0 && (
              <div className="lineage-info">
                <span className="lineage-label">← Parents:</span>
                <span className="lineage-ids">
                  {partition.parent_partitions.map(id => `P${id}`).join(', ')}
                </span>
              </div>
            )}
            {partition.child_partitions.length > 0 && (
              <div className="lineage-info">
                <span className="lineage-label">→ Children:</span>
                <span className="lineage-ids">
                  {partition.child_partitions.map(id => `P${id}`).join(', ')}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // Render shuffle info between stages
  const renderShuffle = (shuffle) => {
    if (!shuffle) return null;

    const fromPartitions = partitionsByStage[shuffle.from_stage_id] || [];
    const toPartitions = partitionsByStage[shuffle.to_stage_id] || [];

    return (
      <div className="shuffle-boundary">
        <div className="shuffle-header">
          <span className="shuffle-icon">🔀</span>
          <span className="shuffle-title">SHUFFLE BOUNDARY</span>
        </div>
        <div className="shuffle-details">
          <div className="shuffle-stat">
            <span className="stat-label">Data Volume:</span>
            <span className="stat-value">{shuffle.data_volume_mb.toFixed(1)} MB</span>
          </div>
          <div className="shuffle-stat">
            <span className="stat-label">Redistribution:</span>
            <span className="stat-value">
              {shuffle.from_partitions} → {shuffle.to_partitions} partitions
            </span>
          </div>
          <div className="shuffle-stat">
            <span className="stat-label">Network:</span>
            <span className="stat-value">All-to-All</span>
          </div>
        </div>
        <div className="shuffle-explanation">
          <strong>Why shuffle?</strong> Data needs to be redistributed across partitions.
          Each of the {fromPartitions.length} source partitions sends data to ALL
          {toPartitions.length} destination partitions over the network.
        </div>

        {/* Visual representation of shuffle pattern */}
        <div className="shuffle-pattern">
          <div className="pattern-source">
            {fromPartitions.slice(0, 3).map(p => (
              <div key={p.id} className="pattern-box">P{p.id}</div>
            ))}
            {fromPartitions.length > 3 && <div className="pattern-more">+{fromPartitions.length - 3}</div>}
          </div>
          <div className="pattern-arrows">
            <div className="crossing-arrows">
              <div className="arrow-line" />
              <div className="arrow-line" />
              <div className="arrow-line" />
            </div>
          </div>
          <div className="pattern-dest">
            {toPartitions.slice(0, 3).map(p => (
              <div key={p.id} className="pattern-box">P{p.id}</div>
            ))}
            {toPartitions.length > 3 && <div className="pattern-more">+{toPartitions.length - 3}</div>}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="execution-diagram">
      <div className="diagram-header">
        <h4>📊 Detailed Execution Diagram</h4>
        <div className="diagram-legend">
          <span className="legend-item">
            <span className="legend-box legend-pending"></span> Pending
          </span>
          <span className="legend-item">
            <span className="legend-box legend-active"></span> Running
          </span>
          <span className="legend-item">
            <span className="legend-box legend-completed"></span> Completed
          </span>
        </div>
      </div>

      <div className="stages-diagram">
        {stages.map((stage, idx) => {
          const stageParts = partitionsByStage[stage.id] || [];
          const nextStage = stages[idx + 1];
          const shuffle = nextStage ? getShuffleBetween(stage.id, nextStage.id) : null;

          return (
            <div key={stage.id} className="stage-section">
              {/* Stage Header */}
              <div className="stage-diagram-header">
                <div className="stage-info">
                  <span className="stage-number">Stage {stage.id}</span>
                  <span className="stage-name">{stage.name}</span>
                  <span className="stage-op-type">{stage.operation_type}</span>
                  {/* Cache indicator - check if stage name mentions InMemoryRelation or cache */}
                  {(stage.name.toLowerCase().includes('inmemory') ||
                    stage.name.toLowerCase().includes('cache')) && (
                    <span className="cache-badge" title="Data is cached in memory">
                      💾 CACHED
                    </span>
                  )}
                </div>
                <div className="stage-stats">
                  <span className="stat-item">
                    📦 {stageParts.length} partitions
                  </span>
                  <span className="stat-item">
                    ⚙️ {stage.tasks.length} tasks
                  </span>
                  <span className="stat-item">
                    ⚡ {stage.parallelism} parallel
                  </span>
                </div>
              </div>

              {/* Partitions Grid */}
              <div className="partitions-grid">
                {stageParts.map(partition => renderPartition(partition, stage))}
              </div>

              {/* Shuffle Boundary */}
              {shuffle && renderShuffle(shuffle)}

              {/* Simple connector for non-shuffle */}
              {!shuffle && nextStage && (
                <div className="narrow-dependency">
                  <div className="narrow-arrow">↓</div>
                  <div className="narrow-label">Narrow Dependency (No Shuffle)</div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Executor Summary */}
      <div className="executor-summary">
        <h5>💻 Executor Summary</h5>
        <div className="executor-grid">
          {nodes.map(node => {
            const nodeTasks = currentState?.tasksByNode?.[node.id] || { active: [], completed: 0 };
            const activeCount = nodeTasks.active.length;
            const completedCount = nodeTasks.completed;

            return (
              <div key={node.id} className="executor-card">
                <div className="executor-header">
                  <span className="executor-name">{node.name}</span>
                  <span className="executor-cores">{node.cores} cores</span>
                </div>
                <div className="executor-stats">
                  <div className="executor-stat">
                    <span>⚡ Active:</span>
                    <span>{activeCount}</span>
                  </div>
                  <div className="executor-stat">
                    <span>✓ Completed:</span>
                    <span>{completedCount}</span>
                  </div>
                  <div className="executor-stat">
                    <span>💾 Memory:</span>
                    <span>{node.memory_gb}GB</span>
                  </div>
                </div>
                {nodeTasks.active.length > 0 && (
                  <div className="executor-active-tasks">
                    <strong>Processing:</strong>
                    {nodeTasks.active.slice(0, 3).map(task => (
                      <span key={task.id} className="active-task-badge">
                        P{task.partition_id}
                      </span>
                    ))}
                    {nodeTasks.active.length > 3 && (
                      <span className="more-tasks">+{nodeTasks.active.length - 3} more</span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default ExecutionDiagram;
