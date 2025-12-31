import { SvelteSet, SvelteMap } from 'svelte/reactivity';
import type { Board } from './state.svelte';
import type { GameWebSocket } from './websocket';

export interface ClientConnection {
  clientType: string;
  clientId: string | null;
  connected: boolean;
  lastSeen: number; // timestamp
  latency?: number; // milliseconds (optional)
}

class GameStateManager {
  websocket = $state<GameWebSocket | undefined>(undefined);
  currentBoard = $state<number | undefined>(undefined);
  board = $state<Board | undefined>(undefined);
  scores = $state<Record<number, number>>({});
  visibleCategories = new SvelteSet<number>();
  answeredQuestions = new SvelteSet<number>();
  selectedQuestion = $state<number | undefined>(undefined);
  currentSlideIndex = $state(0);
  buzzersEnabled = $state(false);
  activeBuzzerId = $state<number | undefined>(undefined);
  // Map of client connections: `${client_type}:${client_id}` -> ClientConnection
  clientConnections = new SvelteMap<string, ClientConnection>();

  // Methods to update state (separation of concerns)
  setWebsocket(websocket: GameWebSocket) {
    this.websocket = websocket;
  }

  setScores(scores: Record<number, number>) {
    this.scores = scores;
  }

  updateScore(playerId: number, score: number) {
    this.scores = {
      ...this.scores,
      [playerId]: score,
    };
  }

  revealCategory(categoryId: number) {
    this.visibleCategories.add(categoryId);
  }

  selectBoard(boardId: number) {
    this.currentBoard = boardId;
    // Reset state when selecting a new board
    this.visibleCategories.clear();
    this.selectedQuestion = undefined;
  }

  setBoard(board: Board, answeredQuestionIds: number[]) {
    this.board = board;
    this.answeredQuestions.clear();
    answeredQuestionIds.forEach((id) => this.answeredQuestions.add(id));
  }

  selectQuestion(questionId?: number, slideIndex: number = 0) {
    this.selectedQuestion = questionId;
    this.currentSlideIndex = slideIndex;
  }

  markQuestionAnswered(questionId: number, answered: boolean) {
    if (answered) {
      this.answeredQuestions.add(questionId);
    } else {
      this.answeredQuestions.delete(questionId);
    }
  }

  setBuzzersEnabled(enabled: boolean) {
    this.buzzersEnabled = enabled;
  }

  setActiveBuzzer(buzzerId?: number) {
    this.activeBuzzerId = buzzerId;
  }

  setClientConnection(clientType: string, clientId: string | null, connected: boolean) {
    const key = `${clientType}:${clientId || 'default'}`;
    this.clientConnections.set(key, {
      clientType,
      clientId,
      connected,
      lastSeen: Date.now(),
      latency: this.clientConnections.get(key)?.latency,
    });
  }

  setClientLatency(clientType: string, clientId: string | null, latency: number) {
    const key = `${clientType}:${clientId || 'default'}`;
    const existing = this.clientConnections.get(key);
    if (existing) {
      existing.latency = latency;
      this.clientConnections.set(key, existing);
    }
  }

  reset() {
    this.visibleCategories.clear();
    this.answeredQuestions.clear();
    this.selectedQuestion = undefined;
    this.currentSlideIndex = 0;
    this.buzzersEnabled = false;
    this.activeBuzzerId = undefined;
    this.clientConnections.clear();
  }
}

// Create a singleton instance
export const gameState = new GameStateManager();
export type { GameStateManager };
