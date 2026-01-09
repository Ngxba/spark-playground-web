import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './StudyPlanPage.css';

function StudyPlanPage() {
  const navigate = useNavigate();
  const [expandedConcept, setExpandedConcept] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [animateCards, setAnimateCards] = useState(false);

  useEffect(() => {
    // Trigger card entrance animations
    setTimeout(() => setAnimateCards(true), 100);
  }, []);

  const concepts = [
    {
      id: 'partitions',
      title: 'Partitions',
      icon: '🔢',
      summary: 'Data split into chunks for parallel processing',
      details: 'Partitions are the fundamental unit of parallelism in Spark. Your data is divided into partitions, allowing multiple tasks to process different chunks simultaneously across the cluster.',
      tips: [
        'More partitions = more parallelism (up to your core count)',
        'Too many small partitions = overhead costs',
        'Too few large partitions = underutilized cluster',
        'Optimal: ~2-4 partitions per CPU core'
      ],
      puzzleCount: 8,
      status: 'in-progress',
      progress: 50
    },
    {
      id: 'stages',
      title: 'Stages',
      icon: '🏭',
      summary: 'Execution broken into sequential stages',
      details: 'Spark divides your job into stages. A new stage starts whenever data needs to be shuffled between nodes (like in joins or groupBy operations).',
      tips: [
        'Fewer stages = faster execution',
        'Stages run sequentially, not in parallel',
        'Shuffles create stage boundaries',
        'Optimize to minimize stage count'
      ],
      puzzleCount: 6,
      status: 'completed',
      progress: 100
    },
    {
      id: 'shuffles',
      title: 'Shuffles',
      icon: '🔀',
      summary: 'Expensive data movement across network',
      details: 'Shuffles occur when data needs to be redistributed across partitions (e.g., groupBy, join). This involves disk writes and network transfers.',
      tips: [
        'Shuffles write data to disk and move over network',
        'Most expensive operation in Spark',
        'Avoid with broadcast joins for small tables',
        'Use filters before shuffles to reduce data volume'
      ],
      puzzleCount: 7,
      status: 'in-progress',
      progress: 28
    },
    {
      id: 'parallelism',
      title: 'Parallelism',
      icon: '⚡',
      summary: 'Multiple tasks running simultaneously',
      details: 'With multiple CPU cores available, Spark can run multiple tasks in parallel. Parallelism is the key to Spark\'s performance advantages.',
      tips: [
        'Parallelism limited by CPU cores',
        'More partitions than cores = tasks queue up',
        'Fewer partitions than cores = wasted resources',
        'Balance partition count with available cores'
      ],
      puzzleCount: 5,
      status: 'not-started',
      progress: 0
    },
    {
      id: 'broadcast',
      title: 'Broadcast Joins',
      icon: '📡',
      summary: 'Efficient joins for small tables',
      details: 'Instead of shuffling both tables, broadcast the smaller one to all nodes. Each partition of the large table can then join locally without shuffling.',
      tips: [
        'Use for small tables (< 10MB typically)',
        'Eliminates shuffle on large table',
        'Dramatically faster than shuffle join',
        'Use .broadcast(small_df) to force it'
      ],
      puzzleCount: 4,
      status: 'not-started',
      progress: 0
    },
    {
      id: 'cache',
      title: 'Caching',
      icon: '💾',
      summary: 'Reuse computed data in memory',
      details: 'When using the same DataFrame multiple times, cache it in memory to avoid recomputing. Especially useful for iterative algorithms and repeated queries.',
      tips: [
        'Use .cache() or .persist() before reusing DataFrame',
        'Saves time on repeated computations',
        'Uses cluster memory - be mindful of size',
        'Unpersist when done to free memory'
      ],
      puzzleCount: 3,
      status: 'not-started',
      progress: 0
    }
  ];

  const filteredConcepts = concepts.filter(concept => {
    const matchesStatus = filterStatus === 'all' || concept.status === filterStatus;
    const matchesSearch = concept.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         concept.summary.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const overallProgress = Math.round(
    concepts.reduce((sum, c) => sum + c.progress, 0) / concepts.length
  );

  const statusCounts = {
    total: concepts.length,
    completed: concepts.filter(c => c.status === 'completed').length,
    'in-progress': concepts.filter(c => c.status === 'in-progress').length,
    'not-started': concepts.filter(c => c.status === 'not-started').length
  };

  const toggleConcept = (conceptId) => {
    setExpandedConcept(expandedConcept === conceptId ? null : conceptId);
  };

  const handleStartLearning = (conceptId) => {
    // Navigate to puzzles filtered by concept
    navigate(`/puzzles?concept=${conceptId}`);
  };

  const getStatusBadgeClass = (status) => {
    return `status-badge status-${status}`;
  };

  const getStatusLabel = (status) => {
    const labels = {
      'completed': 'Completed',
      'in-progress': 'In Progress',
      'not-started': 'Not Started'
    };
    return labels[status];
  };

  return (
    <div className="study-plan-page">
      {/* Animated Background Grid */}
      <div className="background-grid"></div>
      <div className="background-gradient"></div>

      <div className="study-plan-container">
        {/* Header Section */}
        <header className="study-header">
          <div className="header-content">
            <div className="header-text">
              <h1 className="header-title">
                <span className="title-icon">📚</span>
                STUDY PLAN
              </h1>
              <p className="header-subtitle">
                Master Apache Spark concepts through hands-on practice
              </p>
            </div>
            <div className="header-stats">
              <div className="overall-progress">
                <div className="progress-label">
                  <span>Overall Progress</span>
                  <span className="progress-percentage">{overallProgress}%</span>
                </div>
                <div className="progress-bar-container">
                  <div
                    className="progress-bar-fill"
                    style={{ width: `${overallProgress}%` }}
                  ></div>
                </div>
                <div className="progress-stats">
                  <span className="stat-item">
                    <span className="stat-icon">✓</span>
                    {statusCounts.completed} Completed
                  </span>
                  <span className="stat-item">
                    <span className="stat-icon">◐</span>
                    {statusCounts['in-progress']} In Progress
                  </span>
                  <span className="stat-item">
                    <span className="stat-icon">○</span>
                    {statusCounts['not-started']} Not Started
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Filter and Search Bar */}
        <div className="control-bar">
          <div className="filter-buttons">
            <button
              className={`filter-btn ${filterStatus === 'all' ? 'active' : ''}`}
              onClick={() => setFilterStatus('all')}
            >
              <span className="filter-icon">●</span>
              All ({statusCounts.total})
            </button>
            <button
              className={`filter-btn ${filterStatus === 'not-started' ? 'active' : ''}`}
              onClick={() => setFilterStatus('not-started')}
            >
              <span className="filter-icon">○</span>
              Not Started ({statusCounts['not-started']})
            </button>
            <button
              className={`filter-btn ${filterStatus === 'in-progress' ? 'active' : ''}`}
              onClick={() => setFilterStatus('in-progress')}
            >
              <span className="filter-icon">◐</span>
              In Progress ({statusCounts['in-progress']})
            </button>
            <button
              className={`filter-btn ${filterStatus === 'completed' ? 'active' : ''}`}
              onClick={() => setFilterStatus('completed')}
            >
              <span className="filter-icon">✓</span>
              Completed ({statusCounts.completed})
            </button>
          </div>

          <div className="search-container">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="search-input"
              placeholder="Search concepts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Concepts Grid */}
        <div className="concepts-grid">
          {filteredConcepts.map((concept, index) => (
            <div
              key={concept.id}
              className={`concept-card ${animateCards ? 'animate-in' : ''} ${expandedConcept === concept.id ? 'expanded' : ''}`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {/* Card Header */}
              <div className="card-header" onClick={() => toggleConcept(concept.id)}>
                <div className="card-icon-wrapper">
                  <span className="card-icon">{concept.icon}</span>
                  <div className="icon-glow"></div>
                </div>
                <div className="card-header-content">
                  <h3 className="card-title">{concept.title}</h3>
                  <p className="card-summary">{concept.summary}</p>
                </div>
                <button className="expand-btn">
                  {expandedConcept === concept.id ? '−' : '+'}
                </button>
              </div>

              {/* Status and Progress */}
              <div className="card-meta">
                <span className={getStatusBadgeClass(concept.status)}>
                  {getStatusLabel(concept.status)}
                </span>
                <span className="puzzle-count">
                  <span className="count-number">{concept.puzzleCount}</span> Puzzles
                </span>
              </div>

              <div className="card-progress-bar">
                <div
                  className="card-progress-fill"
                  style={{ width: `${concept.progress}%` }}
                ></div>
              </div>

              {/* Expanded Details */}
              {expandedConcept === concept.id && (
                <div className="card-details">
                  <div className="details-content">
                    <p className="details-description">{concept.details}</p>

                    <div className="details-tips">
                      <h4 className="tips-title">
                        <span className="tips-icon">💡</span>
                        Key Learning Points
                      </h4>
                      <ul className="tips-list">
                        {concept.tips.map((tip, idx) => (
                          <li key={idx} className="tip-item">
                            <span className="tip-bullet">▸</span>
                            {tip}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <button
                      className="start-learning-btn"
                      onClick={() => handleStartLearning(concept.id)}
                    >
                      <span className="btn-icon">⚡</span>
                      Start Learning
                      <span className="btn-arrow">→</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Empty State */}
        {filteredConcepts.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <h3 className="empty-title">No concepts found</h3>
            <p className="empty-text">
              Try adjusting your filters or search query
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default StudyPlanPage;
