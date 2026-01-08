import { Link, useLocation } from 'react-router-dom';
import './Sidebar.css';

function Sidebar() {
  const location = useLocation();

  const navItems = [
    { id: 'library', label: 'Library', icon: '📚', path: '/puzzles' },
    { id: 'puzzles', label: 'Puzzles', icon: '🧩', path: '/puzzles', badge: 'New' },
    { id: 'study-plan', label: 'Study Plan', icon: '📋', path: '/study-plan' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-content">
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <Link
              key={item.id}
              to={item.path}
              className={`sidebar-nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <span className="sidebar-nav-icon">{item.icon}</span>
              <span className="sidebar-nav-label">{item.label}</span>
              {item.badge && <span className="sidebar-nav-badge">{item.badge}</span>}
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-progress">
            <div className="sidebar-progress-header">
              <span className="sidebar-progress-title">Your Progress</span>
            </div>
            <div className="sidebar-progress-stats">
              <div className="sidebar-stat">
                <div className="sidebar-stat-value">0/12</div>
                <div className="sidebar-stat-label">Solved</div>
              </div>
              <div className="sidebar-stat">
                <div className="sidebar-stat-value">0%</div>
                <div className="sidebar-stat-label">Complete</div>
              </div>
            </div>
            <div className="sidebar-progress-bar">
              <div className="sidebar-progress-fill" style={{ width: '0%' }}></div>
            </div>
          </div>

          <button className="sidebar-signin-btn">
            <span className="sidebar-signin-icon">🔐</span>
            Sign In
          </button>
          <p className="sidebar-signin-text">
            Sign in to track your progress and save your solutions
          </p>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
