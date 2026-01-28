import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const authService = {
  /**
   * Sign up a new user
   */
  async signUp(username, email, password) {
    const response = await api.post('/auth/signup', {
      username,
      email,
      password,
    });
    // Store token and user data
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      // Dispatch custom event to notify components
      window.dispatchEvent(new Event('authStateChanged'));
    }
    return response.data;
  },

  /**
   * Sign in an existing user
   */
  async signIn(email, password) {
    const response = await api.post('/auth/signin', {
      email,
      password,
    });
    // Store token and user data
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      // Dispatch custom event to notify components
      window.dispatchEvent(new Event('authStateChanged'));
    }
    return response.data;
  },

  /**
   * Sign out the current user
   */
  signOut() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    // Dispatch custom event to notify components
    window.dispatchEvent(new Event('authStateChanged'));
  },

  /**
   * Get current user from local storage
   */
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  },
};

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
   * Run user code for a puzzle (V2 - function-based submission)
   *
   * Users submit code with `def solve(...) -> DataFrame` format.
   * Example:
   *   def solve(fruits):
   *     return fruits.orderBy('type')
   */
  async runPuzzle(puzzleId, code, sparkConfig = null) {
    const body = {
      code,
      ...(sparkConfig && { spark_config: sparkConfig }),
    };
  
    const { data } = await api.post(
      `/puzzles/${puzzleId}/run`,
      body
    );
  
    return data;
  }  
};

export default api;
