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

  it('recordPlayerAnswer makes POST request and returns version', async () => {
    const mockResponse = { player_id: 1, score: 500, version: 42 };
    fetchMock.mockResolvedValue({ ok: true, json: async () => mockResponse });

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
    expect(result.version).toBe(42);
  });

  it('toggleQuestion makes PATCH request and returns version', async () => {
    const mockResponse = { question_id: 10, answered: true, version: 15 };
    fetchMock.mockResolvedValue({ ok: true, json: async () => mockResponse });

    const result = await toggleQuestion(10, true);

    expect(result.version).toBe(15);
  });

  it('handles error responses with detailed messages', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      statusText: 'Bad Request',
      text: async () => 'Invalid player ID'
    });

    await expect(recordPlayerAnswer(1, 1, 1, true)).rejects.toThrow(
      'Failed to record answer: Bad Request - Invalid player ID'
    );
  });
});
