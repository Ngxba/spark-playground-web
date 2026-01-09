import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import PuzzleList from './pages/PuzzleList';
import PuzzleWorkspace from './pages/PuzzleWorkspace';
import ReportPage from './pages/ReportPage';
import AuthPage from './pages/AuthPage';
import ProfilePage from './pages/ProfilePage';
import SettingsPage from './pages/SettingsPage';
import StudyPlanPage from './pages/StudyPlanPage';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import RightSidebar from './components/RightSidebar';
import './App.css';

function AppContent() {
  const location = useLocation();
  const showSidebars = location.pathname === '/puzzles' || location.pathname === '/study-plan';
  const showHeader = location.pathname !== '/' && !location.pathname.startsWith('/signin') && !location.pathname.startsWith('/signup');

  return (
    <div className="app">
      {showHeader && <Header />}
      <div className="app-container">
        {showSidebars && <Sidebar />}
        <main className="app-main">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/signin" element={<AuthPage />} />
            <Route path="/signup" element={<AuthPage />} />
            <Route path="/puzzles" element={<PuzzleList />} />
            <Route path="/study-plan" element={<StudyPlanPage />} />
            <Route path="/puzzle/:puzzleId" element={<PuzzleWorkspace />} />
            <Route path="/puzzle/:puzzleId/report" element={<ReportPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
        {showSidebars && <RightSidebar />}
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
