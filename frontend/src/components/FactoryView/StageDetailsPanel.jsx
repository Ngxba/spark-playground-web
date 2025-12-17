import './StageFlowView.css';

/**
 * StageDetailsPanel - Shows detailed information about the current stage
 *
 * Displays stage name, operation type, partition counts, and shuffle indicator.
 */
function StageDetailsPanel({ stage, stageIndex, totalStages }) {
  const getStageTypeLabel = (type) => {
    const labels = {
      scan: 'Input',
      transform: 'Transformation',
      shuffle: 'Shuffle',
      aggregate: 'Aggregation',
      output: 'Output'
    };
    return labels[type] || 'Processing';
  };

  const getStageIcon = (stageName) => {
    if (stageName.includes('Scan')) return '📂';
    if (stageName.includes('Filter')) return '🔍';
    if (stageName.includes('Shuffle') || stageName.includes('Exchange')) return '🔀';
    if (stageName.includes('Aggregate') || stageName.includes('HashAggregate')) return '📊';
    if (stageName.includes('Join')) return '🔗';
    if (stageName.includes('Sort')) return '↕️';
    if (stageName.includes('Project')) return '📋';
    return '⚙️';
  };

  return (
    <div className="stage-details-panel">
      <div className="stage-details-header">
        <h3>
          {getStageIcon(stage.name)} Stage {stageIndex + 1}: {stage.name}
        </h3>
        <span className="stage-type-badge">{getStageTypeLabel(stage.type)}</span>
      </div>

      <div className="stage-details-grid">
        <div className="detail-item">
          <label>Operation:</label>
          <value>{stage.operation}</value>
        </div>

        <div className="detail-item">
          <label>Input Partitions:</label>
          <value className="partition-count">{stage.input.partitionCount}</value>
        </div>

        <div className="detail-item">
          <label>Output Partitions:</label>
          <value className="partition-count">{stage.output.partitionCount}</value>
        </div>

        <div className="detail-item">
          <label>Type:</label>
          <value>{getStageTypeLabel(stage.type)}</value>
        </div>

        <div className="detail-item">
          <label>Shuffle:</label>
          <value className={stage.isShuffle ? 'shuffle-yes' : 'shuffle-no'}>
            {stage.isShuffle ? '⚠️ Yes' : '✅ No'}
          </value>
        </div>

        {stage.isRepartition && (
          <div className="detail-item">
            <label>Repartition:</label>
            <value className="repartition-yes">Yes</value>
          </div>
        )}
      </div>
    </div>
  );
}

export default StageDetailsPanel;
