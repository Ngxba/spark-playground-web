import './StageFlowView.css';

/**
 * DataFlowVisualization - Visual representation of data movement
 *
 * Shows partitions as cards and visualizes data flow between stages,
 * with special handling for shuffles and repartitioning.
 */
function DataFlowVisualization({ stage, previousStage }) {
  const inputPartitions = stage.input.partitionCount;
  const outputPartitions = stage.output.partitionCount;
  const isShuffle = stage.isShuffle;
  const isRepartition = stage.isRepartition;

  // Render partition boxes
  const renderPartitions = (count, label, className) => {
    const partitions = [];
    for (let i = 0; i < count; i++) {
      partitions.push(
        <div key={i} className={`partition-box ${className}`}>
          <div className="partition-label">Partition {i + 1}</div>
          <div className="partition-data">
            <div className="data-bar"></div>
            <div className="data-bar"></div>
            <div className="data-bar"></div>
          </div>
        </div>
      );
    }
    return (
      <div className="partitions-column">
        <div className="partitions-label">{label}</div>
        <div className="partitions-grid">{partitions}</div>
      </div>
    );
  };

  // Render simple stage (no shuffle)
  const renderSimpleStage = () => {
    return (
      <div className="data-flow-simple">
        {renderPartitions(inputPartitions, `Input (${inputPartitions} partitions)`, 'input')}
        <div className="flow-arrows">
          {Array.from({ length: inputPartitions }).map((_, i) => (
            <div key={i} className="simple-arrow">→</div>
          ))}
        </div>
        {renderPartitions(outputPartitions, `Output (${outputPartitions} partitions)`, 'output')}
      </div>
    );
  };

  // Render shuffle stage
  const renderShuffleStage = () => {
    return (
      <div className="data-flow-shuffle">
        {renderPartitions(inputPartitions, `Input (${inputPartitions} partitions)`, 'input')}

        <div className="shuffle-box">
          <div className="shuffle-icon">🔀</div>
          <div className="shuffle-label">Exchange</div>
          <div className="shuffle-sublabel">(Shuffle)</div>
        </div>

        {renderPartitions(outputPartitions, `Output (${outputPartitions} partitions)`, 'output')}

        {/* SVG for crossing lines */}
        <svg className="shuffle-lines" viewBox="0 0 200 200">
          {/* Draw crossing lines from input to output partitions */}
          {Array.from({ length: inputPartitions }).map((_, i) => {
            const y1 = (i + 0.5) * (200 / inputPartitions);
            return Array.from({ length: outputPartitions }).map((_, j) => {
              const y2 = (j + 0.5) * (200 / outputPartitions);
              return (
                <line
                  key={`${i}-${j}`}
                  x1="0"
                  y1={y1}
                  x2="200"
                  y2={y2}
                  stroke="#f59e0b"
                  strokeWidth="1"
                  opacity="0.3"
                  strokeDasharray="4,2"
                />
              );
            });
          })}
        </svg>

        <div className="shuffle-warning-text">
          ⚠️ Warning: This is an expensive operation! Data is being redistributed across partitions.
        </div>
      </div>
    );
  };

  // Render repartition stage
  const renderRepartitionStage = () => {
    const increasing = outputPartitions > inputPartitions;
    return (
      <div className="data-flow-repartition">
        {renderPartitions(inputPartitions, `Input (${inputPartitions} partitions)`, 'input')}

        <div className="repartition-middle">
          <div className="repartition-icon">
            {increasing ? '📈' : '📉'}
          </div>
          <div className="repartition-label">
            {increasing ? 'Increasing Partitions' : 'Decreasing Partitions'}
          </div>
        </div>

        {renderPartitions(outputPartitions, `Output (${outputPartitions} partitions)`, 'output')}

        {/* SVG for repartition lines */}
        <svg className="repartition-lines" viewBox="0 0 200 200">
          {Array.from({ length: inputPartitions }).map((_, i) => {
            const y1 = (i + 0.5) * (200 / inputPartitions);
            const partitionsPerInput = Math.ceil(outputPartitions / inputPartitions);
            const startOutput = i * partitionsPerInput;

            return Array.from({ length: partitionsPerInput }).map((_, j) => {
              const outputIdx = startOutput + j;
              if (outputIdx >= outputPartitions) return null;
              const y2 = (outputIdx + 0.5) * (200 / outputPartitions);

              return (
                <line
                  key={`${i}-${j}`}
                  x1="0"
                  y1={y1}
                  x2="200"
                  y2={y2}
                  stroke="#8b5cf6"
                  strokeWidth="2"
                  opacity="0.5"
                />
              );
            });
          })}
        </svg>
      </div>
    );
  };

  return (
    <div className="data-flow-visualization">
      <h4>Data Flow</h4>

      {isShuffle ? (
        renderShuffleStage()
      ) : isRepartition ? (
        renderRepartitionStage()
      ) : (
        renderSimpleStage()
      )}
    </div>
  );
}

export default DataFlowVisualization;
