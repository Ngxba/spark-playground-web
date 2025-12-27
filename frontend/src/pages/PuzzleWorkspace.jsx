import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { puzzleService } from '../services/api';
import ScenarioPanel from '../components/ScenarioPanel';
import ReferencePanel from '../components/ReferencePanel';
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

  useEffect(() => {
    loadPuzzle();
    // Load last run result from sessionStorage
    const savedResult = sessionStorage.getItem(`puzzle_${puzzleId}_last_run`);
    if (savedResult) {
      try {
        setRunResult(JSON.parse(savedResult));
      } catch (err) {
        console.error('Failed to parse saved run result:', err);
      }
    }
  }, [puzzleId]);

  const loadPuzzle = async () => {
    try {
      setLoading(true);
      const data = await puzzleService.getPuzzle(puzzleId);
      setPuzzle(data);
      setCode(data.starter_code || '# Write your code here\n');
      setError(null);
    } catch (err) {
      setError('Failed to load puzzle. Please make sure the backend is running.');
      console.error('Error loading puzzle:', err);
    } finally {
      setLoading(false);
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

      const result = await puzzleService.runPuzzle(puzzleId, code);

      // Wait for animation to complete
      setTimeout(() => {
        setRunResult(result);
        setIsRunning(false);
        // Save result to sessionStorage
        sessionStorage.setItem(`puzzle_${puzzleId}_last_run`, JSON.stringify(result));
      }, 2000);
    } catch (err) {
      setIsRunning(false);
      console.error('Error running code:', err);
      alert('Failed to run code. Please check your code and try again.');
    }
  };

  const handleReset = () => {
    if (puzzle) {
      setCode(puzzle.starter_code || '# Write your code here\n');
      setRunResult(null);
      // Clear saved run result
      sessionStorage.removeItem(`puzzle_${puzzleId}_last_run`);
    }
  };

  const handleBack = () => {
    navigate('/');
  };

  if (loading) {
    return (
      <div className="workspace-container">
        <h2>Loading puzzle...</h2>
      </div>
    );
  }

  if (error || !puzzle) {
    return (
      <div className="workspace-container">
        <div className="error-message">
          <h2>Error</h2>
          <p>{error || 'Puzzle not found'}</p>
          <button onClick={handleBack} className="btn-primary">
            Back to Puzzles
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="workspace-container">
      {/* Header */}
      <div className="workspace-header">
        <button onClick={handleBack} className="btn-secondary back-button">
          ← Back
        </button>
        <div className="puzzle-info">
          <h2>{puzzle.title}</h2>
          <span className={`difficulty-badge difficulty-${puzzle.difficulty}`}>
            {puzzle.difficulty}
          </span>
        </div>
        <div className="puzzle-tags">
          {puzzle.tags.map((tag) => (
            <span key={tag} className="tag">
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Goal */}
      <div className="puzzle-goal">
        <h3>🎯 Goal</h3>
        <p>{puzzle.goal}</p>
      </div>

      {/* Main workspace */}
      <div className="workspace-content">
        {/* Left side - Scenario & Info */}
        <div className="visualization-panel">
          <ScenarioPanel
            puzzle={puzzle}
            isRunning={isRunning}
            result={runResult}
          />
          <ReferencePanel />
        </div>

        {/* Right side - Code Editor */}
        <div className="editor-panel">
          <div className="editor-header">
            <h3>Code Editor</h3>
            <div className="editor-actions">
              <button
                onClick={handleReset}
                className="btn-secondary"
                disabled={isRunning}
              >
                Reset
              </button>
              {runResult && (
                <button
                  onClick={() => navigate(`/puzzle/${puzzleId}/report`, { state: { result: runResult } })}
                  className="btn-info"
                  title="View the last run report"
                >
                  📊 View Last Report
                </button>
              )}
              <button
                onClick={handleRunCode}
                className="btn-success run-button"
                disabled={isRunning}
              >
                {isRunning ? '🏭 Running...' : '▶ Run Factory'}
              </button>
            </div>
          </div>

          <div className="editor-container">
            <Editor
              height="100%"
              defaultLanguage="python"
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 4,
              }}
            />
          </div>

          {runResult && runResult.stars > 0 && (
            <div className="quick-result">
              <div className="stars">
                {[...Array(3)].map((_, i) => (
                  <span
                    key={i}
                    className={i < runResult.stars ? 'star-filled' : 'star-empty'}
                  >
                    ★
                  </span>
                ))}
              </div>
              <button onClick={() => navigate(`/puzzle/${puzzleId}/report`, { state: { result: runResult } })} className="btn-primary">
                View Full Report
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PuzzleWorkspace;
