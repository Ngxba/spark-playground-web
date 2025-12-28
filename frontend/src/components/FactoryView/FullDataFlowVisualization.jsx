import './StageFlowView.css';

/**
 * FullDataFlowVisualization - Complete pipeline visualization showing all steps
 *
 * Shows all steps connected in a single view with data flow between them.
 */
function FullDataFlowVisualization({ stages, currentStageIndex, onStageClick }) {
  const getStageColor = (stageType) => {
    const colors = {
      scan: '#10b981',      // Green
      transform: '#3b82f6', // Blue
      shuffle: '#f59e0b',   // Amber/Yellow
      aggregate: '#8b5cf6', // Purple
      output: '#10b981'     // Green
    };
    return colors[stageType] || '#6b7280';
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

  const renderPartitionGroup = (count, stageIndex, position) => {
    const partitions = [];
    const maxDisplay = Math.min(count, 4); // Show max 4 partitions visually

    for (let i = 0; i < maxDisplay; i++) {
      partitions.push(
        <div key={`${stageIndex}-${position}-${i}`} className="mini-partition-box">
          <div className="mini-partition-bar"></div>
        </div>
      );
    }

    return (
      <div className="partition-group">
        <div className="partition-group-label">{count} partition{count !== 1 ? 's' : ''}</div>
        <div className="partition-boxes">
          {partitions}
          {count > maxDisplay && <div className="partition-more">+{count - maxDisplay}</div>}
        </div>
      </div>
    );
  };

  const renderStageConnection = (stage, index, nextStage) => {
    const isCurrent = index === currentStageIndex;
    const isPast = index < currentStageIndex;
    const stageColor = getStageColor(stage.type);

    return (
      <div key={stage.id} className="full-flow-stage-group">
        {/* Stage Box */}
        <div
          className={`full-flow-stage ${isCurrent ? 'current' : ''} ${isPast ? 'completed' : ''} ${onStageClick ? 'clickable' : ''}`}
          onClick={() => onStageClick && onStageClick(index)}
          title={onStageClick ? `Click to view Step ${index + 1} details` : ''}
        >
          <div
            className="full-flow-stage-header"
            style={{ backgroundColor: stageColor }}
          >
            <span className="full-flow-stage-icon">{getStageIcon(stage.name)}</span>
            <div className="full-flow-stage-info">
              <div className="full-flow-stage-number">Step {index + 1}</div>
              <div className="full-flow-stage-name">{stage.name}</div>
            </div>
          </div>

          {/* Input Partitions */}
          <div className="full-flow-partitions">
            {renderPartitionGroup(stage.input.partitionCount, index, 'input')}
          </div>

          {/* Shuffle Indicator */}
          {stage.isShuffle && (
            <div className="full-flow-shuffle-badge">
              🔀 Shuffle
            </div>
          )}

          {/* Output Partitions */}
          <div className="full-flow-partitions">
            {renderPartitionGroup(stage.output.partitionCount, index, 'output')}
          </div>
        </div>

        {/* Connection Arrow to Next Stage */}
        {nextStage && (
          <div className="full-flow-connector">
            <svg width="60" height="100" viewBox="0 0 60 100" preserveAspectRatio="none">
              {/* Draw lines from output partitions to input partitions */}
              {stage.isShuffle ? (
                // Shuffle: crossing lines
                <>
                  <line x1="0" y1="20" x2="60" y2="20" stroke={stageColor} strokeWidth="2" strokeDasharray="4,2" opacity="0.6" />
                  <line x1="0" y1="40" x2="60" y2="40" stroke={stageColor} strokeWidth="2" strokeDasharray="4,2" opacity="0.6" />
                  <line x1="0" y1="60" x2="60" y2="60" stroke={stageColor} strokeWidth="2" strokeDasharray="4,2" opacity="0.6" />
                  <line x1="0" y1="80" x2="60" y2="80" stroke={stageColor} strokeWidth="2" strokeDasharray="4,2" opacity="0.6" />
                </>
              ) : (
                // Normal: straight lines
                <>
                  <line x1="0" y1="30" x2="60" y2="30" stroke={isPast ? stageColor : '#d1d5db'} strokeWidth="2" />
                  <line x1="0" y1="50" x2="60" y2="50" stroke={isPast ? stageColor : '#d1d5db'} strokeWidth="2" />
                  <line x1="0" y1="70" x2="60" y2="70" stroke={isPast ? stageColor : '#d1d5db'} strokeWidth="2" />
                </>
              )}
              {/* Arrow head */}
              <polygon points="60,50 54,46 54,54" fill={isPast ? stageColor : '#d1d5db'} />
            </svg>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="full-data-flow-visualization">
      <h4>[A6.3] 📊 Complete Data Flow Pipeline</h4>
      <div className="full-flow-container">
        {stages.map((stage, index) =>
          renderStageConnection(stage, index, stages[index + 1])
        )}
      </div>

      <div className="full-flow-legend">
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#10b981' }}></div>
          <span>Scan/Input</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#3b82f6' }}></div>
          <span>Transform</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#f59e0b' }}></div>
          <span>Shuffle</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#8b5cf6' }}></div>
          <span>Aggregate</span>
        </div>
      </div>
    </div>
  );
}

export default FullDataFlowVisualization;
