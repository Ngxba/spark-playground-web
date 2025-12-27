import { useState, useEffect } from 'react';
import './ExecutionDiagram.css';

/**
 * ExecutionDiagram - Detailed visualization showing:
 * - Partitions within each stage
 * - Executor assignment for each partition/task
 * - Shuffle boundaries and redistribution
 * - Cache indicators
 */
function ExecutionDiagram({
  simulationData,
  currentState,
  selectedStageIndex: externalSelectedStageIndex,
  onStageSelect
}) {
  const [hoveredPartition, setHoveredPartition] = useState(null);
  const [hoveredTask, setHoveredTask] = useState(null);
  const [viewMode, setViewMode] = useState('single'); // 'single' or 'all'

  // Use external stage index if provided, otherwise use internal state
  const [internalStageIndex, setInternalStageIndex] = useState(0);
  const selectedStageIndex = externalSelectedStageIndex !== undefined
    ? externalSelectedStageIndex
    : internalStageIndex;

  const handleStageSelect = (index) => {
    if (onStageSelect) {
      onStageSelect(index);
    } else {
      setInternalStageIndex(index);
    }
  };

  if (!simulationData) return null;

  const { stages, partitions, shuffles, nodes } = simulationData;

  // Keyboard navigation support
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (viewMode !== 'single') return;

      if (e.key === 'ArrowLeft' && selectedStageIndex > 0) {
        e.preventDefault();
        handleStageSelect(selectedStageIndex - 1);
      } else if (e.key === 'ArrowRight' && selectedStageIndex < stages.length - 1) {
        e.preventDefault();
        handleStageSelect(selectedStageIndex + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedStageIndex, viewMode, stages.length, handleStageSelect]);

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
          Each of the {fromPartitions.length} source partitions sends data to ALL{' '}
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

  // Determine which stages to display based on view mode
  const stagesToDisplay = viewMode === 'single'
    ? [stages[selectedStageIndex]]
    : stages;

  return (
    <div className="execution-diagram">
      {/* [A2.1] Diagram Header */}
      <div className="diagram-header">
        <h4>[A2] 📊 Detailed Execution Diagram</h4>
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

      {/* [A2.2] Stage Navigation */}
      <div className="stage-navigation">
        <h5 className="section-title">[A2.2] Stage Navigation</h5>
        {viewMode === 'single' && (
          <div className="keyboard-hint">
            💡 Tip: Use arrow keys ← → to navigate between stages
          </div>
        )}
        <div className="stage-navigation-controls">
          <button
            className="stage-nav-arrow"
            onClick={() => handleStageSelect(Math.max(0, selectedStageIndex - 1))}
            disabled={selectedStageIndex === 0 || viewMode === 'all'}
            title="Previous stage"
          >
            ← Prev
          </button>
          <div className="stage-tabs">
            {stages.map((stage, idx) => (
              <button
                key={stage.id}
                className={`stage-tab ${selectedStageIndex === idx && viewMode === 'single' ? 'stage-tab-active' : ''}`}
                onClick={() => {
                  handleStageSelect(idx);
                  setViewMode('single');
                }}
              >
                <div className="stage-tab-number">Stage {stage.id}</div>
                <div className="stage-tab-name">{stage.name}</div>
              </button>
            ))}
          </div>
          <button
            className="stage-nav-arrow"
            onClick={() => handleStageSelect(Math.min(stages.length - 1, selectedStageIndex + 1))}
            disabled={selectedStageIndex === stages.length - 1 || viewMode === 'all'}
            title="Next stage"
          >
            Next →
          </button>
        </div>
        <button
          className={`view-mode-toggle ${viewMode === 'all' ? 'view-mode-active' : ''}`}
          onClick={() => setViewMode(viewMode === 'single' ? 'all' : 'single')}
          title={viewMode === 'single' ? 'Show all stages' : 'Show single stage'}
        >
          {viewMode === 'single' ? '📋 View All Stages' : '🔍 View Single Stage'}
        </button>
      </div>

      {/* [A2.3] Stages Diagram */}
      <div className="stages-diagram">
        <h5 className="section-title">[A2.3] Stages & Partitions</h5>
        {stagesToDisplay.map((stage, idx) => {
          // Get the actual index in the full stages array
          const actualIdx = viewMode === 'single' ? selectedStageIndex : idx;
          const stageParts = partitionsByStage[stage.id] || [];
          const nextStage = stages[actualIdx + 1];
          const shuffle = nextStage ? getShuffleBetween(stage.id, nextStage.id) : null;

          return (
            <div key={stage.id} className="stage-section">
              {/* Stage Header */}
              <div className="stage-diagram-header">
                <div className="stage-header-main">
                  <div className="stage-title-section">
                    <span className="stage-number">Stage {stage.id}</span>
                    <div className="stage-title-right">
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
                  </div>
                  <div className="stage-stats">
                    <div className="stat-card">
                      <span className="stat-icon">📦</span>
                      <div className="stat-content">
                        <span className="stat-value">{stageParts.length}</span>
                        <span className="stat-label">Partitions</span>
                      </div>
                    </div>
                    <div className="stat-card">
                      <span className="stat-icon">⚙️</span>
                      <div className="stat-content">
                        <span className="stat-value">{stage.tasks.length}</span>
                        <span className="stat-label">Tasks</span>
                      </div>
                    </div>
                    <div className="stat-card">
                      <span className="stat-icon">⚡</span>
                      <div className="stat-content">
                        <span className="stat-value">{stage.parallelism}</span>
                        <span className="stat-label">Parallel</span>
                      </div>
                    </div>
                  </div>
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

      {/* [A2.4] Executor Summary */}
      <div className="executor-summary">
        <h5>[A2.4] 💻 Executor Summary {viewMode === 'single' && `- Stage ${stages[selectedStageIndex].id}`}</h5>
        <div className="executor-grid">
          {nodes.map(node => {
            // Filter tasks by selected stage(s)
            const relevantStageIds = viewMode === 'single'
              ? [stages[selectedStageIndex].id]
              : stages.map(s => s.id);

            // Get tasks for this node from the selected stage(s)
            let activeTasks = [];
            let completedCount = 0;

            if (currentState?.tasksByNode?.[node.id]) {
              const nodeTasks = currentState.tasksByNode[node.id];
              activeTasks = nodeTasks.active.filter(task => {
                // Find which stage this task belongs to
                const taskStage = stages.find(s => s.tasks.some(t => t.id === task.id));
                return taskStage && relevantStageIds.includes(taskStage.id);
              });

              // For completed count, count tasks from selected stage(s)
              relevantStageIds.forEach(stageId => {
                const stage = stages.find(s => s.id === stageId);
                if (stage) {
                  const nodeTasksInStage = stage.tasks.filter(t =>
                    t.node_id === node.id &&
                    currentState.completedTasks?.some(ct => ct.id === t.id)
                  );
                  completedCount += nodeTasksInStage.length;
                }
              });
            }

            return (
              <div key={node.id} className="executor-card">
                <div className="executor-header">
                  <span className="executor-name">{node.name}</span>
                  <span className="executor-cores">{node.cores} cores</span>
                </div>
                <div className="executor-stats">
                  <div className="executor-stat">
                    <span>⚡ Active:</span>
                    <span>{activeTasks.length}</span>
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
                {activeTasks.length > 0 && (
                  <div className="executor-active-tasks">
                    <strong>Processing:</strong>
                    {activeTasks.slice(0, 3).map(task => (
                      <span key={task.id} className="active-task-badge">
                        P{task.partition_id}
                      </span>
                    ))}
                    {activeTasks.length > 3 && (
                      <span className="more-tasks">+{activeTasks.length - 3} more</span>
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
