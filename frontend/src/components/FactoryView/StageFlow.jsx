import './StageFlow.css';

/**
 * StageFlow - Visualizes execution stages and their progress
 */
function StageFlow({ stages, shuffles, currentState }) {
  if (!stages || stages.length === 0) {
    return null;
  }

  const getStageStatus = (stage) => {
    if (!currentState) return 'pending';

    if (currentState.activeStages.includes(stage.id)) {
      return 'running';
    }

    // Check if stage has started
    const stageEndTime = stage.end_time;
    if (currentState.time >= stageEndTime) {
      return 'completed';
    }

    if (currentState.time >= stage.start_time) {
      return 'running';
    }

    return 'pending';
  };

  const getStageProgress = (stage) => {
    if (!currentState) return 0;

    const status = getStageStatus(stage);
    if (status === 'completed') return 100;
    if (status === 'pending') return 0;

    // Calculate based on completed tasks in this stage
    const completedInStage = stage.tasks.filter(task =>
      currentState.completedTasks.some(t => t.id === task.id)
    ).length;

    return (completedInStage / stage.tasks.length) * 100;
  };

  const getOperationIcon = (operationType) => {
    const icons = {
      scan: '📁',
      filter: '🔍',
      join: '🔗',
      aggregate: '📊',
      shuffle: '🔀',
      process: '⚙️',
    };
    return icons[operationType] || '⚙️';
  };

  const getOperationColor = (operationType) => {
    const colors = {
      scan: '#3b82f6',      // Blue
      filter: '#10b981',    // Green
      join: '#f59e0b',      // Orange
      aggregate: '#eab308', // Yellow
      shuffle: '#ef4444',   // Red
      process: '#6b7280',   // Gray
    };
    return colors[operationType] || '#6b7280';
  };

  return (
    <div className="stage-flow">
      <h4 className="stage-flow-title">Execution Pipeline: {stages.length} Stages</h4>
      <div className="stages-container">
        {stages.map((stage, idx) => {
          const status = getStageStatus(stage);
          const progress = getStageProgress(stage);
          const icon = getOperationIcon(stage.operation_type);
          const color = getOperationColor(stage.operation_type);

          // Check for shuffle after this stage
          const shuffleAfter = shuffles?.find(s => s.from_stage_id === stage.id);

          return (
            <div key={stage.id} className="stage-container">
              <div className={`stage stage-${status}`}>
                <div className="stage-header" style={{ borderColor: color }}>
                  <span className="stage-icon">{icon}</span>
                  <div className="stage-info">
                    <div className="stage-name">{stage.name}</div>
                    <div className="stage-meta">
                      Stage {stage.id} • {stage.tasks.length} tasks • {stage.parallelism} parallel
                    </div>
                  </div>
                  <div className="stage-status-badge">
                    {status === 'completed' && '✓'}
                    {status === 'running' && '▶'}
                    {status === 'pending' && '○'}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="stage-progress-container">
                  <div
                    className="stage-progress-bar"
                    style={{
                      width: `${progress}%`,
                      backgroundColor: color
                    }}
                  />
                </div>

                {/* Task Count */}
                <div className="stage-tasks">
                  {status === 'running' && currentState && (
                    <span className="tasks-active">
                      {stage.tasks.filter(t =>
                        currentState.activeTasks.some(at => at.id === t.id)
                      ).length} running
                    </span>
                  )}
                  {status === 'completed' && (
                    <span className="tasks-completed">
                      {stage.tasks.length} completed
                    </span>
                  )}
                </div>
              </div>

              {/* Shuffle Indicator */}
              {shuffleAfter && idx < stages.length - 1 && (
                <div className="shuffle-connector">
                  <div className="shuffle-icon" title={`Shuffle: ${shuffleAfter.data_volume_mb.toFixed(1)} MB`}>
                    <span>🔀</span>
                    <span className="shuffle-label">
                      {shuffleAfter.data_volume_mb.toFixed(1)} MB
                    </span>
                  </div>
                  <div className="connector-line" />
                </div>
              )}

              {/* Regular Connector */}
              {!shuffleAfter && idx < stages.length - 1 && (
                <div className="stage-connector">
                  <div className="connector-arrow">→</div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default StageFlow;
