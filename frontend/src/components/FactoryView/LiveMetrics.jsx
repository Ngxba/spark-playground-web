import './LiveMetrics.css';

/**
 * LiveMetrics - Shows live execution metrics
 */
function LiveMetrics({ currentState, metrics, partitionCount }) {
  if (!currentState || !metrics) {
    return null;
  }

  const activeTasks = currentState.totalActive || 0;
  const completedTasks = currentState.totalCompleted || 0;
  const totalTasks = metrics.total_tasks || 0;
  const activeShuffles = currentState.activeShuffles?.length || 0;
  const currentStage = currentState.activeStages?.[0];

  return (
    <div className="live-metrics">
      <h4 className="metrics-title">Live Metrics</h4>
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon">⚡</div>
          <div className="metric-content">
            <div className="metric-label">Active Tasks</div>
            <div className="metric-value">{activeTasks}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">✓</div>
          <div className="metric-content">
            <div className="metric-label">Completed Tasks</div>
            <div className="metric-value">
              {completedTasks} / {totalTasks}
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">🔢</div>
          <div className="metric-content">
            <div className="metric-label">Partitions</div>
            <div className="metric-value">{partitionCount}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">🏭</div>
          <div className="metric-content">
            <div className="metric-label">Total Stages</div>
            <div className="metric-value">{metrics.total_stages}</div>
          </div>
        </div>

        {activeShuffles > 0 && (
          <div className="metric-card metric-warning">
            <div className="metric-icon">🔀</div>
            <div className="metric-content">
              <div className="metric-label">Active Shuffles</div>
              <div className="metric-value">{activeShuffles}</div>
            </div>
          </div>
        )}

        {currentStage !== undefined && (
          <div className="metric-card metric-highlight">
            <div className="metric-icon">▶</div>
            <div className="metric-content">
              <div className="metric-label">Current Stage</div>
              <div className="metric-value">Stage {currentStage}</div>
            </div>
          </div>
        )}

        <div className="metric-card">
          <div className="metric-icon">⚙️</div>
          <div className="metric-content">
            <div className="metric-label">Avg Parallelism</div>
            <div className="metric-value">
              {metrics.avg_parallelism?.toFixed(1) || 0}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LiveMetrics;
