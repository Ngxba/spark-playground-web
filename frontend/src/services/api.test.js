import { describe, it, expect } from 'vitest';

// Simple tests for API structure
describe('Puzzle Service API Structure', () => {
  it('should export puzzleService with correct methods', async () => {
    const { puzzleService } = await import('./api');

    expect(puzzleService).toBeDefined();
    expect(typeof puzzleService.getAllPuzzles).toBe('function');
    expect(typeof puzzleService.getPuzzle).toBe('function');
    expect(typeof puzzleService.runPuzzle).toBe('function');
  });

  it('should have valid API URL configuration', () => {
    // API base URL should be configurable via env
    const envUrl = import.meta.env.VITE_API_URL;
    expect(envUrl).toBeDefined();
    expect(typeof envUrl).toBe('string');
  });
});

// Note: Full integration tests with axios mocking are complex with Vite/Vitest
// These should be tested in E2E tests or with a running backend
