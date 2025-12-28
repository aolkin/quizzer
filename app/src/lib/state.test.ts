import { describe, it, expect, beforeEach } from 'vitest';
import { shouldUpdatePlayer, shouldUpdateQuestion } from './state.svelte';

describe('Version tracking', () => {
  describe('shouldUpdatePlayer', () => {
    it('accepts first version', () => {
      const playerId = 1;
      const result = shouldUpdatePlayer(playerId, 42);
      expect(result).toBe(true);
    });

    it('accepts newer version', () => {
      const playerId = 2;
      shouldUpdatePlayer(playerId, 42);
      const result = shouldUpdatePlayer(playerId, 43);
      expect(result).toBe(true);
    });

    it('ignores out-of-order updates', () => {
      const playerId = 3;
      shouldUpdatePlayer(playerId, 42);
      const result = shouldUpdatePlayer(playerId, 41);
      expect(result).toBe(false);
    });

    it('accepts same version (idempotent)', () => {
      const playerId = 4;
      shouldUpdatePlayer(playerId, 42);
      const result = shouldUpdatePlayer(playerId, 42);
      expect(result).toBe(true);
    });

    it('handles multiple players independently', () => {
      const player1 = 10;
      const player2 = 20;
      
      shouldUpdatePlayer(player1, 42);
      shouldUpdatePlayer(player2, 50);
      
      expect(shouldUpdatePlayer(player1, 41)).toBe(false);
      expect(shouldUpdatePlayer(player2, 51)).toBe(true);
      expect(shouldUpdatePlayer(player1, 43)).toBe(true);
    });
  });

  describe('shouldUpdateQuestion', () => {
    it('accepts first version', () => {
      const questionId = 100;
      const result = shouldUpdateQuestion(questionId, 1);
      expect(result).toBe(true);
    });

    it('accepts newer version', () => {
      const questionId = 101;
      shouldUpdateQuestion(questionId, 10);
      const result = shouldUpdateQuestion(questionId, 11);
      expect(result).toBe(true);
    });

    it('ignores out-of-order updates', () => {
      const questionId = 102;
      shouldUpdateQuestion(questionId, 10);
      const result = shouldUpdateQuestion(questionId, 9);
      expect(result).toBe(false);
    });

    it('accepts same version (idempotent)', () => {
      const questionId = 103;
      shouldUpdateQuestion(questionId, 10);
      const result = shouldUpdateQuestion(questionId, 10);
      expect(result).toBe(true);
    });

    it('handles multiple questions independently', () => {
      const question1 = 200;
      const question2 = 201;
      
      shouldUpdateQuestion(question1, 15);
      shouldUpdateQuestion(question2, 25);
      
      expect(shouldUpdateQuestion(question1, 14)).toBe(false);
      expect(shouldUpdateQuestion(question2, 26)).toBe(true);
      expect(shouldUpdateQuestion(question1, 16)).toBe(true);
    });
  });

  describe('allQuestions helper', () => {
    it('flattens board questions from categories', async () => {
      const { allQuestions } = await import('./state.svelte');
      
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
              { id: 1, text: 'Q1', type: 'text', special: false, answer: 'A1', points: 100, answered: false },
              { id: 2, text: 'Q2', type: 'text', special: false, answer: 'A2', points: 200, answered: false }
            ]
          },
          {
            id: 2,
            name: 'Category 2',
            order: 2,
            questions: [
              { id: 3, text: 'Q3', type: 'text', special: false, answer: 'A3', points: 300, answered: false }
            ]
          }
        ]
      };

      const questions = allQuestions(board);
      expect(questions).toHaveLength(3);
      expect(questions[0].id).toBe(1);
      expect(questions[1].id).toBe(2);
      expect(questions[2].id).toBe(3);
    });

    it('returns empty array for undefined board', async () => {
      const { allQuestions } = await import('./state.svelte');
      const questions = allQuestions(undefined);
      expect(questions).toEqual([]);
    });
  });
});
