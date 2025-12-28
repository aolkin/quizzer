import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { GameWebSocket } from './websocket';
import { UiMode } from './state.svelte';
import { gameState } from './game-state.svelte';

// Create a proper mock WebSocket that maintains state
let currentMockSocket: any = null;

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
  simulateMessage(data: any) {
    if (this.onmessage) {
      const event = new MessageEvent('message', {
        data: JSON.stringify(data)
      });
      this.onmessage(event);
    }
  }
}

describe('GameWebSocket', () => {
  let originalWebSocket: typeof WebSocket;

  beforeEach(() => {
    // Store original WebSocket
    originalWebSocket = global.WebSocket as any;
    
    // Reset current mock
    currentMockSocket = null;
    
    // Replace WebSocket with mock
    global.WebSocket = MockWebSocket as any;

    // Reset game state
    gameState.reset();
    gameState.currentBoard = undefined;
    gameState.board = undefined;
    gameState.scores = {};
    gameState.visibleCategories = new Set();
    gameState.answeredQuestions = new Set();
  });

  afterEach(() => {
    // Restore original WebSocket
    global.WebSocket = originalWebSocket;
    currentMockSocket = null;
  });

  describe('connection', () => {
    it('connects to the correct URL', () => {
      new GameWebSocket('123', UiMode.Host);
      expect(currentMockSocket).toBeTruthy();
      expect(currentMockSocket.url).toBe('ws://quasar.local:8000/ws/game/123/');
    });

    it('sends join_game message on connection', () => {
      new GameWebSocket('123', UiMode.Host);
      
      // Trigger onopen callback
      if (currentMockSocket.onopen) {
        currentMockSocket.onopen(new Event('open'));
      }
      
      expect(currentMockSocket.sentMessages.length).toBeGreaterThan(0);
      const message = JSON.parse(currentMockSocket.sentMessages[0]);
      expect(message.type).toBe('join_game');
      expect(message.clientId).toBeDefined();
    });
  });

  describe('message handling', () => {
    it('handles reveal_category message', () => {
      new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.simulateMessage({
        type: 'reveal_category',
        categoryId: 5
      });
      
      expect(gameState.visibleCategories.has(5)).toBe(true);
    });

    it('handles select_question message', () => {
      new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.simulateMessage({
        type: 'select_question',
        question: 42
      });
      
      expect(gameState.selectedQuestion).toBe(42);
    });

    it('handles toggle_question message with version check', () => {
      new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.simulateMessage({
        type: 'toggle_question',
        question_id: 10,
        answered: true,
        version: 1
      });
      
      expect(gameState.answeredQuestions.has(10)).toBe(true);
    });

    it('handles update_score message with version check', () => {
      new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.simulateMessage({
        type: 'update_score',
        player_id: 1,
        score: 500,
        version: 1
      });
      
      expect(gameState.scores[1]).toBe(500);
    });

    it('handles toggle_buzzers message', () => {
      new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.simulateMessage({
        type: 'toggle_buzzers',
        enabled: true
      });
      
      expect(gameState.buzzersEnabled).toBe(true);
    });

    it('handles buzzer_pressed message', () => {
      new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.simulateMessage({
        type: 'buzzer_pressed',
        buzzerId: 3
      });
      
      expect(gameState.activeBuzzerId).toBe(3);
    });

    it('handles select_board message', () => {
      new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.simulateMessage({
        type: 'select_board',
        board: 5
      });
      
      expect(gameState.currentBoard).toBe(5);
    });
  });

  describe('sending messages', () => {
    it('sends reveal_category message', () => {
      const ws = new GameWebSocket('123', UiMode.Host);
      
      // Clear initial messages
      currentMockSocket.sentMessages = [];
      
      ws.revealCategory(7);
      
      expect(currentMockSocket.sentMessages.length).toBe(1);
      const message = JSON.parse(currentMockSocket.sentMessages[0]);
      expect(message.type).toBe('reveal_category');
      expect(message.categoryId).toBe(7);
    });

    it('sends select_board message', () => {
      const ws = new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.sentMessages = [];
      
      ws.selectBoard(8);
      
      const message = JSON.parse(currentMockSocket.sentMessages[0]);
      expect(message.type).toBe('select_board');
      expect(message.board).toBe(8);
    });

    it('sends select_question message', () => {
      const ws = new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.sentMessages = [];
      
      ws.selectQuestion(42);
      
      const message = JSON.parse(currentMockSocket.sentMessages[0]);
      expect(message.type).toBe('select_question');
      expect(message.question).toBe(42);
    });

    it('sends toggle_buzzers message', () => {
      const ws = new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.sentMessages = [];
      
      ws.toggleBuzzers(true);
      
      const message = JSON.parse(currentMockSocket.sentMessages[0]);
      expect(message.type).toBe('toggle_buzzers');
      expect(message.enabled).toBe(true);
    });

    it('includes clientId in all messages', () => {
      const ws = new GameWebSocket('123', UiMode.Host);
      
      currentMockSocket.sentMessages = [];
      ws.revealCategory(1);
      
      const message = JSON.parse(currentMockSocket.sentMessages[0]);
      expect(message.clientId).toBeDefined();
      expect(typeof message.clientId).toBe('string');
    });
  });

  describe('reconnection', () => {
    it('attempts to reconnect on disconnect', () => {
      vi.useFakeTimers();
      
      new GameWebSocket('123', UiMode.Host);
      const firstSocket = currentMockSocket;
      
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

