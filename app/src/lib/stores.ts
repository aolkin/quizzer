import { type Writable, writable } from 'svelte/store';
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

export const gameState: Writable<GameState> = writable({
  visibleCategories: new Set(),
  answeredQuestions: new Set(),
  scores: {},
  buzzersEnabled: false,
});
