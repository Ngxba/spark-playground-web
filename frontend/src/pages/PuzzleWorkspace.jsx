import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { puzzleService } from '../services/api';
import { runHistoryService } from '../services/runHistoryService';
import ScenarioPanel from '../components/ScenarioPanel';
import './PuzzleWorkspace.css';

function PuzzleWorkspace() {
  const { puzzleId } = useParams();
  const navigate = useNavigate();

  const [puzzle, setPuzzle] = useState(null);
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState(null);

  // UI State
  const [leftTab, setLeftTab] = useState('description');
  const [bottomTab, setBottomTab] = useState('testcases');
  const [language, setLanguage] = useState('python');
  const [showVisualization, setShowVisualization] = useState(true);
  const [splitPosition, setSplitPosition] = useState(50);
  const [timer, setTimer] = useState(0);
  const [isTimerRunning, setIsTimerRunning] = useState(false);

  // Submissions State
  const [submissions, setSubmissions] = useState([]);
  const [loadingSubmissions, setLoadingSubmissions] = useState(false);
  const [submissionsError, setSubmissionsError] = useState(null);

  const isDragging = useRef(false);
  const timerInterval = useRef(null);

  useEffect(() => {
    loadPuzzle();
    const savedResult = sessionStorage.getItem(`puzzle_${puzzleId}_last_run`);
    if (savedResult) {
      try {
        setRunResult(JSON.parse(savedResult));
      } catch (err) {
        console.error('Failed to parse saved run result:', err);
      }
    }

    // Start timer
    setIsTimerRunning(true);

    return () => {
      if (timerInterval.current) {
        clearInterval(timerInterval.current);
      }
    };
  }, [puzzleId]);

  // Load submissions when submissions tab is selected
  useEffect(() => {
    if (leftTab === 'submissions') {
      loadSubmissions();
    }
  }, [leftTab]);

  useEffect(() => {
    if (isTimerRunning) {
      timerInterval.current = setInterval(() => {
        setTimer(t => t + 1);
      }, 1000);
    } else {
      if (timerInterval.current) {
        clearInterval(timerInterval.current);
      }
    }

    return () => {
      if (timerInterval.current) {
        clearInterval(timerInterval.current);
      }
    };
  }, [isTimerRunning]);

  const loadPuzzle = async () => {
    try {
      setLoading(true);
      const data = await puzzleService.getPuzzle(puzzleId);
      setPuzzle(data);
      setCode(data.starter_code || '# Write your PySpark code here\nfrom pyspark.sql import SparkSession\n\n');
      setError(null);
    } catch (err) {
      setError('Failed to load puzzle. Please make sure the backend is running.');
      console.error('Error loading puzzle:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSubmissions = async () => {
    setLoadingSubmissions(true);
    setSubmissionsError(null);
    try {
      const data = await runHistoryService.getPuzzleRuns(puzzleId);
      setSubmissions(data);
    } catch (error) {
      console.error('Error loading submissions:', error);
      setSubmissionsError('Failed to load submission history.');
    } finally {
      setLoadingSubmissions(false);
    }
  };

  const handleViewSubmission = async (runId) => {
    try {
      const runDetail = await runHistoryService.getRunDetail(runId);
      navigate(`/puzzle/${puzzleId}/report`, {
        state: { result: runDetail }
      });
    } catch (error) {
      console.error('Error loading run detail:', error);
      alert('Failed to load submission details');
    }
  };

  const handleRunCode = async () => {
    if (!code.trim()) {
      alert('Please write some code first!');
      return;
    }

    try {
      setIsRunning(true);
      setRunResult(null);
      setBottomTab('results');

      const result = await puzzleService.runPuzzle(puzzleId, code);

      setTimeout(() => {
        setRunResult(result);
        setIsRunning(false);
        sessionStorage.setItem(`puzzle_${puzzleId}_last_run`, JSON.stringify(result));
        // Reload submissions if on submissions tab
        if (leftTab === 'submissions') {
          loadSubmissions();
        }
      }, 2000);
    } catch (err) {
      setIsRunning(false);
      console.error('Error running code:', err);
      setRunResult({
        success: false,
        error: err.message || 'Failed to run code. Please check your code and try again.'
      });
    }
  };

  const handleSubmit = async () => {
    if (!code.trim()) {
      alert('Please write some code first!');
      return;
    }

    await handleRunCode();
    // After running, if successful, navigate to report
    setTimeout(() => {
      if (runResult && runResult.success) {
        navigate(`/puzzle/${puzzleId}/report`, { state: { result: runResult } });
      }
    }, 2500);
  };

  const handleReset = () => {
    if (puzzle) {
      setCode(puzzle.starter_code || '# Write your PySpark code here\nfrom pyspark.sql import SparkSession\n\n');
      setRunResult(null);
      setTimer(0);
      sessionStorage.removeItem(`puzzle_${puzzleId}_last_run`);
    }
  };

  const handleMouseDown = () => {
    isDragging.current = true;
  };

  const handleMouseMove = (e) => {
    if (!isDragging.current) return;

    const container = document.querySelector('.workspace-split-container');
    if (container) {
      const rect = container.getBoundingClientRect();
      const newPosition = ((e.clientX - rect.left) / rect.width) * 100;
      setSplitPosition(Math.min(Math.max(newPosition, 20), 80));
    }
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="workspace-modern">
        <div className="workspace-loading">
          <div className="loading-spinner"></div>
          <h2>Initializing Spark Environment...</h2>
        </div>
      </div>
    );
  }

  if (error || !puzzle) {
    return (
      <div className="workspace-modern">
        <div className="workspace-error">
          <div className="error-icon">⚠️</div>
          <h2>Connection Error</h2>
          <p>{error || 'Puzzle not found'}</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            Back to Problems
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="workspace-modern">
      {/* Top Action Bar */}
      <div className="workspace-action-bar">
        <button onClick={() => navigate('/')} className="action-back-btn">
          <span>←</span>
          Problems
        </button>

        <div className="problem-title-section">
          <h1 className="problem-title">{puzzle.title}</h1>
          <span className={`difficulty-badge difficulty-${puzzle.difficulty}`}>
            {puzzle.difficulty}
          </span>
        </div>

        <div className="action-bar-controls">
          <div className="timer-display">
            <span className="timer-icon">⏱️</span>
            <span className="timer-value">{formatTime(timer)}</span>
          </div>

          <button onClick={handleReset} className="action-btn action-btn-secondary" disabled={isRunning}>
            <span>↻</span>
            Reset
          </button>

          <button onClick={handleRunCode} className="action-btn action-btn-run" disabled={isRunning}>
            <span>▶</span>
            {isRunning ? 'Running...' : 'Run Code'}
          </button>

          <button onClick={handleSubmit} className="action-btn action-btn-submit" disabled={isRunning}>
            <span>✓</span>
            Submit
          </button>
        </div>
      </div>

      {/* Split Panel Container */}
      <div className="workspace-split-container">
        {/* Left Panel - Problem Description */}
        <div className="workspace-left-panel" style={{ width: `${splitPosition}%` }}>
          <div className="panel-tabs">
            <button
              className={`panel-tab ${leftTab === 'description' ? 'active' : ''}`}
              onClick={() => setLeftTab('description')}
            >
              Description
            </button>
            <button
              className={`panel-tab ${leftTab === 'hints' ? 'active' : ''}`}
              onClick={() => setLeftTab('hints')}
            >
              Hints
            </button>
            <button
              className={`panel-tab ${leftTab === 'solution' ? 'active' : ''}`}
              onClick={() => setLeftTab('solution')}
            >
              Solution
            </button>
            <button
              className={`panel-tab ${leftTab === 'submissions' ? 'active' : ''}`}
              onClick={() => setLeftTab('submissions')}
            >
              Submissions
            </button>
          </div>

          <div className="panel-content">
            {leftTab === 'description' && (
              <div className="description-content">
                <div className="problem-section">
                  <h3 className="section-title">🎯 Goal</h3>
                  <p className="section-text">{puzzle.goal}</p>
                </div>

                <div className="problem-section">
                  <h3 className="section-title">📝 Description</h3>
                  <p className="section-text">{puzzle.description}</p>
                </div>

                <div className="problem-section">
                  <h3 className="section-title">🏷️ Topics</h3>
                  <div className="problem-tags">
                    {puzzle.tags.map((tag) => (
                      <span key={tag} className="tag">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="problem-section">
                  <h3 className="section-title">💡 Example</h3>
                  <div className="example-box">
                    <div className="example-label">Input:</div>
                    <pre className="example-code">Sample Spark DataFrame with transactions</pre>
                    <div className="example-label">Output:</div>
                    <pre className="example-code">Transformed DataFrame with aggregated results</pre>
                  </div>
                </div>
              </div>
            )}

            {leftTab === 'hints' && (
              <div className="hints-content">
                <div className="hint-card">
                  <div className="hint-header">
                    <span className="hint-icon">💡</span>
                    <span className="hint-title">Hint 1</span>
                  </div>
                  <p className="hint-text">Think about which Spark transformation is best suited for this operation.</p>
                </div>
                <div className="hint-card">
                  <div className="hint-header">
                    <span className="hint-icon">💡</span>
                    <span className="hint-title">Hint 2</span>
                  </div>
                  <p className="hint-text">Consider using groupBy and aggregation functions.</p>
                </div>
                <div className="hint-card locked">
                  <div className="hint-header">
                    <span className="hint-icon">🔒</span>
                    <span className="hint-title">Hint 3 (Locked)</span>
                  </div>
                  <p className="hint-text">Unlock by attempting the puzzle first</p>
                </div>
              </div>
            )}

            {leftTab === 'solution' && (
              <div className="solution-content">
                <div className="solution-locked">
                  <div className="locked-icon">🔒</div>
                  <h3>Solution Locked</h3>
                  <p>Complete the puzzle to unlock the solution</p>
                  <button className="btn-secondary">Unlock with Premium</button>
                </div>
              </div>
            )}

            {leftTab === 'submissions' && (
              <div className="submissions-content">
                {loadingSubmissions ? (
                  <div className="submissions-loading">
                    <div className="loading-spinner"></div>
                    <h3>Loading submission history...</h3>
                  </div>
                ) : submissionsError ? (
                  <div className="submissions-error">
                    <div className="error-icon">⚠️</div>
                    <h3>Failed to Load</h3>
                    <p>{submissionsError}</p>
                    <button onClick={loadSubmissions} className="btn-secondary">
                      Try Again
                    </button>
                  </div>
                ) : submissions.length === 0 ? (
                  <div className="no-submissions">
                    <div className="no-submissions-icon">📋</div>
                    <h3>No Submissions Yet</h3>
                    <p>Your submission history will appear here after you run your code</p>
                  </div>
                ) : (
                  <div className="submissions-list">
                    <div className="submissions-header">
                      <h3>Submission History</h3>
                      <p className="submissions-count">{submissions.length} total submissions</p>
                    </div>
                    <div className="submissions-table-wrapper">
                      <table className="submissions-table">
                        <thead>
                          <tr>
                            <th>Status</th>
                            <th>Date & Time</th>
                            <th>Rating</th>
                            <th>Details</th>
                          </tr>
                        </thead>
                        <tbody>
                          {submissions.map((submission, index) => (
                            <tr
                              key={submission.id}
                              className="submission-row"
                              onClick={() => handleViewSubmission(submission.id)}
                              style={{ animationDelay: `${index * 0.05}s` }}
                            >
                              <td>
                                <div className={`submission-status ${submission.is_correct ? 'success' : 'error'}`}>
                                  <span className="status-icon">
                                    {submission.is_correct ? '✅' : '❌'}
                                  </span>
                                  <span className="status-text">
                                    {submission.is_correct ? 'Passed' : 'Failed'}
                                  </span>
                                </div>
                              </td>
                              <td>
                                <div className="submission-date">
                                  <div className="date-main">
                                    {new Date(submission.created_at).toLocaleDateString()}
                                  </div>
                                  <div className="date-time">
                                    {new Date(submission.created_at).toLocaleTimeString()}
                                  </div>
                                </div>
                              </td>
                              <td>
                                <div className="submission-stars">
                                  {submission.is_correct ? (
                                    <>
                                      {[...Array(3)].map((_, i) => (
                                        <span
                                          key={i}
                                          className={`star ${i < (submission.stars || 0) ? 'filled' : 'empty'}`}
                                        >
                                          ★
                                        </span>
                                      ))}
                                    </>
                                  ) : (
                                    <span className="no-stars">-</span>
                                  )}
                                </div>
                              </td>
                              <td>
                                <div className="submission-details">
                                  {submission.error_message ? (
                                    <span className="detail-error">
                                      <span className="detail-icon">⚠️</span>
                                      Error
                                    </span>
                                  ) : (
                                    <span className="detail-view">
                                      <span className="detail-icon">📊</span>
                                      View Report
                                    </span>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Resizable Divider */}
        <div className="workspace-divider" onMouseDown={handleMouseDown}>
          <div className="divider-handle">
            <div className="divider-dots"></div>
          </div>
        </div>

        {/* Right Panel - Code Editor */}
        <div className="workspace-right-panel" style={{ width: `${100 - splitPosition}%` }}>
          <div className="editor-top-bar">
            <select
              className="language-selector"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="python">PySpark</option>
              <option value="scala">Scala</option>
            </select>

            <button
              className="visualization-toggle"
              onClick={() => setShowVisualization(!showVisualization)}
            >
              <span>{showVisualization ? '🔼' : '🔽'}</span>
              Factory View
            </button>
          </div>

          <div className="editor-main-container">
            <div className="monaco-editor-wrapper">
              <Editor
                height="100%"
                defaultLanguage={language}
                theme="vs-dark"
                value={code}
                onChange={(value) => setCode(value || '')}
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  fontFamily: "'JetBrains Mono', 'Courier New', monospace",
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  tabSize: 4,
                  renderWhitespace: 'selection',
                  bracketPairColorization: { enabled: true },
                }}
              />
            </div>

            {/* Bottom Tabs Panel */}
            <div className="editor-bottom-panel">
              <div className="bottom-panel-tabs">
                <button
                  className={`bottom-tab ${bottomTab === 'testcases' ? 'active' : ''}`}
                  onClick={() => setBottomTab('testcases')}
                >
                  Test Cases
                </button>
                <button
                  className={`bottom-tab ${bottomTab === 'results' ? 'active' : ''}`}
                  onClick={() => setBottomTab('results')}
                >
                  Results
                  {runResult && (
                    <span className={`result-indicator ${runResult.success ? 'success' : 'error'}`}>
                      {runResult.success ? '✓' : '✗'}
                    </span>
                  )}
                </button>
                <button
                  className={`bottom-tab ${bottomTab === 'console' ? 'active' : ''}`}
                  onClick={() => setBottomTab('console')}
                >
                  Console
                </button>
              </div>

              <div className="bottom-panel-content">
                {bottomTab === 'testcases' && (
                  <div className="testcases-panel">
                    <div className="testcase-item">
                      <div className="testcase-header">
                        <span className="testcase-label">Test Case 1</span>
                        <span className="testcase-status pending">Pending</span>
                      </div>
                      <div className="testcase-data">
                        <div className="testcase-input">
                          <strong>Input:</strong> Sample DataFrame
                        </div>
                        <div className="testcase-expected">
                          <strong>Expected:</strong> Aggregated results
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {bottomTab === 'results' && (
                  <div className="results-panel">
                    {isRunning ? (
                      <div className="running-state">
                        <div className="running-animation">
                          <div className="factory-spinner"></div>
                        </div>
                        <h3>Running Spark Job...</h3>
                        <p>Processing your transformation pipeline</p>
                      </div>
                    ) : runResult ? (
                      <div className={`result-display ${runResult.success ? 'success' : 'error'}`}>
                        <div className="result-header">
                          <div className="result-icon">
                            {runResult.success ? '✅' : '❌'}
                          </div>
                          <div className="result-summary">
                            <h3>{runResult.success ? 'All Tests Passed!' : 'Tests Failed'}</h3>
                            <p>{runResult.message || 'Check the output below'}</p>
                          </div>
                        </div>

                        {runResult.stars > 0 && (
                          <div className="result-stars">
                            {[...Array(3)].map((_, i) => (
                              <span
                                key={i}
                                className={`star ${i < runResult.stars ? 'filled' : 'empty'}`}
                              >
                                ★
                              </span>
                            ))}
                          </div>
                        )}

                        {runResult.success && (
                          <button
                            onClick={() => navigate(`/puzzle/${puzzleId}/report`, { state: { result: runResult } })}
                            className="btn-primary"
                          >
                            View Full Report
                          </button>
                        )}

                        {runResult.error && (
                          <div className="error-output">
                            <pre>{runResult.error}</pre>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="no-results">
                        <div className="no-results-icon">📊</div>
                        <h3>No Results Yet</h3>
                        <p>Run your code to see results</p>
                      </div>
                    )}
                  </div>
                )}

                {bottomTab === 'console' && (
                  <div className="console-panel">
                    <div className="console-output">
                      <div className="console-line">
                        <span className="console-prompt">$</span>
                        <span className="console-text">Spark Console Ready</span>
                      </div>
                      {runResult && runResult.console_output && (
                        <div className="console-line">
                          <pre>{runResult.console_output}</pre>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Collapsible Factory Visualization */}
      {showVisualization && (
        <div className="factory-visualization-panel">
          <div className="visualization-header">
            <h3>🏭 Factory Data Flow</h3>
            <button onClick={() => setShowVisualization(false)} className="close-viz-btn">
              ✕
            </button>
          </div>
          <div className="visualization-content">
            <ScenarioPanel
              puzzle={puzzle}
              isRunning={isRunning}
              result={runResult}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default PuzzleWorkspace;
