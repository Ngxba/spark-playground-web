import { useState, useEffect } from 'react';
import { authService } from '../services/api';
import { useNavigate } from 'react-router-dom';
import './ProfilePage.css';

function ProfilePage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    if (!currentUser) {
      navigate('/signin');
      return;
    }

    // Simulate loading user data
    setTimeout(() => {
      setUser(currentUser);
      setLoading(false);
    }, 500);
  }, [navigate]);

  if (loading) {
    return (
      <div className="profile-loading">
        <div className="loading-spinner"></div>
        <p>LOADING PROFILE DATA...</p>
      </div>
    );
  }

  const stats = {
    puzzlesSolved: 12,
    totalPuzzles: 50,
    streak: 0,
    stars: 0,
    rank: 'Beginner',
    totalRuns: 47,
    bestTime: '2.3s',
    efficiency: 87
  };

  const achievements = [
    { id: 1, name: 'First Steps', description: 'Complete your first puzzle', icon: '🎯', unlocked: true, rarity: 'common' },
    { id: 2, name: 'Speed Demon', description: 'Solve a puzzle in under 3 seconds', icon: '⚡', unlocked: false, rarity: 'rare' },
    { id: 3, name: 'Efficiency Expert', description: 'Achieve 95% efficiency rating', icon: '💎', unlocked: false, rarity: 'epic' },
    { id: 4, name: 'Week Warrior', description: 'Maintain a 7-day streak', icon: '🔥', unlocked: false, rarity: 'rare' },
    { id: 5, name: 'Master Mind', description: 'Solve 25 hard puzzles', icon: '🧠', unlocked: false, rarity: 'legendary' },
    { id: 6, name: 'Data Wizard', description: 'Master all shuffle operations', icon: '🪄', unlocked: false, rarity: 'epic' }
  ];

  const recentActivity = [
    { id: 1, puzzle: 'Word Count Analysis', difficulty: 'easy', status: 'solved', time: '4.2s', date: '2 hours ago' },
    { id: 2, puzzle: 'Join Optimization', difficulty: 'medium', status: 'solved', time: '8.1s', date: '1 day ago' },
    { id: 3, puzzle: 'Partition Tuning', difficulty: 'hard', status: 'attempted', time: 'N/A', date: '2 days ago' }
  ];

  return (
    <div className="profile-page">
      <div className="profile-container">
        {/* Profile Header */}
        <div className="profile-header">
          <div className="profile-banner">
            <div className="banner-grid"></div>
            <div className="banner-glow"></div>
          </div>

          <div className="profile-info">
            <div className="profile-avatar-section">
              <div className="profile-avatar">
                <span className="avatar-icon">👤</span>
                <div className="avatar-ring"></div>
                <div className="avatar-status"></div>
              </div>
              <div className="profile-rank-badge">
                <span className="rank-icon">⚡</span>
                <span className="rank-text">{stats.rank}</span>
              </div>
            </div>

            <div className="profile-details">
              <h1 className="profile-username">{user?.username}</h1>
              <p className="profile-email">{user?.email}</p>
              <div className="profile-meta">
                <span className="meta-item">
                  <span className="meta-icon">📅</span>
                  Joined January 2026
                </span>
                <span className="meta-divider">•</span>
                <span className="meta-item">
                  <span className="meta-icon">🎯</span>
                  {stats.puzzlesSolved}/{stats.totalPuzzles} Puzzles
                </span>
              </div>
            </div>

            <div className="profile-actions">
              <button className="action-btn btn-edit" onClick={() => navigate('/settings')}>
                <span className="btn-icon">⚙️</span>
                Edit Profile
              </button>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="stats-grid">
          <div className="stat-card stat-primary">
            <div className="stat-icon-wrapper">
              <span className="stat-icon-large">🎯</span>
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.puzzlesSolved}</div>
              <div className="stat-label">Puzzles Solved</div>
              <div className="stat-progress">
                <div
                  className="stat-progress-bar"
                  style={{ width: `${(stats.puzzlesSolved / stats.totalPuzzles) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>

          <div className="stat-card stat-secondary">
            <div className="stat-icon-wrapper">
              <span className="stat-icon-large">🔥</span>
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.streak}</div>
              <div className="stat-label">Day Streak</div>
              <div className="stat-sublabel">Keep the momentum going!</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper">
              <span className="stat-icon-large">⭐</span>
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.stars}</div>
              <div className="stat-label">Total Stars</div>
              <div className="stat-sublabel">Earned from puzzles</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon-wrapper">
              <span className="stat-icon-large">⚡</span>
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.efficiency}%</div>
              <div className="stat-label">Avg Efficiency</div>
              <div className="stat-sublabel">Performance metric</div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="profile-tabs">
          <button
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <span className="tab-icon">📊</span>
            Overview
          </button>
          <button
            className={`tab-btn ${activeTab === 'achievements' ? 'active' : ''}`}
            onClick={() => setActiveTab('achievements')}
          >
            <span className="tab-icon">🏆</span>
            Achievements
          </button>
          <button
            className={`tab-btn ${activeTab === 'activity' ? 'active' : ''}`}
            onClick={() => setActiveTab('activity')}
          >
            <span className="tab-icon">📈</span>
            Activity
          </button>
        </div>

        {/* Tab Content */}
        <div className="profile-content">
          {activeTab === 'overview' && (
            <div className="overview-section fade-in">
              <div className="overview-grid">
                <div className="overview-card">
                  <h3 className="card-title">
                    <span className="title-icon">🎯</span>
                    Progress Overview
                  </h3>
                  <div className="progress-list">
                    <div className="progress-item">
                      <div className="progress-header">
                        <span className="progress-label">Easy Puzzles</span>
                        <span className="progress-value">8/15</span>
                      </div>
                      <div className="progress-bar-container">
                        <div className="progress-bar-fill easy" style={{ width: '53%' }}></div>
                      </div>
                    </div>
                    <div className="progress-item">
                      <div className="progress-header">
                        <span className="progress-label">Medium Puzzles</span>
                        <span className="progress-value">4/20</span>
                      </div>
                      <div className="progress-bar-container">
                        <div className="progress-bar-fill medium" style={{ width: '20%' }}></div>
                      </div>
                    </div>
                    <div className="progress-item">
                      <div className="progress-header">
                        <span className="progress-label">Hard Puzzles</span>
                        <span className="progress-value">0/15</span>
                      </div>
                      <div className="progress-bar-container">
                        <div className="progress-bar-fill hard" style={{ width: '0%' }}></div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="overview-card">
                  <h3 className="card-title">
                    <span className="title-icon">📊</span>
                    Performance Metrics
                  </h3>
                  <div className="metrics-list">
                    <div className="metric-item">
                      <span className="metric-label">Total Runs</span>
                      <span className="metric-value">{stats.totalRuns}</span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-label">Best Time</span>
                      <span className="metric-value highlight">{stats.bestTime}</span>
                    </div>
                    <div className="metric-item">
                      <span className="metric-label">Avg Efficiency</span>
                      <span className="metric-value highlight">{stats.efficiency}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'achievements' && (
            <div className="achievements-section fade-in">
              <div className="achievements-header">
                <h3>
                  <span className="section-icon">🏆</span>
                  Your Achievements
                </h3>
                <div className="achievements-stats">
                  <span className="achievement-count">
                    {achievements.filter(a => a.unlocked).length}/{achievements.length} Unlocked
                  </span>
                </div>
              </div>
              <div className="achievements-grid">
                {achievements.map(achievement => (
                  <div
                    key={achievement.id}
                    className={`achievement-card ${achievement.unlocked ? 'unlocked' : 'locked'} rarity-${achievement.rarity}`}
                  >
                    <div className="achievement-glow"></div>
                    <div className="achievement-icon">{achievement.icon}</div>
                    <h4 className="achievement-name">{achievement.name}</h4>
                    <p className="achievement-description">{achievement.description}</p>
                    <div className="achievement-rarity">{achievement.rarity}</div>
                    {achievement.unlocked && (
                      <div className="achievement-unlocked-badge">
                        <span>✓</span>
                      </div>
                    )}
                    {!achievement.unlocked && (
                      <div className="achievement-lock">
                        <span>🔒</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'activity' && (
            <div className="activity-section fade-in">
              <div className="activity-header">
                <h3>
                  <span className="section-icon">📈</span>
                  Recent Activity
                </h3>
              </div>
              <div className="activity-list">
                {recentActivity.map(activity => (
                  <div key={activity.id} className="activity-item">
                    <div className="activity-icon-wrapper">
                      <span className="activity-icon">
                        {activity.status === 'solved' ? '✓' : '○'}
                      </span>
                    </div>
                    <div className="activity-details">
                      <div className="activity-main">
                        <span className="activity-puzzle">{activity.puzzle}</span>
                        <span className={`activity-difficulty difficulty-${activity.difficulty}`}>
                          {activity.difficulty}
                        </span>
                      </div>
                      <div className="activity-meta">
                        <span className={`activity-status status-${activity.status}`}>
                          {activity.status}
                        </span>
                        {activity.status === 'solved' && (
                          <>
                            <span className="activity-divider">•</span>
                            <span className="activity-time">Time: {activity.time}</span>
                          </>
                        )}
                        <span className="activity-divider">•</span>
                        <span className="activity-date">{activity.date}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
