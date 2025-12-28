import './StageFlowView.css';

/**
 * NavigationControls - Buttons to move through steps
 *
 * Provides Previous/Next buttons and current step indicator.
 */
function NavigationControls({
  currentIndex,
  totalStages,
  onPrevious,
  onNext,
  canGoPrevious,
  canGoNext
}) {
  return (
    <div className="navigation-controls">
      <button
        className="nav-button prev-button"
        onClick={onPrevious}
        disabled={!canGoPrevious}
        title="Previous Step"
      >
        ← Previous
      </button>

      <div className="stage-indicator">
        Step {currentIndex + 1} of {totalStages}
      </div>

      <button
        className="nav-button next-button"
        onClick={onNext}
        disabled={!canGoNext}
        title="Next Step"
      >
        Next →
      </button>
    </div>
  );
}

export default NavigationControls;
