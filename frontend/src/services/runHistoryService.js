const API_BASE = 'http://localhost:8000/api';

export const runHistoryService = {
  async getAllRuns(limit = 50, offset = 0) {
    const response = await fetch(`${API_BASE}/runs?limit=${limit}&offset=${offset}`);
    if (!response.ok) {
      throw new Error('Failed to fetch runs');
    }
    return response.json();
  },

  async getPuzzleRuns(puzzleId, limit = 50, offset = 0) {
    const response = await fetch(`${API_BASE}/puzzles/${puzzleId}/runs?limit=${limit}&offset=${offset}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch runs for puzzle ${puzzleId}`);
    }
    return response.json();
  },

  async getRunDetail(runId) {
    const response = await fetch(`${API_BASE}/runs/${runId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch run ${runId}`);
    }
    return response.json();
  }
};
