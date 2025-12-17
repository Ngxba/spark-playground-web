import { useState, useEffect } from 'react';
import './FactoryVisualization.css';

function FactoryVisualization({ puzzle, isRunning, result }) {
  const [animationState, setAnimationState] = useState('idle'); // idle, running, complete

  useEffect(() => {
    if (isRunning) {
      setAnimationState('running');
      // Simulate animation duration
      const timer = setTimeout(() => {
        setAnimationState('complete');
      }, 2000);
      return () => clearTimeout(timer);
    } else {
      setAnimationState('idle');
    }
  }, [isRunning]);

  if (!puzzle) return null;

  const config = puzzle.visualization_config || {};
  const inputConveyors = config.input_conveyors || 1;
  const outputConveyors = config.output_conveyors || 1;
  const transformation = config.transformation || 'transform';

  return (
    <div className="factory-visualization">
      <h3>Factory View</h3>
      <p className="factory-description">{puzzle.scenario}</p>

      <svg className="factory-svg" viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg">
        {/* Input Conveyors */}
        <g className="input-section">
          {[...Array(inputConveyors)].map((_, i) => {
            const y = 100 + i * (200 / Math.max(inputConveyors, 1));
            return (
              <g key={`input-${i}`}>
                {/* Conveyor belt */}
                <rect
                  x="20"
                  y={y}
                  width="200"
                  height="40"
                  fill="#ddd"
                  stroke="#999"
                  strokeWidth="2"
                  rx="4"
                />
                <text x="120" y={y + 25} textAnchor="middle" fontSize="12" fill="#666">
                  Input {i + 1}
                </text>
                {/* Data boxes */}
                {animationState !== 'idle' && (
                  <>
                    <rect
                      x="40"
                      y={y + 10}
                      width="20"
                      height="20"
                      fill="#667eea"
                      className={animationState === 'running' ? 'moving-box' : ''}
                    />
                    <rect
                      x="80"
                      y={y + 10}
                      width="20"
                      height="20"
                      fill="#764ba2"
                      className={animationState === 'running' ? 'moving-box' : ''}
                      style={{ animationDelay: '0.3s' }}
                    />
                    <rect
                      x="120"
                      y={y + 10}
                      width="20"
                      height="20"
                      fill="#667eea"
                      className={animationState === 'running' ? 'moving-box' : ''}
                      style={{ animationDelay: '0.6s' }}
                    />
                  </>
                )}
              </g>
            );
          })}
        </g>

        {/* Transformation Machine */}
        <g className="transformation-section">
          <rect
            x="320"
            y="120"
            width="160"
            height="160"
            fill="#fff"
            stroke="#667eea"
            strokeWidth="3"
            rx="8"
          />
          <text x="400" y="170" textAnchor="middle" fontSize="14" fontWeight="bold" fill="#667eea">
            {transformation.toUpperCase()}
          </text>
          <text x="400" y="190" textAnchor="middle" fontSize="11" fill="#666">
            MACHINE
          </text>

          {/* Show shuffle indicator if applicable */}
          {result && result.metrics && result.metrics.shuffles > 0 && (
            <g>
              <circle cx="400" cy="230" r="30" fill="#fff3cd" stroke="#ffc107" strokeWidth="2" />
              <text x="400" y="235" textAnchor="middle" fontSize="20">
                🔁
              </text>
              <text x="400" y="255" textAnchor="middle" fontSize="10" fill="#856404">
                Shuffle
              </text>
            </g>
          )}

          {/* Show broadcast indicator if applicable */}
          {result && result.metrics && result.metrics.broadcast_used && (
            <g>
              <circle cx="400" cy="230" r="30" fill="#d4edda" stroke="#28a745" strokeWidth="2" />
              <text x="400" y="235" textAnchor="middle" fontSize="20">
                📡
              </text>
              <text x="400" y="255" textAnchor="middle" fontSize="10" fill="#155724">
                Broadcast
              </text>
            </g>
          )}

          {/* Show cache indicator if applicable */}
          {result && result.metrics && result.metrics.cache_used && (
            <g>
              <rect x="380" y="85" width="40" height="30" fill="#d4edda" stroke="#28a745" strokeWidth="2" rx="4" />
              <text x="400" y="105" textAnchor="middle" fontSize="18">
                💾
              </text>
            </g>
          )}
        </g>

        {/* Output Conveyors */}
        <g className="output-section">
          {[...Array(outputConveyors)].map((_, i) => {
            const y = 100 + i * (200 / Math.max(outputConveyors, 1));
            return (
              <g key={`output-${i}`}>
                {/* Conveyor belt */}
                <rect
                  x="580"
                  y={y}
                  width="200"
                  height="40"
                  fill="#ddd"
                  stroke="#999"
                  strokeWidth="2"
                  rx="4"
                />
                <text x="680" y={y + 25} textAnchor="middle" fontSize="12" fill="#666">
                  Output {i + 1}
                </text>
                {/* Result boxes */}
                {animationState === 'complete' && result && result.correct && (
                  <>
                    <rect
                      x="600"
                      y={y + 10}
                      width="20"
                      height="20"
                      fill="#28a745"
                      className="result-box"
                    />
                    <rect
                      x="640"
                      y={y + 10}
                      width="20"
                      height="20"
                      fill="#28a745"
                      className="result-box"
                      style={{ animationDelay: '0.2s' }}
                    />
                    <rect
                      x="680"
                      y={y + 10}
                      width="20"
                      height="20"
                      fill="#28a745"
                      className="result-box"
                      style={{ animationDelay: '0.4s' }}
                    />
                  </>
                )}
                {animationState === 'complete' && result && !result.correct && (
                  <text x="680" y={y + 25} textAnchor="middle" fontSize="20" fill="#d32f2f">
                    ❌
                  </text>
                )}
              </g>
            );
          })}
        </g>

        {/* Connection lines */}
        <line x1="220" y1="120" x2="320" y2="150" stroke="#999" strokeWidth="2" />
        {inputConveyors > 1 && (
          <line x1="220" y1="200" x2="320" y2="230" stroke="#999" strokeWidth="2" />
        )}
        <line x1="480" y1="150" x2="580" y2="120" stroke="#999" strokeWidth="2" />
        {outputConveyors > 1 && (
          <line x1="480" y1="230" x2="580" y2="200" stroke="#999" strokeWidth="2" />
        )}
      </svg>

      {/* Status indicator */}
      <div className="factory-status">
        {animationState === 'idle' && <span className="status-idle">Ready to run</span>}
        {animationState === 'running' && (
          <span className="status-running">🏭 Factory running...</span>
        )}
        {animationState === 'complete' && result && (
          <span className={result.correct ? 'status-success' : 'status-error'}>
            {result.correct ? '✅ Complete!' : '❌ Output incorrect'}
          </span>
        )}
      </div>
    </div>
  );
}

export default FactoryVisualization;
