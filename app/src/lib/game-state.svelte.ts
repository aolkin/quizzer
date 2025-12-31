import { SvelteSet } from 'svelte/reactivity';
import type { Board } from './state.svelte';
import type { GameWebSocket } from './websocket';

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
  buzzerConnected = $state(false);

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

  selectQuestion(questionId?: number) {
    this.selectedQuestion = questionId;
    this.currentSlideIndex = 0;
  }

  setCurrentSlide(index: number) {
    this.currentSlideIndex = index;
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

  setBuzzerConnected(connected: boolean) {
    this.buzzerConnected = connected;
  }

  reset() {
    this.visibleCategories.clear();
    this.answeredQuestions.clear();
    this.selectedQuestion = undefined;
    this.currentSlideIndex = 0;
    this.buzzersEnabled = false;
    this.activeBuzzerId = undefined;
    this.buzzerConnected = false;
  }
}

// Create a singleton instance
export const gameState = new GameStateManager();
