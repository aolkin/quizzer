import { describe, it, expect, beforeEach } from 'vitest';
import { gameState } from './game-state.svelte';
import type { Board } from './state.svelte';

describe('GameStateManager', () => {
  beforeEach(() => {
    gameState.reset();
    gameState.currentBoard = undefined;
    gameState.board = undefined;
    gameState.scores = {};
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
    gameState.setClientConnection('buzzer', 'test-buzzer', true);

    gameState.reset();

    expect(gameState.visibleCategories.size).toBe(0);
    expect(gameState.answeredQuestions.size).toBe(0);
    expect(gameState.selectedQuestion).toBeUndefined();
    expect(gameState.buzzersEnabled).toBe(false);
    expect(gameState.activeBuzzerId).toBeUndefined();
    expect(gameState.clientConnections.size).toBe(0);
  });

  it('tracks client connections', () => {
    gameState.setClientConnection('buzzer', 'buzzer-1', true);
    gameState.setClientConnection('osc', 'osc-lighting', true);

    expect(gameState.clientConnections.size).toBe(2);
    expect(gameState.clientConnections.get('buzzer:buzzer-1')?.connected).toBe(true);
    expect(gameState.clientConnections.get('osc:osc-lighting')?.connected).toBe(true);
  });

  it('provides backwards-compatible buzzerConnected getter', () => {
    expect(gameState.buzzerConnected).toBe(false);

    gameState.setClientConnection('buzzer', 'buzzer-1', true);
    expect(gameState.buzzerConnected).toBe(true);

    gameState.setClientConnection('buzzer', 'buzzer-1', false);
    expect(gameState.buzzerConnected).toBe(false);
  });

  it('handles client latency updates', () => {
    gameState.setClientConnection('buzzer', 'buzzer-1', true);
    gameState.setClientLatency('buzzer', 'buzzer-1', 50);

    const client = gameState.clientConnections.get('buzzer:buzzer-1');
    expect(client?.latency).toBe(50);
  });
});
