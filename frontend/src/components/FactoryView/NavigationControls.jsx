import './StageFlowView.css';

/**
 * NavigationControls - Buttons to move through stages
 *
 * Provides Previous/Next buttons and current stage indicator.
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
        title="Previous Stage"
      >
        ← Previous
      </button>

      <div className="stage-indicator">
        Stage {currentIndex + 1} of {totalStages}
      </div>

      <button
        className="nav-button next-button"
        onClick={onNext}
        disabled={!canGoNext}
        title="Next Stage"
      >
        Next →
      </button>
    </div>
  );
}

export default NavigationControls;
