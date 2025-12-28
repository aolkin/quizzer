import { describe, it, expect, beforeEach } from 'vitest';
import { gameState } from './game-state.svelte';
import type { Board } from './state.svelte';

describe('GameStateManager', () => {
  beforeEach(() => {
    // Reset game state before each test
    gameState.reset();
    gameState.currentBoard = undefined;
    gameState.board = undefined;
    gameState.scores = {};
    gameState.visibleCategories = new Set();
    gameState.answeredQuestions = new Set();
    gameState.selectedQuestion = undefined;
  });

  describe('score management', () => {
    it('initializes with empty scores', () => {
      expect(gameState.scores).toEqual({});
    });

    it('updates individual player score', () => {
      gameState.updateScore(1, 100);
      expect(gameState.scores[1]).toBe(100);
    });

    it('updates multiple player scores independently', () => {
      gameState.updateScore(1, 100);
      gameState.updateScore(2, 200);
      expect(gameState.scores[1]).toBe(100);
      expect(gameState.scores[2]).toBe(200);
    });

    it('overwrites existing score', () => {
      gameState.updateScore(1, 100);
      gameState.updateScore(1, 300);
      expect(gameState.scores[1]).toBe(300);
    });

    it('sets all scores at once', () => {
      const scores = { 1: 100, 2: 200, 3: 300 };
      gameState.setScores(scores);
      expect(gameState.scores).toEqual(scores);
    });
  });

  describe('category visibility', () => {
    it('starts with no visible categories', () => {
      expect(gameState.visibleCategories.size).toBe(0);
    });

    it('reveals a category', () => {
      gameState.revealCategory(1);
      expect(gameState.visibleCategories.has(1)).toBe(true);
    });

    it('reveals multiple categories', () => {
      gameState.revealCategory(1);
      gameState.revealCategory(2);
      expect(gameState.visibleCategories.has(1)).toBe(true);
      expect(gameState.visibleCategories.has(2)).toBe(true);
      expect(gameState.visibleCategories.size).toBe(2);
    });
  });

  describe('board selection', () => {
    it('selects a board', () => {
      gameState.selectBoard(5);
      expect(gameState.currentBoard).toBe(5);
    });

    it('resets state when selecting new board', () => {
      gameState.revealCategory(1);
      gameState.selectQuestion(10);
      
      gameState.selectBoard(5);
      
      expect(gameState.visibleCategories.size).toBe(0);
      expect(gameState.selectedQuestion).toBeUndefined();
    });

    it('sets board data with answered questions', () => {
      const board: Board = {
        id: 1,
        name: 'Test Board',
        order: 1,
        categories: [
          {
            id: 1,
            name: 'Category 1',
            order: 1,
            questions: [
              { id: 1, text: 'Q1', type: 'text', special: false, answer: 'A1', points: 100, answered: true },
              { id: 2, text: 'Q2', type: 'text', special: false, answer: 'A2', points: 200, answered: false }
            ]
          }
        ]
      };

      gameState.setBoard(board, [1]);
      
      expect(gameState.board).toEqual(board);
      expect(gameState.answeredQuestions.has(1)).toBe(true);
      expect(gameState.answeredQuestions.has(2)).toBe(false);
    });
  });

  describe('question management', () => {
    it('selects a question', () => {
      gameState.selectQuestion(42);
      expect(gameState.selectedQuestion).toBe(42);
    });

    it('clears selected question', () => {
      gameState.selectQuestion(42);
      gameState.selectQuestion(undefined);
      expect(gameState.selectedQuestion).toBeUndefined();
    });

    it('marks question as answered', () => {
      gameState.markQuestionAnswered(1, true);
      expect(gameState.answeredQuestions.has(1)).toBe(true);
    });

    it('marks question as not answered', () => {
      gameState.markQuestionAnswered(1, true);
      gameState.markQuestionAnswered(1, false);
      expect(gameState.answeredQuestions.has(1)).toBe(false);
    });
  });

  describe('buzzer management', () => {
    it('starts with buzzers disabled', () => {
      expect(gameState.buzzersEnabled).toBe(false);
    });

    it('enables buzzers', () => {
      gameState.setBuzzersEnabled(true);
      expect(gameState.buzzersEnabled).toBe(true);
    });

    it('disables buzzers', () => {
      gameState.setBuzzersEnabled(true);
      gameState.setBuzzersEnabled(false);
      expect(gameState.buzzersEnabled).toBe(false);
    });

    it('sets active buzzer', () => {
      gameState.setActiveBuzzer(5);
      expect(gameState.activeBuzzerId).toBe(5);
    });

    it('clears active buzzer', () => {
      gameState.setActiveBuzzer(5);
      gameState.setActiveBuzzer(undefined);
      expect(gameState.activeBuzzerId).toBeUndefined();
    });
  });

  describe('reset', () => {
    it('clears all state', () => {
      gameState.revealCategory(1);
      gameState.markQuestionAnswered(1, true);
      gameState.selectQuestion(10);
      gameState.setBuzzersEnabled(true);
      gameState.setActiveBuzzer(5);

      gameState.reset();

      expect(gameState.visibleCategories.size).toBe(0);
      expect(gameState.answeredQuestions.size).toBe(0);
      expect(gameState.selectedQuestion).toBeUndefined();
      expect(gameState.buzzersEnabled).toBe(false);
      expect(gameState.activeBuzzerId).toBeUndefined();
    });
  });
});
