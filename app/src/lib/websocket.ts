import { goto } from '$app/navigation';
import { get } from 'svelte/store';
import { AudioClient, Sound } from './audio.svelte';
import { allQuestions, ENDPOINT, UiMode, shouldUpdatePlayer, shouldUpdateQuestion } from './state.svelte';
import { gameState } from './stores';
import { recordPlayerAnswer as apiRecordPlayerAnswer, toggleQuestion as apiToggleQuestion, getBoard as apiGetBoard } from './api';

const CLIENT_ID = Math.random().toString(36);

export class GameWebSocket {
  private socket: WebSocket;
  private reconnectAttempts = 0;
  private maxReconnectTimeout = 1000;
  private reconnectTimeout = 100;
  private reconnectTimer?: number;

  constructor(private readonly gameId: string, private readonly mode: UiMode, private readonly audio?: AudioClient) {
    this.connect();
  }

  private connect() {
    this.socket = new WebSocket(`ws://${ENDPOINT}/ws/game/${this.gameId}/`);
    this.socket.onmessage = (event) => this.handleMessage(event);

    this.socket.onclose = () => {
      this.scheduleReconnect();
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      // onclose will be called automatically after onerror
    };

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.reconnectTimeout = 100;
      console.log('WebSocket connected');
      this.send({ type: 'join_game' });
    };
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;
    this.reconnectTimeout = Math.min(this.reconnectTimeout * 2, this.maxReconnectTimeout);

    console.log(`Reconnecting in ${this.reconnectTimeout}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.reconnectTimeout);
  }

  send(message: any) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            try {
                this.socket.send(JSON.stringify({
                  ...message,
                  clientId: CLIENT_ID,
                }));
            } catch (error) {
                console.error('Failed to send WebSocket message:', error);
            }
        } else {
            console.warn('Cannot send message: WebSocket is not open');
        }
    }

  handleMessage(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'join_game' && this.mode === UiMode.Host && data.clientId !== CLIENT_ID) {
      const currentState = get(gameState);
      if (currentState.currentBoard) {
        this.selectBoard(currentState.currentBoard);
      }
      currentState.visibleCategories.forEach(categoryId => this.revealCategory(categoryId))
      if (currentState.selectedQuestion) {
        this.selectQuestion(currentState.selectedQuestion);
      }
    } else if (data.type === 'reveal_category') {
      gameState.update((state) => {
        state.visibleCategories.add(data.categoryId);
        return state;
      });
    } else if (data.type === 'select_board') {
      const updateBoard = async () => {
        try {
          const board = await apiGetBoard(data.board);
          gameState.update((state) => {
            return state.currentBoard !== data.board ? state : ({
              ...state,
              answeredQuestions: new Set(allQuestions(board).filter(q => q.answered).map(q => q.id)),
              board,
              lastError: undefined
            });
          });
        } catch (error) {
          console.error('Error fetching board:', error);
          gameState.update((state) => ({
            ...state,
            lastError: `Failed to load board: ${error instanceof Error ? error.message : String(error)}`
          }));
        }
      }
      gameState.update((state) => {
        if (state.currentBoard !== data.board) {
          updateBoard();
          return ({
            ...state,
            visibleCategories: new Set(),
            selectedQuestion: undefined,
            currentBoard: data.board
          });
        } else {
          return state;
        }
      });
    } else if (data.type === 'select_question') {
      gameState.update((state) => ({
        ...state,
        selectedQuestion: data.question,
      }));
    } else if (data.type === 'toggle_question') {
      if (shouldUpdateQuestion(data.question_id, data.version)) {
        gameState.update((state) => {
          if (data.answered) {
            state.answeredQuestions.add(data.question_id);
          } else if (data.answered === false) {
            state.answeredQuestions.delete(data.question_id);
          }
          return state;
        });
      }
    } else if (data.type === 'toggle_buzzers') {
      gameState.update(state => ({
        ...state,
        buzzersEnabled: data.enabled
      }));
    } else if (data.type === 'buzzer_pressed') {
      if (data.buzzerId !== null) {
        this.audio?.play(Sound.Buzzer);
      }
      gameState.update(state => ({
        ...state,
        activeBuzzerId: data.buzzerId
      }));
    } else if (data.type === 'update_score') {
      if (shouldUpdatePlayer(data.player_id, data.version)) {
        gameState.update(state => ({
          ...state,
          scores: {
            ...state.scores,
            [data.player_id]: data.score,
          }
        }));
      }
    }
  }

  revealCategory(categoryId) {
    this.send({
      type: 'reveal_category',
      categoryId,
    });
  }

  selectBoard(board) {
    this.send({
      type: 'select_board',
      board
    });
  }

  selectQuestion(question) {
    this.send({
      type: 'select_question',
      question
    });
  }

  async updateQuestionStatus(questionId: number, answered: boolean) {
    try {
      await apiToggleQuestion(questionId, answered);
      // Update will come via WebSocket broadcast
      gameState.update((state) => ({ ...state, lastError: undefined }));
    } catch (error) {
      console.error('Failed to toggle question:', error);
      gameState.update((state) => ({
        ...state,
        lastError: `Failed to update question: ${error instanceof Error ? error.message : String(error)}`
      }));
      throw error;
    }
  }

  async recordPlayerAnswer(playerId: number, questionId: number, isCorrect: boolean, points?: number) {
    try {
      const boardId = Number(this.gameId);  // this.gameId is actually the board ID
      await apiRecordPlayerAnswer(boardId, playerId, questionId, isCorrect, points);
      // Update will come via WebSocket broadcast
      gameState.update((state) => ({ ...state, lastError: undefined }));
    } catch (error) {
      console.error('Failed to record answer:', error);
      gameState.update((state) => ({
        ...state,
        lastError: `Failed to record answer: ${error instanceof Error ? error.message : String(error)}`
      }));
      throw error;
    }
  }

  toggleBuzzers(enabled: boolean) {
    this.send({
      type: 'toggle_buzzers',
      enabled
    });
  }
}
