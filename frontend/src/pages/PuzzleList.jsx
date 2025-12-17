import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { puzzleService } from '../services/api';
import './PuzzleList.css';

function PuzzleList() {
  const [puzzles, setPuzzles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadPuzzles();
  }, []);

  const loadPuzzles = async () => {
    try {
      setLoading(true);
      const data = await puzzleService.getAllPuzzles();
      setPuzzles(data);
      setError(null);
    } catch (err) {
      setError('Failed to load puzzles. Please make sure the backend is running.');
      console.error('Error loading puzzles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePuzzleClick = (puzzleId) => {
    navigate(`/puzzle/${puzzleId}`);
  };

  if (loading) {
    return (
      <div className="puzzle-list-container">
        <h2>Loading puzzles...</h2>
      </div>
    );
  }

  if (error) {
    return (
      <div className="puzzle-list-container">
        <div className="error-message">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={loadPuzzles} className="btn-primary">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="puzzle-list-container">
      <h2>Choose a Puzzle</h2>
      <p className="subtitle">
        Select a puzzle to start learning Spark concepts through hands-on coding challenges.
      </p>

      <div className="puzzle-grid">
        {puzzles.map((puzzle) => (
          <div
            key={puzzle.id}
            className="puzzle-card"
            onClick={() => handlePuzzleClick(puzzle.id)}
          >
            <div className="puzzle-card-header">
              <h3>{puzzle.title}</h3>
              <span className={`difficulty-badge difficulty-${puzzle.difficulty}`}>
                {puzzle.difficulty}
              </span>
            </div>

            <p className="puzzle-description">{puzzle.description}</p>

            <div className="puzzle-tags">
              {puzzle.tags.map((tag) => (
                <span key={tag} className="tag">
                  {tag}
                </span>
              ))}
            </div>

            <button className="btn-primary" style={{ marginTop: 'auto' }}>
              Start Puzzle
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PuzzleList;
