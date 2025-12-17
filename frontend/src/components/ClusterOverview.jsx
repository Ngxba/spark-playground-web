import './ClusterOverview.css';

/**
 * ClusterOverview - Shows Spark cluster configuration and resource utilization
 * Displays the "before execution" state: available resources, configuration
 */
function ClusterOverview({ clusterConfig }) {
  if (!clusterConfig) {
    return (
      <div className="cluster-overview-empty">
        <div className="empty-state">
          <h3>No Cluster Information Available</h3>
          <p>Run your code to see cluster configuration and resource utilization.</p>
        </div>
      </div>
    );
  }

  const { mode, driver_memory, executor_memory, shuffle_partitions, total_cores, executors, cluster_summary } = clusterConfig;

  const formatMemory = (memoryMb) => {
    if (memoryMb >= 1024) {
      return `${(memoryMb / 1024).toFixed(1)} GB`;
    }
    return `${memoryMb} MB`;
  };

  const coresInUse = cluster_summary?.cores_in_use || 0;
  const coresAvailable = cluster_summary?.cores_available || total_cores;
  const utilizationPercent = coresAvailable > 0 ? (coresInUse / coresAvailable) * 100 : 0;

  return (
    <div className="cluster-overview">
      <div className="cluster-overview-header">
        <h3>Spark Cluster Overview</h3>
        <div className="cluster-mode-badge">
          {mode}
        </div>
      </div>

      {/* Cluster Summary Card */}
      <div className="cluster-summary-card">
        <h4>Cluster Resources</h4>
        <div className="summary-grid">
          <div className="summary-item">
            <div className="summary-icon">🖥️</div>
            <div className="summary-content">
              <div className="summary-label">Executors</div>
              <div className="summary-value">{cluster_summary?.total_executors || 1}</div>
            </div>
          </div>

          <div className="summary-item">
            <div className="summary-icon">⚙️</div>
            <div className="summary-content">
              <div className="summary-label">Total Cores</div>
              <div className="summary-value">{coresAvailable}</div>
            </div>
          </div>

          <div className="summary-item">
            <div className="summary-icon">💾</div>
            <div className="summary-content">
              <div className="summary-label">Total Memory</div>
              <div className="summary-value">
                {formatMemory(cluster_summary?.total_memory_mb || 2048)}
              </div>
            </div>
          </div>

          <div className="summary-item">
            <div className="summary-icon">🔀</div>
            <div className="summary-content">
              <div className="summary-label">Shuffle Partitions</div>
              <div className="summary-value">{shuffle_partitions}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Resource Utilization */}
      <div className="utilization-card">
        <h4>Core Utilization</h4>
        <div className="utilization-stats">
          <div className="stat-row">
            <span className="stat-label">In Use:</span>
            <span className="stat-value success">{coresInUse} cores</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Available:</span>
            <span className="stat-value">{coresAvailable - coresInUse} cores</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Total:</span>
            <span className="stat-value">{coresAvailable} cores</span>
          </div>
        </div>

        <div className="utilization-bar-container">
          <div className="utilization-bar">
            <div
              className="utilization-fill"
              style={{ width: `${utilizationPercent}%` }}
            />
          </div>
          <div className="utilization-percent">{utilizationPercent.toFixed(1)}% utilized</div>
        </div>
      </div>

      {/* Executors Detail */}
      <div className="executors-detail">
        <h4>Executor Details</h4>
        {executors && executors.length > 0 ? (
          <div className="executors-grid">
            {executors.map((executor, index) => (
              <div key={executor.id || index} className={`executor-card ${executor.is_active ? 'executor-active' : 'executor-idle'}`}>
                <div className="executor-header">
                  <div className="executor-id">
                    {executor.id === 'driver' ? '🎯 Driver' : `⚡ Executor ${executor.id}`}
                  </div>
                  <div className={`executor-status ${executor.state?.toLowerCase()}`}>
                    {executor.state}
                  </div>
                </div>

                <div className="executor-info">
                  <div className="info-row">
                    <span className="info-label">Host:</span>
                    <span className="info-value">{executor.host}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Cores:</span>
                    <span className="info-value">{executor.cores}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Memory:</span>
                    <span className="info-value">{formatMemory(executor.memory_mb)}</span>
                  </div>
                </div>

                {/* Visual core representation */}
                <div className="executor-cores">
                  {[...Array(Math.min(executor.cores, 12))].map((_, i) => (
                    <div
                      key={i}
                      className={`core-indicator ${executor.is_active ? 'core-active' : 'core-idle'}`}
                      title={`Core ${i + 1}`}
                    />
                  ))}
                  {executor.cores > 12 && (
                    <div className="core-overflow">+{executor.cores - 12}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-executors">
            <p>No executor information available</p>
          </div>
        )}
      </div>

      {/* Configuration Details */}
      <div className="config-details">
        <h4>Configuration</h4>
        <div className="config-grid">
          <div className="config-item">
            <div className="config-label">Execution Mode</div>
            <div className="config-value">{mode}</div>
          </div>
          <div className="config-item">
            <div className="config-label">Driver Memory</div>
            <div className="config-value">{driver_memory}</div>
          </div>
          <div className="config-item">
            <div className="config-label">Executor Memory</div>
            <div className="config-value">{executor_memory}</div>
          </div>
          <div className="config-item">
            <div className="config-label">Shuffle Partitions</div>
            <div className="config-value">{shuffle_partitions}</div>
          </div>
        </div>
      </div>

      {/* Info Panel */}
      <div className="cluster-info-panel">
        <div className="info-icon">💡</div>
        <div className="info-text">
          <strong>About This Cluster:</strong> This playground runs in <strong>local mode</strong>,
          where Spark uses all available CPU cores on your machine. In production, you'd have
          multiple worker nodes with distributed executors across a cluster.
        </div>
      </div>
    </div>
  );
}

export default ClusterOverview;
