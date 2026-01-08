import './ExecutionInsights.css';

function ExecutionInsights({ metrics, dagStructure }) {
  if (!metrics) {
    return (
      <div className="execution-insights">
        <p className="no-data">No execution data available</p>
      </div>
    );
  }

  const getOptimizations = () => {
    const optimizations = [];

    if (metrics.broadcast_used) {
      optimizations.push({
        type: 'success',
        icon: '✅',
        title: 'Broadcast Join Detected',
        description:
          'Small dataset was broadcasted to all workers, avoiding expensive shuffle operations. This is optimal for joining large datasets with small lookup tables.',
        impact: 'High Performance Gain',
      });
    }

    if (metrics.cache_used) {
      optimizations.push({
        type: 'success',
        icon: '✅',
        title: 'Caching Utilized',
        description:
          'DataFrame was cached in memory for reuse, avoiding recomputation. This significantly speeds up iterative operations.',
        impact: 'Medium Performance Gain',
      });
    }

    return optimizations;
  };

  const getSuggestions = () => {
    const suggestions = [];

    if (metrics.shuffles > 0 && !metrics.broadcast_used) {
      suggestions.push({
        type: 'warning',
        icon: '⚠️',
        title: 'Shuffle Detected',
        description: `${metrics.shuffles} shuffle operation${
          metrics.shuffles > 1 ? 's' : ''
        } detected. Shuffles redistribute data across partitions and can be expensive. Consider using broadcast() for small datasets to avoid shuffles.`,
        suggestion: 'Use df.join(broadcast(small_df)) for small lookup tables',
      });
    }

    if (metrics.skew_detected) {
      suggestions.push({
        type: 'warning',
        icon: '⚠️',
        title: 'Data Skew Detected',
        description:
          'Some partitions have significantly more data than others, which can cause performance bottlenecks. Consider repartitioning or salting techniques.',
        suggestion: 'Use df.repartition() or apply salting to distribute data evenly',
      });
    }

    if (metrics.stages > 3) {
      suggestions.push({
        type: 'info',
        icon: 'ℹ️',
        title: 'Multiple Stages',
        description: `Execution plan has ${metrics.stages} stages. Each stage boundary represents a shuffle operation. Fewer stages generally mean better performance.`,
        suggestion: 'Review your transformations to minimize shuffles',
      });
    }

    return suggestions;
  };

  const optimizations = getOptimizations();
  const suggestions = getSuggestions();

  return (
    <div className="execution-insights">
      <h3>Execution Analysis</h3>

      {/* Stage Breakdown */}
      <div className="insights-section">
        <h4>Execution Summary</h4>
        <div className="execution-summary">
          <div className="summary-item">
            <span className="summary-icon">🏭</span>
            <div className="summary-content">
              <div className="summary-label">Stages</div>
              <div className="summary-value">{metrics.stages}</div>
              <div className="summary-description">
                {metrics.stages === 1
                  ? 'Single-stage execution (optimal)'
                  : `Multi-stage execution with ${metrics.stages - 1} shuffle${
                      metrics.stages > 2 ? 's' : ''
                    }`}
              </div>
            </div>
          </div>

          <div className="summary-item">
            <span className="summary-icon">🔁</span>
            <div className="summary-content">
              <div className="summary-label">Shuffles</div>
              <div className="summary-value">{metrics.shuffles}</div>
              <div className="summary-description">
                {metrics.shuffles === 0
                  ? 'No data movement between partitions'
                  : `Data redistributed ${metrics.shuffles} time${
                      metrics.shuffles > 1 ? 's' : ''
                    }`}
              </div>
            </div>
          </div>

          <div className="summary-item">
            <span className="summary-icon">⏱️</span>
            <div className="summary-content">
              <div className="summary-label">Simulated Time</div>
              <div className="summary-value">{(metrics.time_simulated || 0).toFixed(1)}s</div>
              <div className="summary-description">
                Estimated execution time based on operations
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Optimizations Applied */}
      {optimizations.length > 0 && (
        <div className="insights-section">
          <h4>Optimizations Applied</h4>
          <div className="insights-list">
            {optimizations.map((opt, i) => (
              <div key={i} className={`insight-card ${opt.type}`}>
                <div className="insight-header">
                  <span className="insight-icon">{opt.icon}</span>
                  <span className="insight-title">{opt.title}</span>
                  <span className="insight-impact">{opt.impact}</span>
                </div>
                <p className="insight-description">{opt.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="insights-section">
          <h4>Optimization Opportunities</h4>
          <div className="insights-list">
            {suggestions.map((sug, i) => (
              <div key={i} className={`insight-card ${sug.type}`}>
                <div className="insight-header">
                  <span className="insight-icon">{sug.icon}</span>
                  <span className="insight-title">{sug.title}</span>
                </div>
                <p className="insight-description">{sug.description}</p>
                {sug.suggestion && (
                  <div className="insight-suggestion">
                    <strong>Suggestion:</strong> {sug.suggestion}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {optimizations.length === 0 && suggestions.length === 0 && (
        <div className="insights-section">
          <p className="no-insights">
            Run your code to see detailed execution analysis and optimization
            suggestions.
          </p>
        </div>
      )}
    </div>
  );
}

export default ExecutionInsights;
