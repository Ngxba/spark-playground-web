import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PuzzleList from './pages/PuzzleList';
import PuzzleWorkspace from './pages/PuzzleWorkspace';
import ReportPage from './pages/ReportPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>Spark Playground</h1>
          <p>Learn Apache Spark through interactive factory puzzles</p>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<PuzzleList />} />
            <Route path="/puzzle/:puzzleId" element={<PuzzleWorkspace />} />
            <Route path="/puzzle/:puzzleId/report" element={<ReportPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
