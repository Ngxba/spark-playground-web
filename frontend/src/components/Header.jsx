import { Link, useNavigate, useLocation, useParams } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import { authService } from '../services/api';
import { puzzleService } from '../services/api';
import './Header.css';

function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const params = useParams();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [statusText, setStatusText] = useState('SYSTEM ONLINE');
  const userMenuRef = useRef(null);

  // Check authentication state on mount and when storage changes
  useEffect(() => {
    const checkAuthStatus = () => {
      const isAuth = authService.isAuthenticated();
      setIsLoggedIn(isAuth);
      if (isAuth) {
        const user = authService.getCurrentUser();
        setCurrentUser(user);
      } else {
        setCurrentUser(null);
      }
    };

    checkAuthStatus();

    // Listen for storage changes (for cross-tab synchronization)
    window.addEventListener('storage', checkAuthStatus);

    // Listen for custom auth change events (for same-tab updates)
    window.addEventListener('authStateChanged', checkAuthStatus);

    return () => {
      window.removeEventListener('storage', checkAuthStatus);
      window.removeEventListener('authStateChanged', checkAuthStatus);
    };
  }, []);

  // Update status text based on current route
  useEffect(() => {
    const updateStatusText = async () => {
      const path = location.pathname;

      if (path === '/puzzles') {
        setStatusText('PUZZLES');
      } else if (path.startsWith('/puzzle/')) {
        // Extract puzzleId from path
        const puzzleId = path.split('/')[2];
        if (puzzleId && !path.includes('/report')) {
          try {
            const puzzle = await puzzleService.getPuzzle(puzzleId);
            setStatusText(puzzle.title.toUpperCase());
          } catch (err) {
            setStatusText('PUZZLE');
          }
        } else if (path.includes('/report')) {
          setStatusText('RUN REPORT');
        }
      } else {
        setStatusText('SYSTEM ONLINE');
      }
    };

    updateStatusText();
  }, [location.pathname]);

  const handleLogin = () => {
    navigate('/signin');
  };

  const handleLogout = () => {
    authService.signOut();
    setIsLoggedIn(false);
    setCurrentUser(null);
    setShowUserMenu(false);
    navigate('/');
  };

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);

  return (
    <header className="app-header-compact">
      <div className="header-container">
        {/* Left: Home/Logo */}
        <div className="header-left">
          <Link to="/" className="header-home-btn" title="Home">
            <span className="home-icon">🏠</span>
            <span className="home-text">SPARK PLAYGROUND</span>
          </Link>
        </div>

        {/* Center: Status indicator */}
        <div className="header-center">
          <div className="system-status-compact">
            <span className="status-dot-compact"></span>
            <span className="status-text-compact">{statusText}</span>
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
            <div className="header-user-menu" ref={userMenuRef}>
              <button
                className="header-user-btn"
                onClick={() => setShowUserMenu(!showUserMenu)}
              >
                <span className="user-avatar">👤</span>
                <span className="user-name">{currentUser?.username || 'User'}</span>
                <span className="dropdown-arrow">{showUserMenu ? '▲' : '▼'}</span>
              </button>

              {showUserMenu && (
                <div className="user-dropdown">
                  <div className="dropdown-item" onClick={() => {
                    setShowUserMenu(false);
                    navigate('/profile');
                  }}>
                    <span className="dropdown-icon">👤</span>
                    <span>Profile</span>
                  </div>
                  <div className="dropdown-item" onClick={() => {
                    setShowUserMenu(false);
                    navigate('/settings');
                  }}>
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
