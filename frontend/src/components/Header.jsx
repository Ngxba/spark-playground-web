import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import './Header.css';

function Header() {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false); // TODO: Replace with actual auth state
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogin = () => {
    // TODO: Implement actual login logic
    setIsLoggedIn(true);
    setShowUserMenu(false);
  };

  const handleLogout = () => {
    // TODO: Implement actual logout logic
    setIsLoggedIn(false);
    setShowUserMenu(false);
  };

  return (
    <header className="app-header-compact">
      <div className="header-container">
        {/* Left: Home/Logo */}
        <div className="header-left">
          <Link to="/" className="header-home-btn" title="Home">
            <span className="home-icon">🏠</span>
            <span className="home-text">SPARK PLAYGROUND</span>
          </Link>

          <div className="header-divider"></div>

          <Link to="/puzzles" className="header-nav-link">
            <span className="nav-icon">🧩</span>
            <span className="nav-text">Puzzles</span>
          </Link>
        </div>

        {/* Center: Status indicator */}
        <div className="header-center">
          <div className="system-status-compact">
            <span className="status-dot-compact"></span>
            <span className="status-text-compact">SYSTEM ONLINE</span>
          </div>
        </div>

        {/* Right: User actions */}
        <div className="header-right">
          {/* Stats (if logged in) */}
          {isLoggedIn && (
            <>
              <div className="header-stats">
                <div className="stat-item-compact">
                  <span className="stat-icon">🔥</span>
                  <span className="stat-value">0</span>
                  <span className="stat-label">Streak</span>
                </div>
                <div className="stat-divider"></div>
                <div className="stat-item-compact">
                  <span className="stat-icon">⭐</span>
                  <span className="stat-value">0</span>
                  <span className="stat-label">Stars</span>
                </div>
              </div>
              <div className="header-divider"></div>
            </>
          )}

          {/* Auth buttons */}
          {!isLoggedIn ? (
            <button className="header-login-btn" onClick={handleLogin}>
              <span className="login-icon">🔐</span>
              <span className="login-text">Sign In</span>
            </button>
          ) : (
            <div className="header-user-menu">
              <button
                className="header-user-btn"
                onClick={() => setShowUserMenu(!showUserMenu)}
              >
                <span className="user-avatar">👤</span>
                <span className="user-name">User</span>
                <span className="dropdown-arrow">{showUserMenu ? '▲' : '▼'}</span>
              </button>

              {showUserMenu && (
                <div className="user-dropdown">
                  <div className="dropdown-item" onClick={() => navigate('/profile')}>
                    <span className="dropdown-icon">👤</span>
                    <span>Profile</span>
                  </div>
                  <div className="dropdown-item" onClick={() => navigate('/settings')}>
                    <span className="dropdown-icon">⚙️</span>
                    <span>Settings</span>
                  </div>
                  <div className="dropdown-divider"></div>
                  <div className="dropdown-item logout" onClick={handleLogout}>
                    <span className="dropdown-icon">🚪</span>
                    <span>Sign Out</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
