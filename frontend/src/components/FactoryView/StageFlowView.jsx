import { useState } from 'react';
import StageNavigator from './StageNavigator';
import StageDetailsPanel from './StageDetailsPanel';
import DataFlowVisualization from './DataFlowVisualization';
import StageExplanationPanel from './StageExplanationPanel';
import NavigationControls from './NavigationControls';
import FullDataFlowVisualization from './FullDataFlowVisualization';
import './StageFlowView.css';

/**
 * StageFlowView - Interactive Stage-by-Stage Execution Visualization
 *
 * Allows users to navigate through Spark execution stages one at a time,
 * with educational explanations and data flow visualization.
 */
function StageFlowView({ stageFlowData }) {
  const [currentStageIndex, setCurrentStageIndex] = useState(0);

  // If no stage flow data, show message
  if (!stageFlowData || !stageFlowData.stages || stageFlowData.stages.length === 0) {
    return (
      <div className="stage-flow-view-empty">
        <div className="empty-state">
          <h3>No Stage Flow Data Available</h3>
          <p>
            Run your code to see a stage-by-stage visualization of how Spark executes it.
            You'll be able to navigate through each stage, see data flow, and learn about
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
      setCurrentStageIndex(currentStageIndex - 1);
    }
  };

  const handleNext = () => {
    if (currentStageIndex < stages.length - 1) {
      setCurrentStageIndex(currentStageIndex + 1);
    }
  };

  const handleStageSelect = (index) => {
    if (index >= 0 && index < stages.length) {
      setCurrentStageIndex(index);
    }
  };

  return (
    <div className="stage-flow-view">
      {/* Header with overall explanation */}
      <div className="stage-flow-header">
        <h2>Stage-by-Stage Execution</h2>
        <p className="overall-explanation">{explanation}</p>
        {shuffleCount > 0 && (
          <div className="shuffle-warning">
            ⚠️ This query has {shuffleCount} shuffle operation{shuffleCount > 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Stage Navigator Timeline */}
      <StageNavigator
        stages={stages}
        currentStageIndex={currentStageIndex}
        onStageSelect={handleStageSelect}
      />

      {/* Full Pipeline Visualization */}
      <FullDataFlowVisualization
        stages={stages}
        currentStageIndex={currentStageIndex}
      />

      {/* Current Stage Details */}
      <StageDetailsPanel
        stage={currentStage}
        stageIndex={currentStageIndex}
        totalStages={stages.length}
      />

      {/* Data Flow Visualization */}
      <DataFlowVisualization
        stage={currentStage}
        previousStage={previousStage}
      />

      {/* Stage Explanation */}
      <StageExplanationPanel
        explanation={currentStage.explanation}
        performanceNote={currentStage.performanceNote}
      />

      {/* Navigation Controls */}
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
