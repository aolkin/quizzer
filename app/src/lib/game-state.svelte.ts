import type { Board } from './state.svelte';
import type { GameWebSocket } from './websocket';

interface GameState {
  websocket?: GameWebSocket;
  currentBoard?: number;
  board?: Board;
  scores: Record<number, number>;
  visibleCategories: Set<number>;
  answeredQuestions: Set<number>;
  selectedQuestion?: number;
  buzzersEnabled: boolean;
  activeBuzzerId?: number;
}

class GameStateManager {
  websocket = $state<GameWebSocket | undefined>(undefined);
  currentBoard = $state<number | undefined>(undefined);
  board = $state<Board | undefined>(undefined);
  scores = $state<Record<number, number>>({});
  visibleCategories = $state<Set<number>>(new Set());
  answeredQuestions = $state<Set<number>>(new Set());
  selectedQuestion = $state<number | undefined>(undefined);
  buzzersEnabled = $state(false);
  activeBuzzerId = $state<number | undefined>(undefined);

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
    this.visibleCategories = new Set();
    this.selectedQuestion = undefined;
  }

  setBoard(board: Board, answeredQuestionIds: number[]) {
    this.board = board;
    this.answeredQuestions = new Set(answeredQuestionIds);
  }

  selectQuestion(questionId?: number) {
    this.selectedQuestion = questionId;
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

  reset() {
    this.visibleCategories = new Set();
    this.answeredQuestions = new Set();
    this.selectedQuestion = undefined;
    this.buzzersEnabled = false;
    this.activeBuzzerId = undefined;
  }
}

// Create a singleton instance
export const gameState = new GameStateManager();
