import { useMemo, useState } from 'react';
import { calculateExecutionRounds, getUtilizationColorClass, formatDuration } from './utils/roundsCalculator';
import './ExecutionRoundsView.css';

/**
 * CoreAssignmentGrid - Shows which cores handle which tasks in a round
 */
function CoreAssignmentGrid({ round, totalCores, nodes }) {
  // Group assignments by node and core
  const coreGrid = {};
  nodes.forEach(node => {
    coreGrid[node.id] = Array(node.cores).fill(null);
  });

  // Fill in the assignments
  round.coreAssignments.forEach(assignment => {
    if (coreGrid[assignment.nodeId]) {
      coreGrid[assignment.nodeId][assignment.coreId] = assignment;
    }
  });

  return (
    <div className="core-assignment-grid">
      <div className="grid-header">Core Assignments:</div>
      <div className="grid-content">
        {nodes.map(node => (
          <div key={node.id} className="node-cores-grid">
            <div className="node-label">Node {node.id}</div>
            <div className="cores-row">
              {coreGrid[node.id].map((assignment, coreIdx) => (
                <div
                  key={coreIdx}
                  className={`core-cell ${assignment ? 'core-assigned' : 'core-empty'}`}
                  title={assignment ? `Core ${coreIdx}: Partition ${assignment.partitionId}` : `Core ${coreIdx}: Idle`}
                >
                  <div className="core-number">C{coreIdx}</div>
                  {assignment && (
                    <div className="core-partition">P{assignment.partitionId}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * RoundCard - Individual round display with expand/collapse
 */
function RoundCard({ round, roundNumber, isActive, isCompleted, isPending, totalCores, nodes }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const statusClass = isActive ? 'round-active' : isCompleted ? 'round-completed' : isPending ? 'round-pending' : '';

  return (
    <div className={`round-card ${statusClass}`}>
      <div className="round-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="round-header-left">
          <div className="round-number">Round {roundNumber}</div>
          <div className="round-partitions">
            {round.partitions.length} partition{round.partitions.length !== 1 ? 's' : ''}
          </div>
          {isActive && <span className="round-badge active-badge">Active</span>}
          {isCompleted && <span className="round-badge completed-badge">Completed</span>}
          {isPending && <span className="round-badge pending-badge">Pending</span>}
        </div>
        <div className="round-header-right">
          <div className="round-timing">
            {formatDuration(round.duration)}
          </div>
          <button className="expand-button" aria-label={isExpanded ? 'Collapse' : 'Expand'}>
            {isExpanded ? '▼' : '▶'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="round-details">
          {/* Core Utilization Bar */}
          <div className="round-utilization">
            <div className="utilization-label">
              Core Utilization: {round.coresUsed}/{totalCores} ({round.utilizationPercent}%)
            </div>
            <div className="utilization-bar-container">
              <div
                className={`utilization-bar ${getUtilizationColorClass(round.utilizationPercent)}`}
                style={{ width: `${round.utilizationPercent}%` }}
              />
            </div>
            {round.coresIdle > 0 && (
              <div className="idle-cores-warning">
                ⚠️ {round.coresIdle} core{round.coresIdle !== 1 ? 's' : ''} idle
              </div>
            )}
          </div>

          {/* Core Assignment Grid */}
          <CoreAssignmentGrid round={round} totalCores={totalCores} nodes={nodes} />

          {/* Partition List */}
          <div className="round-partition-list">
            <div className="partition-list-label">Partitions processed:</div>
            <div className="partition-chips">
              {round.partitions.map((partitionId, idx) => (
                <span key={idx} className="partition-chip">
                  P{partitionId}
                </span>
              ))}
            </div>
          </div>

          {/* Timing Info */}
          <div className="round-timing-info">
            <div className="timing-item">
              <span className="timing-label">Start:</span>
              <span className="timing-value">{round.startTime.toFixed(2)}s</span>
            </div>
            <div className="timing-item">
              <span className="timing-label">End:</span>
              <span className="timing-value">{round.endTime.toFixed(2)}s</span>
            </div>
            <div className="timing-item">
              <span className="timing-label">Duration:</span>
              <span className="timing-value">{formatDuration(round.duration)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * CoreUtilizationSummary - Chart showing utilization across all rounds
 */
function CoreUtilizationSummary({ rounds, totalCores, currentRound }) {
  const avgUtilization = Math.round(
    rounds.reduce((sum, r) => sum + r.utilizationPercent, 0) / rounds.length
  );

  return (
    <div className="core-utilization-summary">
      <div className="summary-header">
        <h6>Core Utilization Summary</h6>
        <div className="avg-utilization">
          Average: <span className="avg-value">{avgUtilization}%</span>
        </div>
      </div>

      <div className="utilization-chart">
        {rounds.map((round, idx) => {
          const isCurrentRound = currentRound === idx;
          return (
            <div
              key={idx}
              className={`chart-bar ${isCurrentRound ? 'chart-bar-active' : ''}`}
              title={`Round ${idx + 1}: ${round.utilizationPercent}% utilization`}
            >
              <div className="bar-label">R{idx + 1}</div>
              <div className="bar-container">
                <div
                  className={`bar-fill ${getUtilizationColorClass(round.utilizationPercent)}`}
                  style={{ height: `${round.utilizationPercent}%` }}
                />
              </div>
              <div className="bar-value">{round.utilizationPercent}%</div>
            </div>
          );
        })}
      </div>

      {avgUtilization < 75 && (
        <div className="utilization-tip">
          💡 Tip: {avgUtilization < 50 ? 'Low' : 'Moderate'} core utilization detected.
          Consider adjusting the number of partitions to match available cores for better performance.
        </div>
      )}
    </div>
  );
}

/**
 * ExecutionRoundsView - Main component showing rounds breakdown
 */
function ExecutionRoundsView({ stage, nodes, currentState }) {
  const roundsData = useMemo(() => {
    if (!stage || !nodes) return null;
    return calculateExecutionRounds(stage, nodes, currentState?.time);
  }, [stage, nodes, currentState?.time]);

  if (!roundsData) return null;

  return (
    <div className="execution-rounds-view">
      <h5 className="section-title">[A2.5] Execution Rounds Analysis</h5>

      <div className="rounds-explanation">
        <p>
          Spark executes tasks in parallel rounds based on available cores.
          Each round processes as many partitions as there are cores available.
        </p>
      </div>

      {/* Formula Display */}
      <div className="rounds-formula">
        <div className="formula-icon">🧮</div>
        <div className="formula-content">
          <div className="formula-label">Parallel Execution Formula:</div>
          <div className="formula-equation">
            <span className="formula-term">{roundsData.totalPartitions} partition{roundsData.totalPartitions !== 1 ? 's' : ''}</span>
            <span className="formula-operator">÷</span>
            <span className="formula-term">{roundsData.totalCores} core{roundsData.totalCores !== 1 ? 's' : ''}</span>
            <span className="formula-operator">=</span>
            <span className="formula-result">{roundsData.totalRounds} round{roundsData.totalRounds !== 1 ? 's' : ''}</span>
          </div>
          <div className="formula-explanation">
            {roundsData.totalRounds === 1 ? (
              <span className="efficiency-good">✓ All partitions process in parallel (optimal)</span>
            ) : (
              <span className="efficiency-warning">
                ⚠️ Tasks execute in {roundsData.totalRounds} sequential rounds
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Rounds Timeline */}
      <div className="rounds-timeline">
        <div className="timeline-header">Execution Rounds:</div>
        {roundsData.rounds.map((round, idx) => (
          <RoundCard
            key={idx}
            round={round}
            roundNumber={idx + 1}
            isActive={roundsData.currentRound === idx}
            isCompleted={currentState && roundsData.currentRound !== null && roundsData.currentRound > idx}
            isPending={currentState && (roundsData.currentRound === null || roundsData.currentRound < idx)}
            totalCores={roundsData.totalCores}
            nodes={nodes}
          />
        ))}
      </div>

      {/* Core Utilization Summary */}
      <CoreUtilizationSummary
        rounds={roundsData.rounds}
        totalCores={roundsData.totalCores}
        currentRound={roundsData.currentRound}
      />
    </div>
  );
}

export default ExecutionRoundsView;
