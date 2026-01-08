import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/api';
import './AuthPage.css';

function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [mode, setMode] = useState('signin'); // 'signin' or 'signup'

  // Set mode based on URL path
  useEffect(() => {
    if (location.pathname === '/signup') {
      setMode('signup');
    } else {
      setMode('signin');
    }
  }, [location.pathname]);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    username: '',
    rememberMe: false
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    // Clear error when user types
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (mode === 'signup') {
      if (!formData.username) {
        newErrors.username = 'Username is required';
      }
      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      if (mode === 'signup') {
        // Sign up
        await authService.signUp(formData.username, formData.email, formData.password);
      } else {
        // Sign in
        await authService.signIn(formData.email, formData.password);
      }

      // Navigate to puzzles page after successful auth
      navigate('/puzzles');
    } catch (error) {
      setIsLoading(false);
      // Handle errors
      if (error.response?.data?.detail) {
        // Backend validation error
        setErrors({ general: error.response.data.detail });
      } else if (error.response?.status === 400) {
        setErrors({ general: 'Email or username already exists' });
      } else if (error.response?.status === 401) {
        setErrors({ general: 'Invalid email or password' });
      } else {
        setErrors({ general: 'An error occurred. Please try again.' });
      }
    }
  };

  const handleGitHubAuth = () => {
    // Implement GitHub OAuth flow
    console.log('GitHub OAuth initiated');
  };

  const toggleMode = () => {
    const newPath = mode === 'signin' ? '/signup' : '/signin';
    navigate(newPath);
    setErrors({});
    setFormData({
      email: '',
      password: '',
      confirmPassword: '',
      username: '',
      rememberMe: false
    });
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        {/* Left Side - Branding */}
        <div className="auth-branding">
          <div className="brand-content">
            <div className="brand-icon">
              <span className="spark-symbol">⚡</span>
            </div>
            <h1 className="brand-title">Spark Playground</h1>
            <p className="brand-tagline">Master Big Data Processing</p>
            <div className="brand-stats">
              <div className="stat-item">
                <span className="stat-value">100+</span>
                <span className="stat-label">Challenges</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">10K+</span>
                <span className="stat-label">Developers</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">50K+</span>
                <span className="stat-label">Solutions</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Auth Form */}
        <div className="auth-form-section">
          <div className="auth-form-container">
            {/* Mode Toggle */}
            <div className="auth-mode-toggle">
              <button
                className={`mode-btn ${mode === 'signin' ? 'active' : ''}`}
                onClick={() => navigate('/signin')}
                type="button"
              >
                Sign In
              </button>
              <button
                className={`mode-btn ${mode === 'signup' ? 'active' : ''}`}
                onClick={() => navigate('/signup')}
                type="button"
              >
                Sign Up
              </button>
              <div
                className="mode-slider"
                style={{ transform: mode === 'signup' ? 'translateX(100%)' : 'translateX(0)' }}
              />
            </div>

            <h2 className="auth-title">
              {mode === 'signin' ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="auth-subtitle">
              {mode === 'signin'
                ? 'Sign in to continue your journey'
                : 'Start your data engineering journey today'}
            </p>

            {/* GitHub OAuth Button */}
            <button
              className="github-auth-btn"
              onClick={handleGitHubAuth}
              type="button"
            >
              <svg className="github-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              Continue with GitHub
            </button>

            <div className="divider">
              <span className="divider-text">OR</span>
            </div>

            {/* Auth Form */}
            <form onSubmit={handleSubmit} className="auth-form">
              {errors.general && (
                <div className="general-error">
                  {errors.general}
                </div>
              )}

              {mode === 'signup' && (
                <div className="form-group">
                  <label htmlFor="username" className="form-label">Username</label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    className={`form-input ${errors.username ? 'error' : ''}`}
                    placeholder="Enter your username"
                  />
                  {errors.username && <span className="error-message">{errors.username}</span>}
                </div>
              )}

              <div className="form-group">
                <label htmlFor="email" className="form-label">Email</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  placeholder="Enter your email"
                />
                {errors.email && <span className="error-message">{errors.email}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="password" className="form-label">Password</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className={`form-input ${errors.password ? 'error' : ''}`}
                  placeholder="Enter your password"
                />
                {errors.password && <span className="error-message">{errors.password}</span>}
              </div>

              {mode === 'signup' && (
                <div className="form-group">
                  <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className={`form-input ${errors.confirmPassword ? 'error' : ''}`}
                    placeholder="Confirm your password"
                  />
                  {errors.confirmPassword && <span className="error-message">{errors.confirmPassword}</span>}
                </div>
              )}

              {mode === 'signin' && (
                <div className="form-options">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="rememberMe"
                      checked={formData.rememberMe}
                      onChange={handleInputChange}
                      className="form-checkbox"
                    />
                    <span className="checkbox-text">Remember me</span>
                  </label>
                  <a href="/forgot-password" className="forgot-link">
                    Forgot password?
                  </a>
                </div>
              )}

              <button
                type="submit"
                className="submit-btn"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="loading-spinner" />
                ) : (
                  mode === 'signin' ? 'Sign In' : 'Create Account'
                )}
              </button>
            </form>

            {/* Alternative Action */}
            <div className="auth-footer">
              {mode === 'signin' ? (
                <p>
                  Don't have an account?
                  <button onClick={toggleMode} className="toggle-link">Sign up</button>
                </p>
              ) : (
                <p>
                  Already have an account?
                  <button onClick={toggleMode} className="toggle-link">Sign in</button>
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthPage;
