import { useState, useEffect } from 'react';
import './ExecutionDiagram.css';

/**
 * ExecutionDiagram - FULLY REDESIGNED
 * Circuit Board Aesthetic for Stages & Partitions
 */
function ExecutionDiagram({
  simulationData,
  currentState,
  selectedStageIndex: externalSelectedStageIndex,
  onStageSelect
}) {
  const [hoveredPartition, setHoveredPartition] = useState(null);
  const [viewMode, setViewMode] = useState('flow'); // 'flow' or 'detailed'

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

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
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
  }, [selectedStageIndex, stages.length]);

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

  // Get executor for a task
  const getExecutorForTask = (task) => {
    if (!task) return null;
    return nodes.find(n => n.id === task.node_id);
  };

  // Check task status
  const isTaskActive = (task) => {
    if (!currentState || !task) return false;
    return currentState.activeTasks?.some(t => t.id === task.id);
  };

  const isTaskCompleted = (task) => {
    if (!currentState || !task) return false;
    return currentState.completedTasks?.some(t => t.id === task.id);
  };

  // Get shuffle between stages
  const getShuffleBetween = (fromStageId, toStageId) => {
    return shuffles?.find(s => s.from_stage_id === fromStageId && s.to_stage_id === toStageId);
  };

  // Render a partition chip (new design)
  const renderPartitionChip = (partition, stage) => {
    const task = getTaskForPartition(partition.id);
    const executor = getExecutorForTask(task);
    const isActive = isTaskActive(task);
    const isCompleted = isTaskCompleted(task);
    const isHovered = hoveredPartition === partition.id;

    let statusClass = 'chip-pending';
    if (isCompleted) statusClass = 'chip-completed';
    else if (isActive) statusClass = 'chip-running';

    return (
      <div
        key={partition.id}
        className={`partition-chip ${statusClass} ${isHovered ? 'chip-hovered' : ''}`}
        onMouseEnter={() => setHoveredPartition(partition.id)}
        onMouseLeave={() => setHoveredPartition(null)}
        title={`Partition ${partition.id} - ${partition.size_mb}MB - ${partition.records_count} records`}
      >
        <div className="chip-core">
          <div className="chip-id">P{partition.id}</div>
          <div className="chip-pulse"></div>
        </div>

        {isHovered && (
          <div className="chip-tooltip">
            <div className="tooltip-header">
              <span className="tooltip-title">Partition {partition.id}</span>
              <span className={`tooltip-status status-${statusClass.replace('chip-', '')}`}>
                {isCompleted ? 'DONE' : isActive ? 'RUN' : 'WAIT'}
              </span>
            </div>
            <div className="tooltip-content">
              <div className="tooltip-row">
                <span className="tooltip-label">Size</span>
                <span className="tooltip-value">{partition.size_mb} MB</span>
              </div>
              <div className="tooltip-row">
                <span className="tooltip-label">Records</span>
                <span className="tooltip-value">{partition.records_count.toLocaleString()}</span>
              </div>
              {executor && (
                <>
                  <div className="tooltip-divider"></div>
                  <div className="tooltip-row">
                    <span className="tooltip-label">Executor</span>
                    <span className="tooltip-value">{executor.name}</span>
                  </div>
                  <div className="tooltip-row">
                    <span className="tooltip-label">Core</span>
                    <span className="tooltip-value">#{task.core_id}</span>
                  </div>
                </>
              )}
              {partition.parent_partitions.length > 0 && (
                <>
                  <div className="tooltip-divider"></div>
                  <div className="tooltip-lineage">
                    <span className="lineage-label">← FROM</span>
                    <span className="lineage-values">
                      {partition.parent_partitions.slice(0, 5).map(id => `P${id}`).join(', ')}
                      {partition.parent_partitions.length > 5 && ` +${partition.parent_partitions.length - 5}`}
                    </span>
                  </div>
                </>
              )}
              {partition.child_partitions.length > 0 && (
                <div className="tooltip-lineage">
                  <span className="lineage-label">→ TO</span>
                  <span className="lineage-values">
                    {partition.child_partitions.slice(0, 5).map(id => `P${id}`).join(', ')}
                    {partition.child_partitions.length > 5 && ` +${partition.child_partitions.length - 5}`}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render shuffle connector (new design)
  const renderShuffleConnector = (shuffle, fromStage, toStage) => {
    if (!shuffle) return null;

    const fromPartitions = partitionsByStage[shuffle.from_stage_id] || [];
    const toPartitions = partitionsByStage[shuffle.to_stage_id] || [];

    return (
      <div className="shuffle-connector">
        <div className="shuffle-bar">
          <div className="shuffle-indicator">
            <div className="shuffle-icon">⚡</div>
            <div className="shuffle-label">SHUFFLE</div>
          </div>
          <div className="shuffle-stats">
            <div className="shuffle-stat">
              <span className="stat-num">{shuffle.data_volume_mb.toFixed(1)}</span>
              <span className="stat-unit">MB</span>
            </div>
            <div className="shuffle-arrow">→</div>
            <div className="shuffle-stat">
              <span className="stat-num">{fromPartitions.length}</span>
              <span className="stat-unit">to</span>
              <span className="stat-num">{toPartitions.length}</span>
            </div>
          </div>
        </div>
        <div className="shuffle-flow-lines">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flow-line" style={{ animationDelay: `${i * 0.2}s` }}></div>
          ))}
        </div>
      </div>
    );
  };

  // Render narrow dependency connector
  const renderNarrowConnector = () => {
    return (
      <div className="narrow-connector">
        <div className="narrow-line"></div>
        <div className="narrow-label">Direct Flow</div>
      </div>
    );
  };

  // Render stage card (new design)
  const renderStageCard = (stage, stageIndex) => {
    const stageParts = partitionsByStage[stage.id] || [];
    const nextStage = stages[stageIndex + 1];
    const shuffle = nextStage ? getShuffleBetween(stage.id, nextStage.id) : null;

    const isSelected = selectedStageIndex === stageIndex;
    const isActive = currentState?.activeStages?.includes(stage.id);
    const isCached = stage.name.toLowerCase().includes('inmemory') ||
                     stage.name.toLowerCase().includes('cache');

    // Calculate completion
    const completedCount = stageParts.filter(p => {
      const task = getTaskForPartition(p.id);
      return isTaskCompleted(task);
    }).length;
    const completionPercent = stageParts.length > 0 ? (completedCount / stageParts.length) * 100 : 0;

    return (
      <div key={stage.id} className="stage-wrapper">
        <div
          className={`stage-card ${isSelected ? 'stage-selected' : ''} ${isActive ? 'stage-active' : ''}`}
          onClick={() => handleStageSelect(stageIndex)}
        >
          {/* Stage Header */}
          <div className="stage-card-header">
            <div className="stage-id-badge">
              <span className="badge-label">STAGE</span>
              <span className="badge-number">{stage.id}</span>
            </div>

            <div className="stage-info">
              <div className="stage-name">{stage.name}</div>
              <div className="stage-meta">
                <span className="meta-tag">{stage.operation_type}</span>
                {isCached && (
                  <span className="meta-tag tag-cache">CACHED</span>
                )}
              </div>
            </div>

            <div className="stage-progress">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${completionPercent}%` }}
                ></div>
              </div>
              <div className="progress-text">
                {completedCount}/{stageParts.length}
              </div>
            </div>
          </div>

          {/* Stage Metrics */}
          <div className="stage-metrics">
            <div className="metric-item">
              <div className="metric-icon">□</div>
              <div className="metric-content">
                <div className="metric-value">{stageParts.length}</div>
                <div className="metric-label">Partitions</div>
              </div>
            </div>
            <div className="metric-item">
              <div className="metric-icon">▣</div>
              <div className="metric-content">
                <div className="metric-value">{stage.tasks.length}</div>
                <div className="metric-label">Tasks</div>
              </div>
            </div>
            <div className="metric-item">
              <div className="metric-icon">∥</div>
              <div className="metric-content">
                <div className="metric-value">{stage.parallelism}</div>
                <div className="metric-label">Parallel</div>
              </div>
            </div>
          </div>

          {/* Partition Chips Flow */}
          <div className="partition-flow">
            <div className="flow-track">
              {stageParts.map(partition => renderPartitionChip(partition, stage))}
            </div>
          </div>
        </div>

        {/* Connector to next stage */}
        {nextStage && (
          shuffle ? renderShuffleConnector(shuffle, stage, nextStage) : renderNarrowConnector()
        )}
      </div>
    );
  };

  return (
    <div className="execution-diagram">
      {/* Diagram Header */}
      <div className="diagram-control-bar">
        <div className="control-left">
          <div className="diagram-title">
            <span className="title-accent">⚡</span>
            <span className="title-text">EXECUTION FLOW</span>
          </div>
          <div className="diagram-subtitle">
            Stage-by-stage partition processing
          </div>
        </div>

        <div className="control-right">
          <div className="view-mode-switch">
            <button
              className={`mode-btn ${viewMode === 'flow' ? 'mode-active' : ''}`}
              onClick={() => setViewMode('flow')}
            >
              Flow View
            </button>
            <button
              className={`mode-btn ${viewMode === 'detailed' ? 'mode-active' : ''}`}
              onClick={() => setViewMode('detailed')}
            >
              Detailed
            </button>
          </div>

          <div className="legend-compact">
            <div className="legend-item">
              <div className="legend-dot dot-pending"></div>
              <span>Pending</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot dot-running"></div>
              <span>Running</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot dot-completed"></div>
              <span>Done</span>
            </div>
          </div>
        </div>
      </div>

      {/* Stage Navigation Pills */}
      <div className="stage-nav-pills">
        {stages.map((stage, idx) => (
          <button
            key={stage.id}
            className={`nav-pill ${selectedStageIndex === idx ? 'pill-active' : ''}`}
            onClick={() => handleStageSelect(idx)}
          >
            <span className="pill-num">{stage.id}</span>
            <span className="pill-name">{stage.operation_type}</span>
          </button>
        ))}
      </div>

      {/* Stages Flow */}
      <div className="stages-flow">
        {viewMode === 'flow' ? (
          // Show all stages in flow
          <div className="flow-container">
            {stages.map((stage, idx) => renderStageCard(stage, idx))}
          </div>
        ) : (
          // Show single selected stage in detail
          <div className="detailed-container">
            {renderStageCard(stages[selectedStageIndex], selectedStageIndex)}

            {/* Executor Summary for selected stage */}
            <div className="executor-panel">
              <div className="panel-header">
                <span className="panel-icon">▦</span>
                <span className="panel-title">EXECUTOR ALLOCATION</span>
              </div>
              <div className="executor-grid">
                {nodes.map(node => {
                  const stageTasks = stages[selectedStageIndex].tasks.filter(t => t.node_id === node.id);
                  const activeTasks = stageTasks.filter(t => currentState?.activeTasks?.some(at => at.id === t.id));
                  const completedTasks = stageTasks.filter(t => currentState?.completedTasks?.some(ct => ct.id === t.id));

                  return (
                    <div key={node.id} className="executor-box">
                      <div className="executor-header">
                        <span className="executor-name">{node.name}</span>
                        <span className="executor-cores">{node.cores} cores</span>
                      </div>
                      <div className="executor-stats">
                        <div className="executor-stat">
                          <span className="stat-label">Active</span>
                          <span className="stat-value stat-active">{activeTasks.length}</span>
                        </div>
                        <div className="executor-stat">
                          <span className="stat-label">Done</span>
                          <span className="stat-value stat-done">{completedTasks.length}</span>
                        </div>
                        <div className="executor-stat">
                          <span className="stat-label">Total</span>
                          <span className="stat-value">{stageTasks.length}</span>
                        </div>
                      </div>
                      {activeTasks.length > 0 && (
                        <div className="executor-active">
                          {activeTasks.slice(0, 3).map(t => (
                            <span key={t.id} className="active-badge">P{t.partition_id}</span>
                          ))}
                          {activeTasks.length > 3 && (
                            <span className="active-more">+{activeTasks.length - 3}</span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Keyboard hint */}
      <div className="keyboard-hint">
        Use ← → arrow keys to navigate stages
      </div>
    </div>
  );
}

export default ExecutionDiagram;
