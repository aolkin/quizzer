import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { recordPlayerAnswer, toggleQuestion, getBoard } from './api';

describe('API', () => {
  let fetchMock: any;

  beforeEach(() => {
    fetchMock = vi.fn();
    global.fetch = fetchMock;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('recordPlayerAnswer', () => {
    it('makes POST request with correct parameters', async () => {
      const mockResponse = {
        player_id: 1,
        score: 500,
        version: 42
      };

      fetchMock.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await recordPlayerAnswer(1, 2, 3, true, 100);

      expect(fetchMock).toHaveBeenCalledWith(
        'http://quasar.local:8000/api/board/1/answers/',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            player_id: 2,
            question_id: 3,
            is_correct: true,
            points: 100
          })
        }
      );

      expect(result).toEqual(mockResponse);
    });

    it('handles correct answer without custom points', async () => {
      const mockResponse = {
        player_id: 1,
        score: 300,
        version: 5
      };

      fetchMock.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await recordPlayerAnswer(1, 1, 1, true);

      const callBody = JSON.parse(fetchMock.mock.calls[0][1].body);
      expect(callBody.is_correct).toBe(true);
      expect(callBody.points).toBeUndefined();
    });

    it('handles incorrect answer', async () => {
      const mockResponse = {
        player_id: 1,
        score: 100,
        version: 6
      };

      fetchMock.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await recordPlayerAnswer(1, 1, 1, false, -100);

      const callBody = JSON.parse(fetchMock.mock.calls[0][1].body);
      expect(callBody.is_correct).toBe(false);
      expect(callBody.points).toBe(-100);
    });

    it('throws error on failed request', async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
        text: async () => 'Database error'
      });

      await expect(recordPlayerAnswer(1, 1, 1, true)).rejects.toThrow(
        'Failed to record answer'
      );
    });

    it('returns version number for race condition prevention', async () => {
      const mockResponse = {
        player_id: 1,
        score: 500,
        version: 42
      };

      fetchMock.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await recordPlayerAnswer(1, 1, 1, true);
      expect(result.version).toBe(42);
    });
  });

  describe('toggleQuestion', () => {
    it('makes PATCH request to mark question answered', async () => {
      const mockResponse = {
        question_id: 10,
        answered: true,
        version: 15
      };

      fetchMock.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await toggleQuestion(10, true);

      expect(fetchMock).toHaveBeenCalledWith(
        'http://quasar.local:8000/api/question/10/',
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answered: true })
        }
      );

      expect(result).toEqual(mockResponse);
    });

    it('makes PATCH request to mark question not answered', async () => {
      const mockResponse = {
        question_id: 10,
        answered: false,
        version: 16
      };

      fetchMock.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await toggleQuestion(10, false);

      const callBody = JSON.parse(fetchMock.mock.calls[0][1].body);
      expect(callBody.answered).toBe(false);
      expect(result.answered).toBe(false);
    });

    it('throws error on failed request', async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        statusText: 'Not Found',
        text: async () => 'Question not found'
      });

      await expect(toggleQuestion(999, true)).rejects.toThrow(
        'Failed to toggle question'
      );
    });

    it('returns version number', async () => {
      const mockResponse = {
        question_id: 10,
        answered: true,
        version: 20
      };

      fetchMock.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await toggleQuestion(10, true);
      expect(result.version).toBe(20);
    });
  });

  describe('getBoard', () => {
    it('makes GET request for board data', async () => {
      const mockBoard = {
        id: 5,
        name: 'Test Board',
        categories: []
      };

      fetchMock.mockResolvedValue({
        ok: true,
        json: async () => mockBoard
      });

      const result = await getBoard(5);

      expect(fetchMock).toHaveBeenCalledWith(
        'http://quasar.local:8000/api/board/5/',
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        }
      );

      expect(result).toEqual(mockBoard);
    });

    it('throws error on 404', async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        statusText: 'Not Found',
        text: async () => 'Board not found'
      });

      await expect(getBoard(999)).rejects.toThrow('Failed to fetch board');
    });
  });

  describe('error handling', () => {
    it('includes status text and error body in error message', async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        statusText: 'Bad Request',
        text: async () => 'Invalid player ID'
      });

      await expect(recordPlayerAnswer(1, 1, 1, true)).rejects.toThrow(
        'Failed to record answer: Bad Request - Invalid player ID'
      );
    });

    it('handles network errors', async () => {
      fetchMock.mockRejectedValue(new Error('Network error'));

      await expect(recordPlayerAnswer(1, 1, 1, true)).rejects.toThrow(
        'Network error'
      );
    });
  });
});
