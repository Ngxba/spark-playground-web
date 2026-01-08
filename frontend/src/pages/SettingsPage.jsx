import { useState, useEffect } from 'react';
import { authService } from '../services/api';
import { useNavigate } from 'react-router-dom';
import './SettingsPage.css';

function SettingsPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('account');
  const [saveStatus, setSaveStatus] = useState('');

  // Form states
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [bio, setBio] = useState('');

  // Preferences
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [weeklyDigest, setWeeklyDigest] = useState(true);
  const [achievementNotifications, setAchievementNotifications] = useState(true);
  const [showHints, setShowHints] = useState(true);
  const [autoRun, setAutoRun] = useState(false);
  const [theme, setTheme] = useState('dark');
  const [editorTheme, setEditorTheme] = useState('monokai');
  const [fontSize, setFontSize] = useState(14);

  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    if (!currentUser) {
      navigate('/signin');
      return;
    }

    // Simulate loading user data
    setTimeout(() => {
      setUser(currentUser);
      setUsername(currentUser.username || '');
      setEmail(currentUser.email || '');
      setBio(currentUser.bio || '');
      setLoading(false);
    }, 500);
  }, [navigate]);

  const handleSaveProfile = (e) => {
    e.preventDefault();
    setSaveStatus('saving');

    // Simulate save
    setTimeout(() => {
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus(''), 3000);
    }, 1000);
  };

  const handleSavePreferences = () => {
    setSaveStatus('saving');

    // Simulate save
    setTimeout(() => {
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus(''), 3000);
    }, 1000);
  };

  const handleDeleteAccount = () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      authService.signOut();
      navigate('/');
    }
  };

  if (loading) {
    return (
      <div className="settings-loading">
        <div className="loading-spinner"></div>
        <p>LOADING SETTINGS...</p>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <div className="settings-container">
        <div className="settings-header">
          <h1>
            <span className="header-icon">⚙️</span>
            Settings
          </h1>
          <p className="header-subtitle">Manage your account and preferences</p>
        </div>

        <div className="settings-layout">
          {/* Sidebar Navigation */}
          <div className="settings-sidebar">
            <button
              className={`sidebar-item ${activeSection === 'account' ? 'active' : ''}`}
              onClick={() => setActiveSection('account')}
            >
              <span className="sidebar-icon">👤</span>
              <span className="sidebar-label">Account</span>
            </button>
            <button
              className={`sidebar-item ${activeSection === 'preferences' ? 'active' : ''}`}
              onClick={() => setActiveSection('preferences')}
            >
              <span className="sidebar-icon">🎨</span>
              <span className="sidebar-label">Preferences</span>
            </button>
            <button
              className={`sidebar-item ${activeSection === 'notifications' ? 'active' : ''}`}
              onClick={() => setActiveSection('notifications')}
            >
              <span className="sidebar-icon">🔔</span>
              <span className="sidebar-label">Notifications</span>
            </button>
            <button
              className={`sidebar-item ${activeSection === 'privacy' ? 'active' : ''}`}
              onClick={() => setActiveSection('privacy')}
            >
              <span className="sidebar-icon">🔒</span>
              <span className="sidebar-label">Privacy</span>
            </button>
            <button
              className={`sidebar-item ${activeSection === 'security' ? 'active' : ''}`}
              onClick={() => setActiveSection('security')}
            >
              <span className="sidebar-icon">🛡️</span>
              <span className="sidebar-label">Security</span>
            </button>
          </div>

          {/* Main Content */}
          <div className="settings-content">
            {saveStatus && (
              <div className={`save-notification ${saveStatus}`}>
                {saveStatus === 'saving' && (
                  <>
                    <span className="notification-spinner"></span>
                    Saving changes...
                  </>
                )}
                {saveStatus === 'saved' && (
                  <>
                    <span className="notification-icon">✓</span>
                    Changes saved successfully!
                  </>
                )}
              </div>
            )}

            {/* Account Section */}
            {activeSection === 'account' && (
              <div className="settings-section fade-in">
                <div className="section-header">
                  <h2>Account Information</h2>
                  <p>Update your account details</p>
                </div>

                <form onSubmit={handleSaveProfile} className="settings-form">
                  <div className="form-group">
                    <label htmlFor="username" className="form-label">
                      <span className="label-icon">👤</span>
                      Username
                    </label>
                    <input
                      type="text"
                      id="username"
                      className="form-input"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Enter your username"
                    />
                    <span className="form-hint">Your unique identifier on the platform</span>
                  </div>

                  <div className="form-group">
                    <label htmlFor="email" className="form-label">
                      <span className="label-icon">✉️</span>
                      Email Address
                    </label>
                    <input
                      type="email"
                      id="email"
                      className="form-input"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your email"
                    />
                    <span className="form-hint">Used for notifications and account recovery</span>
                  </div>

                  <div className="form-group">
                    <label htmlFor="bio" className="form-label">
                      <span className="label-icon">📝</span>
                      Bio
                    </label>
                    <textarea
                      id="bio"
                      className="form-textarea"
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      placeholder="Tell us about yourself..."
                      rows={4}
                    />
                    <span className="form-hint">A brief description about yourself (optional)</span>
                  </div>

                  <div className="form-actions">
                    <button type="submit" className="btn-save">
                      <span className="btn-icon">💾</span>
                      Save Changes
                    </button>
                    <button type="button" className="btn-cancel" onClick={() => navigate('/profile')}>
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Preferences Section */}
            {activeSection === 'preferences' && (
              <div className="settings-section fade-in">
                <div className="section-header">
                  <h2>Editor Preferences</h2>
                  <p>Customize your coding experience</p>
                </div>

                <div className="preferences-grid">
                  <div className="preference-group">
                    <h3 className="preference-title">
                      <span className="title-icon">🎨</span>
                      Appearance
                    </h3>

                    <div className="preference-item">
                      <label className="preference-label">
                        <span className="label-text">Theme</span>
                        <span className="label-description">Choose your preferred color theme</span>
                      </label>
                      <select
                        className="preference-select"
                        value={theme}
                        onChange={(e) => setTheme(e.target.value)}
                      >
                        <option value="dark">Dark</option>
                        <option value="light">Light</option>
                        <option value="auto">Auto</option>
                      </select>
                    </div>

                    <div className="preference-item">
                      <label className="preference-label">
                        <span className="label-text">Editor Theme</span>
                        <span className="label-description">Code editor color scheme</span>
                      </label>
                      <select
                        className="preference-select"
                        value={editorTheme}
                        onChange={(e) => setEditorTheme(e.target.value)}
                      >
                        <option value="monokai">Monokai</option>
                        <option value="github">GitHub</option>
                        <option value="dracula">Dracula</option>
                        <option value="tomorrow">Tomorrow Night</option>
                      </select>
                    </div>

                    <div className="preference-item">
                      <label className="preference-label">
                        <span className="label-text">Font Size</span>
                        <span className="label-description">Editor font size in pixels</span>
                      </label>
                      <div className="slider-wrapper">
                        <input
                          type="range"
                          className="preference-slider"
                          min="12"
                          max="24"
                          value={fontSize}
                          onChange={(e) => setFontSize(parseInt(e.target.value))}
                        />
                        <span className="slider-value">{fontSize}px</span>
                      </div>
                    </div>
                  </div>

                  <div className="preference-group">
                    <h3 className="preference-title">
                      <span className="title-icon">⚡</span>
                      Behavior
                    </h3>

                    <div className="preference-item">
                      <label className="toggle-label">
                        <div className="toggle-info">
                          <span className="toggle-text">Show Hints</span>
                          <span className="toggle-description">Display helpful hints while solving puzzles</span>
                        </div>
                        <div className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={showHints}
                            onChange={(e) => setShowHints(e.target.checked)}
                          />
                          <span className="toggle-slider"></span>
                        </div>
                      </label>
                    </div>

                    <div className="preference-item">
                      <label className="toggle-label">
                        <div className="toggle-info">
                          <span className="toggle-text">Auto-run Code</span>
                          <span className="toggle-description">Automatically run code after changes</span>
                        </div>
                        <div className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={autoRun}
                            onChange={(e) => setAutoRun(e.target.checked)}
                          />
                          <span className="toggle-slider"></span>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>

                <div className="form-actions">
                  <button className="btn-save" onClick={handleSavePreferences}>
                    <span className="btn-icon">💾</span>
                    Save Preferences
                  </button>
                </div>
              </div>
            )}

            {/* Notifications Section */}
            {activeSection === 'notifications' && (
              <div className="settings-section fade-in">
                <div className="section-header">
                  <h2>Notification Settings</h2>
                  <p>Choose what updates you want to receive</p>
                </div>

                <div className="notification-groups">
                  <div className="notification-group">
                    <h3 className="group-title">
                      <span className="title-icon">✉️</span>
                      Email Notifications
                    </h3>

                    <div className="preference-item">
                      <label className="toggle-label">
                        <div className="toggle-info">
                          <span className="toggle-text">Email Notifications</span>
                          <span className="toggle-description">Receive email updates about your account</span>
                        </div>
                        <div className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={emailNotifications}
                            onChange={(e) => setEmailNotifications(e.target.checked)}
                          />
                          <span className="toggle-slider"></span>
                        </div>
                      </label>
                    </div>

                    <div className="preference-item">
                      <label className="toggle-label">
                        <div className="toggle-info">
                          <span className="toggle-text">Weekly Digest</span>
                          <span className="toggle-description">Get a weekly summary of your progress</span>
                        </div>
                        <div className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={weeklyDigest}
                            onChange={(e) => setWeeklyDigest(e.target.checked)}
                            disabled={!emailNotifications}
                          />
                          <span className="toggle-slider"></span>
                        </div>
                      </label>
                    </div>

                    <div className="preference-item">
                      <label className="toggle-label">
                        <div className="toggle-info">
                          <span className="toggle-text">Achievement Unlocked</span>
                          <span className="toggle-description">Get notified when you earn achievements</span>
                        </div>
                        <div className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={achievementNotifications}
                            onChange={(e) => setAchievementNotifications(e.target.checked)}
                            disabled={!emailNotifications}
                          />
                          <span className="toggle-slider"></span>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>

                <div className="form-actions">
                  <button className="btn-save" onClick={handleSavePreferences}>
                    <span className="btn-icon">💾</span>
                    Save Settings
                  </button>
                </div>
              </div>
            )}

            {/* Privacy Section */}
            {activeSection === 'privacy' && (
              <div className="settings-section fade-in">
                <div className="section-header">
                  <h2>Privacy Settings</h2>
                  <p>Control your data and visibility</p>
                </div>

                <div className="privacy-options">
                  <div className="privacy-item">
                    <div className="privacy-icon">👁️</div>
                    <div className="privacy-content">
                      <h3>Profile Visibility</h3>
                      <p>Your profile is currently public. Other users can see your progress and achievements.</p>
                      <button className="btn-secondary">Make Private</button>
                    </div>
                  </div>

                  <div className="privacy-item">
                    <div className="privacy-icon">📊</div>
                    <div className="privacy-content">
                      <h3>Data Collection</h3>
                      <p>We collect analytics to improve your experience. You can opt out at any time.</p>
                      <button className="btn-secondary">Manage Preferences</button>
                    </div>
                  </div>

                  <div className="privacy-item">
                    <div className="privacy-icon">📥</div>
                    <div className="privacy-content">
                      <h3>Export Data</h3>
                      <p>Download a copy of your data including all solved puzzles and statistics.</p>
                      <button className="btn-secondary">Download Data</button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Security Section */}
            {activeSection === 'security' && (
              <div className="settings-section fade-in">
                <div className="section-header">
                  <h2>Security Settings</h2>
                  <p>Keep your account secure</p>
                </div>

                <div className="security-options">
                  <div className="security-item">
                    <div className="security-icon">🔑</div>
                    <div className="security-content">
                      <h3>Change Password</h3>
                      <p>Update your password to keep your account secure</p>
                      <button className="btn-secondary">Change Password</button>
                    </div>
                  </div>

                  <div className="security-item">
                    <div className="security-icon">📱</div>
                    <div className="security-content">
                      <h3>Two-Factor Authentication</h3>
                      <p>Add an extra layer of security to your account</p>
                      <button className="btn-secondary">Enable 2FA</button>
                    </div>
                  </div>

                  <div className="security-item">
                    <div className="security-icon">🔓</div>
                    <div className="security-content">
                      <h3>Active Sessions</h3>
                      <p>Manage devices where you're currently logged in</p>
                      <button className="btn-secondary">View Sessions</button>
                    </div>
                  </div>

                  <div className="security-item danger-zone">
                    <div className="security-icon">⚠️</div>
                    <div className="security-content">
                      <h3>Delete Account</h3>
                      <p>Permanently delete your account and all associated data. This action cannot be undone.</p>
                      <button className="btn-danger" onClick={handleDeleteAccount}>
                        Delete Account
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
