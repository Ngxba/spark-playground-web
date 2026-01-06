import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import PuzzleList from './pages/PuzzleList';
import PuzzleWorkspace from './pages/PuzzleWorkspace';
import ReportPage from './pages/ReportPage';
import Sidebar from './components/Sidebar';
import RightSidebar from './components/RightSidebar';
import './App.css';

function AppContent() {
  const location = useLocation();
  const showSidebars = location.pathname === '/';

  return (
    <div className="app">
      <header className="app-header">
        <h1>Spark Playground</h1>
        <p>Learn Apache Spark through interactive factory puzzles</p>
      </header>
      <div className="app-container">
        {showSidebars && <Sidebar />}
        <main className="app-main">
          <Routes>
            <Route path="/" element={<PuzzleList />} />
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
