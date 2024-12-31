import { goto } from '$app/navigation';
import { get } from 'svelte/store';
import { allQuestions, ENDPOINT, UiMode } from './state.svelte';
import { gameState } from './stores';

const CLIENT_ID = Math.random().toString(36);

export class GameWebSocket {
  private socket: WebSocket;
  private reconnectAttempts = 0;
  private maxReconnectTimeout = 1000;
  private reconnectTimeout = 100;

  constructor(private readonly gameId: string, private readonly mode: UiMode) {
    this.connect();
  }

  private connect() {
    this.socket = new WebSocket(`ws://${ENDPOINT}/ws/game/${this.gameId}/`);
    this.socket.onmessage = (event) => this.handleMessage(event);

    this.socket.onclose = () => {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.reconnectTimeout = Math.min(this.reconnectTimeout * 2, this.maxReconnectTimeout);
        this.connect();
      }, this.reconnectTimeout);
    };

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.reconnectTimeout = 100;
      this.send({ type: 'join_game' });
    };
  }

  send(message: any) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
              ...message,
              clientId: CLIENT_ID,
            }));
        } else {
          throw new Error('WebSocket is closed');
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
        const response = await fetch(`http://${ENDPOINT}/api/board/${data.board}/`);
        const board = await response.json();
        gameState.update((state) => {
          return state.currentBoard !== data.board ? state : ({
            ...state,
            answeredQuestions: new Set(allQuestions(board).filter(q => q.answered).map(q => q.id)),
            board
          });
        });
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
      gameState.update((state) => {
        if (data.answered) {
          state.answeredQuestions.add(data.questionId);
        } else if (data.answered === false) {
          state.answeredQuestions.delete(data.questionId);
        }
        return state;
      });
    } else if (data.type === 'toggle_buzzers') {
      gameState.update(state => ({
        ...state,
        buzzersEnabled: data.enabled
      }));
    } else if (data.type === 'buzzer_pressed') {
      gameState.update(state => ({
        ...state,
        activeBuzzerId: data.buzzerId
      }));
    } else if (data.type === 'update_score') {
      gameState.update(state => ({
        ...state,
        scores: {
          ...state.scores,
          [data.playerId]: data.score,
        }
      }));
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

  updateQuestionStatus(questionId: number, answered: boolean) {
    this.send({
      type: 'toggle_question',
      questionId,
      answered
    });
  }

  recordPlayerAnswer(playerId: number, questionId: number, isCorrect: boolean, points?: number) {
    this.socket.send(JSON.stringify({
      type: 'record_answer',
      playerId,
      questionId,
      isCorrect,
      points
    }));
  }

  toggleBuzzers(enabled: boolean) {
    this.socket.send(JSON.stringify({
      type: 'toggle_buzzers',
      enabled
    }));
  }
}
