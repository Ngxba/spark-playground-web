import './StageFlowView.css';

/**
 * StageExplanationPanel - Educational text explaining what's happening
 *
 * Provides plain language explanation of the current stage,
 * performance implications, and best practices.
 */
function StageExplanationPanel({ explanation, performanceNote }) {
  return (
    <div className="stage-explanation-panel">
      <h4>💡 What's Happening?</h4>

      <div className="explanation-content">
        {explanation.split('\n').map((line, index) => (
          <p key={index}>{line}</p>
        ))}
      </div>

      {performanceNote && (
        <div className="performance-note">
          <div className="performance-note-content">
            {performanceNote}
          </div>
        </div>
      )}
    </div>
  );
}

export default StageExplanationPanel;
