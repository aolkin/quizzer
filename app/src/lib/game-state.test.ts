import { describe, it, expect, beforeEach } from 'vitest';
import { gameState } from './game-state.svelte';
import type { Board } from './state.svelte';

describe('GameStateManager', () => {
  beforeEach(() => {
    gameState.reset();
    gameState.currentBoard = undefined;
    gameState.board = undefined;
    gameState.scores = {};
    gameState.visibleCategories = new Set();
    gameState.answeredQuestions = new Set();
    gameState.selectedQuestion = undefined;
  });

  it('resets state when selecting new board', () => {
    gameState.revealCategory(1);
    gameState.selectQuestion(10);
    
    gameState.selectBoard(5);
    
    expect(gameState.visibleCategories.size).toBe(0);
    expect(gameState.selectedQuestion).toBeUndefined();
  });

  it('tracks answered questions via setBoard', () => {
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
    
    expect(gameState.answeredQuestions.has(1)).toBe(true);
    expect(gameState.answeredQuestions.has(2)).toBe(false);
  });

  it('toggles question answered state', () => {
    gameState.markQuestionAnswered(1, true);
    expect(gameState.answeredQuestions.has(1)).toBe(true);
    
    gameState.markQuestionAnswered(1, false);
    expect(gameState.answeredQuestions.has(1)).toBe(false);
  });

  it('clears all state on reset', () => {
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
