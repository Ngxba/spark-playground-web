import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import PuzzleList from './pages/PuzzleList';
import PuzzleWorkspace from './pages/PuzzleWorkspace';
import ReportPage from './pages/ReportPage';
import AuthPage from './pages/AuthPage';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import RightSidebar from './components/RightSidebar';
import './App.css';

function AppContent() {
  const location = useLocation();
  const showSidebars = location.pathname === '/puzzles';
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
            <Route path="/puzzle/:puzzleId" element={<PuzzleWorkspace />} />
            <Route path="/puzzle/:puzzleId/report" element={<ReportPage />} />
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
