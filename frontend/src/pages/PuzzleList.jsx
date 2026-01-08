import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { puzzleService } from '../services/api';
import './PuzzleList.css';

function PuzzleList() {
  const [puzzles, setPuzzles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const heroBanners = [
    {
      id: 1,
      title: '2025 Spark Challenge',
      subtitle: 'Master Data Processing',
      theme: 'primary',
      icon: '⚡',
      action: 'View Puzzles'
    },
    {
      id: 2,
      title: 'New Quest',
      subtitle: 'Turn coding practice into an epic adventure',
      theme: 'secondary',
      icon: '🎯',
      label: 'NEW',
      action: 'Begin Now'
    },
    {
      id: 3,
      title: 'DataFrame Challenge',
      subtitle: '30 Days of Spark Mastery',
      theme: 'accent',
      icon: '🔥',
      label: 'BEGINNER FRIENDLY',
      action: 'Start Learning'
    },
  ];

  const topics = [
    { id: 'all', label: 'All Topics', icon: '📚', count: 0 },
    { id: 'transformations', label: 'Transformations', icon: '🔄', count: 2076 },
    { id: 'actions', label: 'Actions', icon: '⚡', count: 842 },
    { id: 'joins', label: 'Joins', icon: '🔗', count: 768 },
    { id: 'aggregations', label: 'Aggregations', icon: '📊', count: 647 },
    { id: 'window-functions', label: 'Window Functions', icon: '🪟', count: 636 },
    { id: 'partitioning', label: 'Partitioning', icon: '📦', count: 493 },
    { id: 'caching', label: 'Caching', icon: '💾', count: 454 },
  ];

  useEffect(() => {
    loadPuzzles();
  }, []);

  const loadPuzzles = async () => {
    try {
      setLoading(true);
      const data = await puzzleService.getAllPuzzles();
      setPuzzles(data);
      // Update 'all' topic count
      topics[0].count = data.length;
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

  const filteredPuzzles = puzzles.filter(puzzle => {
    const matchesSearch = puzzle.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         puzzle.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTopic = selectedTopic === 'all' || puzzle.tags.includes(selectedTopic);
    return matchesSearch && matchesTopic;
  });

  if (loading) {
    return (
      <div className="puzzle-list-modern">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <h2>Loading Spark Challenges...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="puzzle-list-modern">
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <h2>Connection Error</h2>
          <p>{error}</p>
          <button onClick={loadPuzzles} className="btn-primary">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="puzzle-list-modern">
      {/* Hero Banners */}
      <div className="hero-banners">
        {heroBanners.map((banner) => (
          <div key={banner.id} className={`hero-banner hero-banner-${banner.theme}`}>
            <div className="hero-banner-content">
              <div className="hero-banner-icon">{banner.icon}</div>
              <div className="hero-banner-text">
                <h3 className="hero-banner-title">{banner.title}</h3>
                <p className="hero-banner-subtitle">{banner.subtitle}</p>
              </div>
              {banner.label && (
                <span className="hero-banner-label">{banner.label}</span>
              )}
            </div>
            <button className="hero-banner-action">{banner.action}</button>
          </div>
        ))}
      </div>

      {/* Topic Filters */}
      <div className="topic-filters-section">
        <div className="topic-filters">
          <button
            className={`topic-filter ${selectedTopic === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedTopic('all')}
          >
            <span className="topic-filter-icon">📚</span>
            <span className="topic-filter-label">All Topics</span>
          </button>
          {topics.slice(1).map((topic) => (
            <button
              key={topic.id}
              className={`topic-filter ${selectedTopic === topic.id ? 'active' : ''}`}
              onClick={() => setSelectedTopic(topic.id)}
            >
              <span className="topic-filter-icon">{topic.icon}</span>
              <span className="topic-filter-label">{topic.label}</span>
              <span className="topic-filter-count">{topic.count}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Search and Controls */}
      <div className="puzzle-controls">
        <div className="puzzle-search">
          <span className="puzzle-search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search puzzles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="puzzle-search-input"
          />
        </div>
        <div className="puzzle-actions">
          <button className="puzzle-filter-btn">
            <span>⚙️</span>
            Filters
          </button>
          <button className="puzzle-sort-btn">
            <span>↕️</span>
            Sort
          </button>
        </div>
        <div className="puzzle-stats">
          <span className="puzzle-stats-icon">🎯</span>
          <span className="puzzle-stats-text">
            {filteredPuzzles.filter(p => p.completed).length}/{filteredPuzzles.length} Solved
          </span>
          <button className="puzzle-stats-btn">✓</button>
        </div>
      </div>

      {/* Puzzles Table */}
      <div className="puzzles-table-container">
        <table className="puzzles-table">
          <thead>
            <tr>
              <th className="col-status">Status</th>
              <th className="col-title">Title</th>
              <th className="col-acceptance">Completion</th>
              <th className="col-difficulty">Difficulty</th>
              <th className="col-tags">Topics</th>
            </tr>
          </thead>
          <tbody>
            {filteredPuzzles.map((puzzle, index) => (
              <tr
                key={puzzle.id}
                className="puzzle-row"
                onClick={() => handlePuzzleClick(puzzle.id)}
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <td className="col-status">
                  <div className={`status-indicator ${puzzle.completed ? 'completed' : 'pending'}`}>
                    {puzzle.completed ? '✓' : '○'}
                  </div>
                </td>
                <td className="col-title">
                  <div className="puzzle-title-cell">
                    <span className="puzzle-number">{index + 1}.</span>
                    <span className="puzzle-title-text">{puzzle.title}</span>
                  </div>
                </td>
                <td className="col-acceptance">
                  <div className="acceptance-cell">
                    <span className="acceptance-value">{Math.floor(Math.random() * 30 + 40)}%</span>
                    <div className="acceptance-bar">
                      <div
                        className="acceptance-fill"
                        style={{ width: `${Math.floor(Math.random() * 30 + 40)}%` }}
                      ></div>
                    </div>
                  </div>
                </td>
                <td className="col-difficulty">
                  <span className={`difficulty-badge difficulty-${puzzle.difficulty}`}>
                    {puzzle.difficulty}
                  </span>
                </td>
                <td className="col-tags">
                  <div className="puzzle-tags-cell">
                    {puzzle.tags.slice(0, 2).map((tag) => (
                      <span key={tag} className="tag">
                        {tag}
                      </span>
                    ))}
                    {puzzle.tags.length > 2 && (
                      <span className="tag tag-more">+{puzzle.tags.length - 2}</span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default PuzzleList;
