import { useState, useEffect } from 'react';
import { runHistoryService } from '../services/runHistoryService';
import './RunHistory.css';

function RunHistory({ puzzleId, onSelectRun }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadRuns();
  }, [puzzleId]);

  const loadRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = puzzleId
        ? await runHistoryService.getPuzzleRuns(puzzleId)
        : await runHistoryService.getAllRuns();
      setRuns(data);
    } catch (error) {
      console.error('Error loading runs:', error);
      setError('Failed to load run history. Make sure PostgreSQL is running.');
    }
    setLoading(false);
  };

  const handleRowClick = async (runId) => {
    try {
      const runDetail = await runHistoryService.getRunDetail(runId);
      onSelectRun(runDetail);
    } catch (error) {
      console.error('Error loading run detail:', error);
      alert('Failed to load run details');
    }
  };

  if (loading) {
    return (
      <div className="run-history">
        <p>Loading run history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="run-history">
        <div className="error-message">
          <p>{error}</p>
          <button onClick={loadRuns}>Retry</button>
        </div>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="run-history">
        <div className="empty-state">
          <h3>No runs yet</h3>
          <p>Run some code to see your execution history here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="run-history">
      <div className="run-history-header">
        <h3>Run History {puzzleId && `- ${puzzleId}`}</h3>
        <p className="run-count">Showing {runs.length} recent runs</p>
      </div>
      <table className="run-history-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Puzzle</th>
            <th>Result</th>
            <th>Stars</th>
            <th>Error</th>
          </tr>
        </thead>
        <tbody>
          {runs.map(run => (
            <tr
              key={run.id}
              onClick={() => handleRowClick(run.id)}
              className="clickable"
            >
              <td>{new Date(run.created_at).toLocaleString()}</td>
              <td>{run.puzzle_id}</td>
              <td className={run.is_correct ? 'success' : 'error'}>
                {run.is_correct ? '✅ Correct' : '❌ Incorrect'}
              </td>
              <td>{'⭐'.repeat(run.stars || 0)}</td>
              <td>{run.error_message ? '⚠️ Error' : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default RunHistory;
