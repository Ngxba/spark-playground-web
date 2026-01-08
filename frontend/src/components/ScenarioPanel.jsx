import { useState } from 'react';
import './ScenarioPanel.css';

/**
 * ScenarioPanel - Beautiful display of puzzle scenario and context
 * Replaces the old FactoryVisualization component
 */
function ScenarioPanel({ puzzle, isRunning, result }) {
  const [showHint, setShowHint] = useState(false);

  if (!puzzle) return null;

  const getStatusIcon = () => {
    if (isRunning) return '⚡';
    if (result?.correct) return '✅';
    if (result && !result.correct) return '❌';
    return '📝';
  };

  const getStatusText = () => {
    if (isRunning) return 'Executing...';
    if (result?.correct) return 'Solution Correct!';
    if (result && !result.correct) return 'Try Again';
    return 'Ready to Code';
  };

  const getStatusClass = () => {
    if (isRunning) return 'status-running';
    if (result?.correct) return 'status-success';
    if (result && !result.correct) return 'status-error';
    return 'status-ready';
  };

  return (
    <div className="scenario-panel">
      {/* Status Card */}
      <div className={`status-card ${getStatusClass()}`}>
        <div className="status-icon">{getStatusIcon()}</div>
        <div className="status-content">
          <div className="status-text">{getStatusText()}</div>
          {result && result.stars > 0 && (
            <div className="status-stars">
              {[...Array(3)].map((_, i) => (
                <span
                  key={i}
                  className={i < result.stars ? 'star-filled' : 'star-empty'}
                >
                  ★
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Scenario Description */}
      <div className="scenario-card">
        <div className="scenario-header">
          <h3>📖 Scenario</h3>
        </div>
        <div className="scenario-content">
          <p>{puzzle.scenario}</p>
        </div>
      </div>

      {/* Expected Output Preview */}
      {puzzle.expected_output && !isRunning && (
        <div className="expected-output-card">
          <div className="card-header">
            <h4>🎯 Expected Result</h4>
            <button
              className="toggle-btn"
              onClick={() => setShowHint(!showHint)}
            >
              {showHint ? 'Hide' : 'Show'} Example
            </button>
          </div>
          {showHint && (
            <div className="expected-output-content">
              <div className="output-preview">
                {Array.isArray(puzzle.expected_output) ? (
                  <table className="mini-table">
                    <thead>
                      <tr>
                        {Object.keys(puzzle.expected_output[0] || {}).map((key) => (
                          <th key={key}>{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {puzzle.expected_output.slice(0, 3).map((row, idx) => (
                        <tr key={idx}>
                          {Object.values(row).map((val, i) => (
                            <td key={i}>{String(val)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <pre>{JSON.stringify(puzzle.expected_output, null, 2)}</pre>
                )}
                {Array.isArray(puzzle.expected_output) &&
                  puzzle.expected_output.length > 3 && (
                    <div className="more-rows">
                      ... and {puzzle.expected_output.length - 3} more rows
                    </div>
                  )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quick Tips */}
      <div className="tips-card">
        <div className="card-header">
          <h4>💡 Quick Tips</h4>
        </div>
        <div className="tips-content">
          <ul>
            <li>
              <strong>Understand the data:</strong> Check what columns are available
            </li>
            <li>
              <strong>Think efficiency:</strong> Minimize shuffles and stages
            </li>
            <li>
              <strong>Test your code:</strong> Run it to see if it produces the expected output
            </li>
            <li>
              <strong>Check the Factory View:</strong> After running, see how Spark executes your code
            </li>
          </ul>
        </div>
      </div>

      {/* Execution Animation (when running) */}
      {isRunning && (
        <div className="execution-animation">
          <div className="animation-container">
            <div className="pulse-ring"></div>
            <div className="pulse-ring delay-1"></div>
            <div className="pulse-ring delay-2"></div>
            <div className="spark-icon">⚡</div>
          </div>
          <p className="animation-text">Executing your Spark code...</p>
          <div className="progress-bar">
            <div className="progress-fill"></div>
          </div>
        </div>
      )}

      {/* Result Summary (when completed) */}
      {result && !isRunning && (
        <div className="result-summary-card">
          <div className="card-header">
            <h4>📊 Quick Summary</h4>
          </div>
          <div className="result-metrics">
            <div className="metric-item">
              <span className="metric-label">Shuffles</span>
              <span className="metric-value">{result.metrics?.shuffles || 0}</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Stages</span>
              <span className="metric-value">{result.metrics?.stages || 0}</span>
            </div>
            {result.metrics?.broadcast_used && (
              <div className="metric-item success">
                <span className="metric-label">Broadcast</span>
                <span className="metric-value">✓ Used</span>
              </div>
            )}
            {result.metrics?.cache_used && (
              <div className="metric-item success">
                <span className="metric-label">Cache</span>
                <span className="metric-value">✓ Used</span>
              </div>
            )}
          </div>
          {result.hint && (
            <div className="hint-preview">
              <strong>💡 Hint:</strong> {result.hint}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ScenarioPanel;
