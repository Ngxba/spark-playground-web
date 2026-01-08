import { useState } from 'react';
import StageNavigator from './StageNavigator';
import StageDetailsPanel from './StageDetailsPanel';
import DataFlowVisualization from './DataFlowVisualization';
import StageExplanationPanel from './StageExplanationPanel';
import NavigationControls from './NavigationControls';
import FullDataFlowVisualization from './FullDataFlowVisualization';
import './StageFlowView.css';

/**
 * StageFlowView - Interactive Step-by-Step Execution Visualization
 *
 * Allows users to navigate through execution steps one at a time,
 * with educational explanations and data flow visualization.
 */
function StageFlowView({ stageFlowData, selectedStageIndex: externalSelectedStageIndex, onStageSelect }) {
  const [internalStageIndex, setInternalStageIndex] = useState(0);

  // Use external stage index if provided, otherwise use internal state
  const currentStageIndex = externalSelectedStageIndex !== undefined
    ? externalSelectedStageIndex
    : internalStageIndex;

  const handleStageIndexChange = (index) => {
    if (onStageSelect) {
      onStageSelect(index);
    } else {
      setInternalStageIndex(index);
    }
  };

  // If no stage flow data, show message
  if (!stageFlowData || !stageFlowData.stages || stageFlowData.stages.length === 0) {
    return (
      <div className="stage-flow-view-empty">
        <div className="empty-state">
          <h3>No Step-by-Step Flow Available</h3>
          <p>
            Run your code to see a step-by-step visualization of how Spark executes it.
            You'll be able to navigate through each step, see data flow, and learn about
            shuffles and optimizations.
          </p>
        </div>
      </div>
    );
  }

  const { stages, shuffleCount, explanation } = stageFlowData;
  const currentStage = stages[currentStageIndex];
  const previousStage = currentStageIndex > 0 ? stages[currentStageIndex - 1] : null;

  const handlePrevious = () => {
    if (currentStageIndex > 0) {
      handleStageIndexChange(currentStageIndex - 1);
    }
  };

  const handleNext = () => {
    if (currentStageIndex < stages.length - 1) {
      handleStageIndexChange(currentStageIndex + 1);
    }
  };

  const handleStageSelect = (index) => {
    if (index >= 0 && index < stages.length) {
      handleStageIndexChange(index);
    }
  };

  return (
    <div className="stage-flow-view">
      {/* [A5.1] Header with overall explanation */}
      <div className="stage-flow-header">
        <h2>[A5] Step-by-Step Execution</h2>
        <p className="overall-explanation">{explanation}</p>
        {shuffleCount > 0 && (
          <div className="shuffle-warning">
            ⚠️ This query has {shuffleCount} shuffle operation{shuffleCount > 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* [A5.2] Stage Navigator Timeline */}
      <StageNavigator
        stages={stages}
        currentStageIndex={currentStageIndex}
        onStageSelect={handleStageSelect}
      />

      {/* [A5.3] Full Pipeline Visualization (Execution Pipeline) */}
      <FullDataFlowVisualization
        stages={stages}
        currentStageIndex={currentStageIndex}
        onStageClick={handleStageSelect}
      />

      {/* [A5.4] Current Stage Details */}
      <StageDetailsPanel
        stage={currentStage}
        stageIndex={currentStageIndex}
        totalStages={stages.length}
      />

      {/* [A5.5] Data Flow Visualization */}
      <DataFlowVisualization
        stage={currentStage}
        previousStage={previousStage}
      />

      {/* [A5.6] Stage Explanation */}
      <StageExplanationPanel
        explanation={currentStage.explanation}
        performanceNote={currentStage.performanceNote}
      />

      {/* [A5.7] Navigation Controls */}
      <NavigationControls
        currentIndex={currentStageIndex}
        totalStages={stages.length}
        onPrevious={handlePrevious}
        onNext={handleNext}
        canGoPrevious={currentStageIndex > 0}
        canGoNext={currentStageIndex < stages.length - 1}
      />
    </div>
  );
}

export default StageFlowView;
