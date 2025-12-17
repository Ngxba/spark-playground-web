import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const puzzleService = {
  /**
   * Get list of all puzzles
   */
  async getAllPuzzles() {
    const response = await api.get('/puzzles');
    return response.data;
  },

  /**
   * Get detailed information about a specific puzzle
   */
  async getPuzzle(puzzleId) {
    const response = await api.get(`/puzzles/${puzzleId}`);
    return response.data;
  },

  /**
   * Run user code for a puzzle
   */
  async runPuzzle(puzzleId, code) {
    const response = await api.post(`/puzzles/${puzzleId}/run`, { code });
    return response.data;
  },
};

export default api;
