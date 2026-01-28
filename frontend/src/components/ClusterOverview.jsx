import './ClusterOverview.css';

/**
 * ClusterOverview - Shows Spark cluster configuration and resource utilization
 * Displays the "before execution" state: available resources, configuration
 */
function ClusterOverview({ clusterConfig, executorsInfo }) {
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

  const { mode, driver_memory, driver_memory_overhead, executor_memory, executor_memory_overhead, executor_cores, shuffle_partitions, runtime_partitions, cluster_capacity } = clusterConfig;

  const formatMemory = (memoryMb) => {
    if (memoryMb >= 1024) {
      return `${(memoryMb / 1024).toFixed(1)} GB`;
    }
    return `${memoryMb} MB`;
  };

  // Ensure executorsInfo is an array (default to empty array if undefined)
  const executorsInfoArray = executorsInfo || [];

  const coresInUse = executorsInfoArray.reduce((sum, i) => sum + i.cores, 0);
  const totalCluserCores = cluster_capacity?.total_cores || 1;
  const utilizationPercent = totalCluserCores > 0 ? (coresInUse / totalCluserCores) * 100 : 0;

  const memoryInUse = executorsInfoArray.reduce((sum, i) => {
    const executorMemory = (i.memory_mb || 0) + (i.memory_overhead_mb || 0);
    return sum + executorMemory;
  }, 0);
  const totalClusterMemory = cluster_capacity?.total_memory_mb || 2048;
  const memoryUtilizationPercent = totalClusterMemory > 0 ? (memoryInUse / totalClusterMemory) * 100 : 0;

  return (
    <div className="cluster-overview">
      <div className="cluster-overview-header">
        <h3>Spark Cluster Overview</h3>
        <div className="cluster-mode-badge">
          {mode}
        </div>
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
            <div className="config-label">Driver Memory Overhead</div>
            <div className="config-value">{driver_memory_overhead}</div>
          </div>
          <div className="config-item">
            <div className="config-label">Executor Memory</div>
            <div className="config-value">{executor_memory}</div>
          </div>
          <div className="config-item">
            <div className="config-label">Executor Memory Overhead</div>
            <div className="config-value">{executor_memory_overhead}</div>
          </div>
          <div className="config-item">
            <div className="config-label">Executor Cores</div>
            <div className="config-value">{executor_cores}</div>
          </div>
          <div className="config-item">
            <div className="config-label">Shuffle Partitions</div>
            <div className="config-value">{shuffle_partitions}</div>
          </div>
        </div>
      </div>

      {/* Cluster Summary Card */}
      <div className="cluster-summary-card">
        <h4>Cluster Resources</h4>
        <div className="summary-grid">
          <div className="summary-item">
            <div className="summary-icon">🖥️</div>
            <div className="summary-content">
              <div className="summary-label">Worker Node(s)</div>
              <div className="summary-value">{cluster_capacity?.total_workers || 1}</div>
            </div>
          </div>

          <div className="summary-item">
            <div className="summary-icon">⚙️</div>
            <div className="summary-content">
              <div className="summary-label">Total Cores</div>
              <div className="summary-value">{totalCluserCores}</div>
            </div>
          </div>

          <div className="summary-item">
            <div className="summary-icon">💾</div>
            <div className="summary-content">
              <div className="summary-label">Total Memory</div>
              <div className="summary-value">
                {formatMemory(cluster_capacity?.total_memory_mb || 2048)}
              </div>
            </div>
          </div>

          <div className="summary-item">
            <div className="summary-icon">📦</div>
            <div className="summary-content">
              <div className="summary-label">Runtime Partitions</div>
              <div className="summary-value">{runtime_partitions}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Resource Utilization */}
      <div className="utilization-card">
        <h4>Resource Utilization</h4>

        <div className="utilization-dual-grid">
          {/* Core Utilization */}
          <div className="utilization-section">
            <div className="utilization-section-header">
              <span className="utilization-icon">⚙️</span>
              <span className="utilization-title">Core Utilization</span>
            </div>

            <div className="utilization-stats">
              <div className="stat-row">
                <span className="stat-label">In Use:</span>
                <span className="stat-value success">{coresInUse} cores</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Available:</span>
                <span className="stat-value">{totalCluserCores - coresInUse} cores</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Total:</span>
                <span className="stat-value">{totalCluserCores} cores</span>
              </div>
            </div>

            <div className="utilization-bar-container">
              <div className="utilization-bar">
                <div
                  className="utilization-fill utilization-fill-cores"
                  style={{ width: `${utilizationPercent}%` }}
                />
              </div>
              <div className="utilization-percent utilization-percent-cores">{utilizationPercent.toFixed(1)}% utilized</div>
            </div>
          </div>

          {/* Memory Utilization */}
          <div className="utilization-section">
            <div className="utilization-section-header">
              <span className="utilization-icon">💾</span>
              <span className="utilization-title">Memory Utilization</span>
            </div>

            <div className="utilization-stats">
              <div className="stat-row">
                <span className="stat-label">In Use:</span>
                <span className="stat-value success">{formatMemory(memoryInUse)}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Available:</span>
                <span className="stat-value">{formatMemory(totalClusterMemory - memoryInUse)}</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Total:</span>
                <span className="stat-value">{formatMemory(totalClusterMemory)}</span>
              </div>
            </div>

            <div className="utilization-bar-container">
              <div className="utilization-bar">
                <div
                  className="utilization-fill utilization-fill-memory"
                  style={{ width: `${memoryUtilizationPercent}%` }}
                />
              </div>
              <div className="utilization-percent utilization-percent-memory">{memoryUtilizationPercent.toFixed(1)}% utilized</div>
            </div>
          </div>
        </div>
      </div>

      {/* Executors Detail */}
      <div className="executors-detail">
        <h4>Executor Details</h4>
        {executorsInfoArray.length > 0 ? (
          <div className="executors-grid">
            {executorsInfoArray.map((executor, index) => (
              <div key={executor.id || index} className={`executor-card ${executor.is_active ? 'executor-active' : 'executor-idle'}`}>
                <div className="executor-header">
                  <div className="executor-id">
                    {executor.id === 'driver' ? '🎯 Driver' : `⚡ Executor ${executor.id}`}
                  </div>
                  {/* <div className={`executor-status ${executor.state?.toLowerCase()}`}>
                    {executor.state}
                  </div> */}
                </div>

                <div className="executor-info">
                  <div className="info-row">
                    <span className="info-label">Host:</span>
                    <span className="info-value">{executor.host}:{executor.port}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Cores:</span>
                    <span className="info-value">{executor.cores}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Total Memory:</span>
                    <span className="info-value">{formatMemory(executor.memory_mb + executor.memory_overhead_mb)}</span>
                  </div>
                </div>

                {/* Memory Breakdown Visual */}
                <div className="executor-memory-breakdown">
                  <div className="memory-breakdown-label">Memory Breakdown</div>
                  <div className="memory-breakdown-bar">
                    <div
                      className="memory-segment memory-base"
                      style={{ width: `${(executor.memory_mb / (executor.memory_mb + executor.memory_overhead_mb)) * 100}%` }}
                      title={`Base Memory: ${formatMemory(executor.memory_mb)}`}
                    >
                      {(executor.memory_mb / (executor.memory_mb + executor.memory_overhead_mb)) > 0.25 && (
                        <span className="memory-segment-label">{formatMemory(executor.memory_mb)}</span>
                      )}
                    </div>
                    <div
                      className="memory-segment memory-overhead"
                      style={{ width: `${(executor.memory_overhead_mb / (executor.memory_mb + executor.memory_overhead_mb)) * 100}%` }}
                      title={`Overhead: ${formatMemory(executor.memory_overhead_mb)}`}
                    >
                      {(executor.memory_overhead_mb / (executor.memory_mb + executor.memory_overhead_mb)) > 0.25 && (
                        <span className="memory-segment-label">{formatMemory(executor.memory_overhead_mb)}</span>
                      )}
                    </div>
                  </div>
                  <div className="memory-breakdown-legend">
                    <div className="legend-item">
                      <span className="legend-color legend-color-base"></span>
                      <span className="legend-text">Base: {formatMemory(executor.memory_mb)}</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-color legend-color-overhead"></span>
                      <span className="legend-text">Overhead: {formatMemory(executor.memory_overhead_mb)}</span>
                    </div>
                  </div>
                </div>

                {/* Visual core representation */}
                <div className="executor-cores">
                  {executor.cores === 0 ? (
                    <div className="executor-cores-empty">No dedicated cores (Driver only)</div>
                  ) : (
                    <>
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
                    </>
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
