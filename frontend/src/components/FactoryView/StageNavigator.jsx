import './StageFlowView.css';

/**
 * StageNavigator - Timeline showing all steps with click navigation
 *
 * Displays a horizontal timeline of all steps with visual indicators
 * for step types and allows clicking to jump to any step.
 */
function StageNavigator({ stages, currentStageIndex, onStageSelect }) {
  const getStageColor = (stageType) => {
    const colors = {
      scan: '#10b981',      // Green
      transform: '#3b82f6', // Blue
      shuffle: '#f59e0b',   // Amber/Yellow
      aggregate: '#8b5cf6', // Purple
      output: '#10b981'     // Green
    };
    return colors[stageType] || '#6b7280'; // Default gray
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
    <div className="stage-navigator">
      <div className="stage-timeline">
        {stages.map((stage, index) => (
          <>
            {/* Stage Container - Circle and Label together */}
            <div key={stage.id} className="stage-timeline-item">
              <div
                className={`stage-circle ${index === currentStageIndex ? 'active' : ''} ${
                  index < currentStageIndex ? 'completed' : ''
                }`}
                style={{
                  backgroundColor: index === currentStageIndex ? getStageColor(stage.type) :
                                   index < currentStageIndex ? getStageColor(stage.type) : '#e5e7eb'
                }}
                onClick={() => onStageSelect(index)}
                title={`${stage.name} - Click to view`}
              >
                <span className="stage-icon">{getStageIcon(stage.name)}</span>
              </div>

              {/* Stage Label */}
              <div className="stage-label">
                <div className="stage-number">Step {index + 1}</div>
                <div className="stage-name" title={stage.name}>{stage.name}</div>
              </div>
            </div>

            {/* Arrow connector - Separate between stages */}
            {index < stages.length - 1 && (
              <div className="stage-arrow" key={`arrow-${index}`}>
                <svg width="50" height="4" viewBox="0 0 50 4">
                  <line
                    x1="0"
                    y1="2"
                    x2="45"
                    y2="2"
                    stroke={index < currentStageIndex ? getStageColor(stages[index].type) : '#d1d5db'}
                    strokeWidth="2"
                  />
                  <polygon
                    points="50,2 44,0 44,4"
                    fill={index < currentStageIndex ? getStageColor(stages[index].type) : '#d1d5db'}
                  />
                </svg>
              </div>
            )}
          </>
        ))}
      </div>
    </div>
  );
}

export default StageNavigator;
