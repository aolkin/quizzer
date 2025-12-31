import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { GameWebSocket } from './websocket';
import { UiMode } from './state.svelte';
import { gameState } from './game-state.svelte';

// Create a proper mock WebSocket that maintains state
let currentMockSocket: MockWebSocket | null = null;

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.OPEN;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  sentMessages: string[] = [];

  constructor(public url: string) {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    currentMockSocket = this;
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    this.sentMessages.push(data);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new Event('close'));
    }
  }

  // Helper method for testing
  simulateMessage(data: object) {
    if (this.onmessage) {
      const event = new MessageEvent('message', {
        data: JSON.stringify(data),
      });
      this.onmessage(event);
    }
  }
}

describe('GameWebSocket', () => {
  let originalWebSocket: typeof WebSocket;

  beforeEach(() => {
    // Store original WebSocket
    originalWebSocket = global.WebSocket as typeof WebSocket;

    // Reset current mock
    currentMockSocket = null;

    // Replace WebSocket with mock
    global.WebSocket = MockWebSocket as unknown as typeof WebSocket;

    // Reset game state
    gameState.reset();
    gameState.currentBoard = undefined;
    gameState.board = undefined;
    gameState.scores = {};
  });

  afterEach(() => {
    // Restore original WebSocket
    global.WebSocket = originalWebSocket;
    currentMockSocket = null;
  });

  describe('connection', () => {
    it('sends join_game message on connection', () => {
      new GameWebSocket('123', UiMode.Host);

      // Trigger onopen callback
      if (currentMockSocket!.onopen) {
        currentMockSocket!.onopen(new Event('open'));
      }

      expect(currentMockSocket!.sentMessages.length).toBeGreaterThan(0);
      const message = JSON.parse(currentMockSocket!.sentMessages[0]);
      expect(message.type).toBe('join_game');
      expect(message.clientId).toBeDefined();
    });
  });

  describe('message handling', () => {
    it('handles update_score with version check', () => {
      new GameWebSocket('123', UiMode.Host);

      currentMockSocket!.simulateMessage({
        type: 'update_score',
        player_id: 1,
        score: 500,
        version: 1,
      });

      expect(gameState.scores[1]).toBe(500);
    });

    it('handles toggle_question with version check', () => {
      new GameWebSocket('123', UiMode.Host);

      currentMockSocket!.simulateMessage({
        type: 'toggle_question',
        question_id: 10,
        answered: true,
        version: 1,
      });

      expect(gameState.answeredQuestions.has(10)).toBe(true);
    });

    it('updates game state for UI messages', () => {
      new GameWebSocket('123', UiMode.Host);

      currentMockSocket!.simulateMessage({ type: 'reveal_category', categoryId: 5 });
      expect(gameState.visibleCategories.has(5)).toBe(true);

      currentMockSocket!.simulateMessage({ type: 'select_question', question: 42 });
      expect(gameState.selectedQuestion).toBe(42);

      currentMockSocket!.simulateMessage({ type: 'buzzer_pressed', buzzerId: 3 });
      expect(gameState.activeBuzzerId).toBe(3);
    });

    it('handles client_connection_status for all client types', () => {
      new GameWebSocket('123', UiMode.Host);

      currentMockSocket!.simulateMessage({
        type: 'client_connection_status',
        client_type: 'buzzer',
        client_id: 'buzzer-1',
        connected: true,
      });

      expect(gameState.clientConnections.get('buzzer:buzzer-1')?.connected).toBe(true);

      currentMockSocket!.simulateMessage({
        type: 'client_connection_status',
        client_type: 'osc',
        client_id: 'osc-lighting',
        connected: true,
      });

      expect(gameState.clientConnections.get('osc:osc-lighting')?.connected).toBe(true);
    });
  });

  describe('sending messages', () => {
    it('sends coordination messages with clientId', () => {
      const ws = new GameWebSocket('123', UiMode.Host);
      currentMockSocket!.sentMessages = [];

      ws.revealCategory(7);
      const msg1 = JSON.parse(currentMockSocket!.sentMessages[0]);
      expect(msg1.type).toBe('reveal_category');
      expect(msg1.categoryId).toBe(7);
      expect(msg1.clientId).toBeDefined();

      ws.selectQuestion(42);
      const msg2 = JSON.parse(currentMockSocket!.sentMessages[1]);
      expect(msg2.type).toBe('select_question');
      expect(msg2.question).toBe(42);
    });
  });

  describe('reconnection', () => {
    it('attempts to reconnect on disconnect', () => {
      vi.useFakeTimers();

      new GameWebSocket('123', UiMode.Host);
      const firstSocket = currentMockSocket!;

      // Simulate disconnect
      firstSocket.close();

      // Fast-forward time to trigger reconnection
      vi.advanceTimersByTime(150);

      // A new socket should be created
      expect(currentMockSocket).toBeTruthy();
      expect(currentMockSocket).not.toBe(firstSocket);

      vi.useRealTimers();
    });
  });
});
