import { goto } from '$app/navigation';
import { AudioClient, Sound } from './audio.svelte';
import { allQuestions, ENDPOINT, UiMode, shouldUpdatePlayer, shouldUpdateQuestion } from './state.svelte';
import { gameState } from './game-state.svelte';
import { recordPlayerAnswer as apiRecordPlayerAnswer, toggleQuestion as apiToggleQuestion, getBoard as apiGetBoard } from './api';

const CLIENT_ID = Math.random().toString(36);

export class GameWebSocket {
  private socket: WebSocket;
  private reconnectAttempts = 0;
  private maxReconnectTimeout = 1000;
  private reconnectTimeout = 100;

  constructor(private readonly gameId: string, private readonly mode: UiMode, private readonly audio?: AudioClient) {
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
      if (gameState.currentBoard) {
        this.selectBoard(gameState.currentBoard);
      }
      gameState.visibleCategories.forEach(categoryId => this.revealCategory(categoryId))
      if (gameState.selectedQuestion) {
        this.selectQuestion(gameState.selectedQuestion);
      }
    } else if (data.type === 'reveal_category') {
      gameState.revealCategory(data.categoryId);
    } else if (data.type === 'select_board') {
      const updateBoard = async () => {
        try {
          const board = await apiGetBoard(data.board);
          if (gameState.currentBoard === data.board) {
            const answeredQuestionIds = allQuestions(board).filter(q => q.answered).map(q => q.id);
            gameState.setBoard(board, answeredQuestionIds);
          }
        } catch (error) {
          console.error('Error fetching board:', error);
        }
      }
      if (gameState.currentBoard !== data.board) {
        gameState.selectBoard(data.board);
        updateBoard();
      }
    } else if (data.type === 'select_question') {
      gameState.selectQuestion(data.question);
    } else if (data.type === 'toggle_question') {
      if (shouldUpdateQuestion(data.question_id, data.version)) {
        gameState.markQuestionAnswered(data.question_id, data.answered);
      }
    } else if (data.type === 'toggle_buzzers') {
      gameState.setBuzzersEnabled(data.enabled);
    } else if (data.type === 'buzzer_pressed') {
      if (data.buzzerId !== null) {
        this.audio?.play(Sound.Buzzer);
      }
      gameState.setActiveBuzzer(data.buzzerId);
    } else if (data.type === 'update_score') {
      if (shouldUpdatePlayer(data.player_id, data.version)) {
        gameState.updateScore(data.player_id, data.score);
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
    } catch (error) {
      console.error('Failed to toggle question:', error);
      throw error;
    }
  }

  async recordPlayerAnswer(playerId: number, questionId: number, isCorrect: boolean, points?: number) {
    try {
      const boardId = Number(this.gameId);  // this.gameId is actually the board ID
      await apiRecordPlayerAnswer(boardId, playerId, questionId, isCorrect, points);
      // Update will come via WebSocket broadcast
    } catch (error) {
      console.error('Failed to record answer:', error);
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
