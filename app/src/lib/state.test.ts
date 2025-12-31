import { describe, it, expect } from 'vitest';
import { shouldUpdatePlayer, allQuestions } from './state.svelte';

describe('Version tracking', () => {
  it('prevents out-of-order updates for race condition safety', () => {
    // Test with player (same logic applies to questions via shouldUpdateQuestion)
    shouldUpdatePlayer(1, 42);
    expect(shouldUpdatePlayer(1, 41)).toBe(false); // Reject older version
    expect(shouldUpdatePlayer(1, 43)).toBe(true); // Accept newer version
    expect(shouldUpdatePlayer(1, 43)).toBe(true); // Idempotent (same version)
  });

  it('tracks versions independently per entity', () => {
    shouldUpdatePlayer(1, 10);
    shouldUpdatePlayer(2, 20);

    expect(shouldUpdatePlayer(1, 9)).toBe(false); // Player 1 rejects old
    expect(shouldUpdatePlayer(2, 21)).toBe(true); // Player 2 accepts new
  });

  it('flattens board questions from categories', () => {
    const board = {
      id: 1,
      name: 'Test Board',
      order: 1,
      categories: [
        {
          id: 1,
          name: 'Category 1',
          order: 1,
          questions: [
            {
              id: 1,
              text: 'Q1',
              type: 'text',
              flags: [],
              answer: 'A1',
              points: 100,
              slides: [],
            },
            {
              id: 2,
              text: 'Q2',
              type: 'text',
              flags: [],
              answer: 'A2',
              points: 200,
              slides: [],
            },
          ],
        },
      ],
    };

    const questions = allQuestions(board);
    expect(questions).toHaveLength(2);
    expect(allQuestions(undefined)).toEqual([]);
  });
});
