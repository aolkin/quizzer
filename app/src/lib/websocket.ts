import { AudioClient, Sound } from './audio.svelte';
import {
  allQuestions,
  ENDPOINT,
  UiMode,
  shouldUpdatePlayer,
  shouldUpdateQuestion,
} from './state.svelte';
import { gameState } from './game-state.svelte';
import { getBoard as apiGetBoard } from './api';

const CLIENT_ID = Math.random().toString(36);

export interface MessageRecipient {
  channel_id?: string;
  client_id?: string;
  client_type?: string;
}

export class GameWebSocket {
  private socket: WebSocket;
  private reconnectAttempts = 0;
  private maxReconnectTimeout = 1000;
  private reconnectTimeout = 100;

  constructor(
    private readonly gameId: string,
    private readonly mode: UiMode,
    private readonly audio?: AudioClient,
  ) {
    this.socket = this.createSocket();
  }

  private createSocket(): WebSocket {
    const socket = new WebSocket(`ws://${ENDPOINT}/ws/game/${this.gameId}/`);
    socket.onmessage = (event) => this.handleMessage(event);

    socket.onclose = () => {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.reconnectTimeout = Math.min(this.reconnectTimeout * 2, this.maxReconnectTimeout);
        this.reconnect();
      }, this.reconnectTimeout);
    };

    socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.reconnectTimeout = 100;
      this.send({ type: 'join_game' });
    };

    return socket;
  }

  private reconnect() {
    this.socket = this.createSocket();
  }

  send(message: Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(
        JSON.stringify({
          ...message,
          clientId: CLIENT_ID,
        }),
      );
    } else {
      throw new Error('WebSocket is closed');
    }
  }

  sendTo(recipient: MessageRecipient, message: Record<string, unknown>) {
    this.send({
      ...message,
      recipient,
    });
  }

  handleMessage(event: MessageEvent) {
    const data = JSON.parse(event.data);
    if (data.type === 'join_game' && this.mode === UiMode.Host && data.clientId !== CLIENT_ID) {
      if (gameState.currentBoard) {
        this.selectBoard(gameState.currentBoard);
      }
      gameState.visibleCategories.forEach((categoryId) => this.revealCategory(categoryId));
      if (gameState.selectedQuestion) {
        this.selectQuestion(gameState.selectedQuestion);
      }
    } else if (data.type === 'reveal_category') {
      gameState.revealCategory(data.categoryId);
    } else if (data.type === 'select_board') {
      if (gameState.currentBoard !== data.board) {
        gameState.selectBoard(data.board);
        // Fetch and set board data asynchronously
        (async () => {
          try {
            const board = await apiGetBoard(data.board);
            // Only update if we're still on the same board (handles race conditions)
            if (gameState.currentBoard === data.board) {
              // Extract answered question IDs from API response (answered field only used for initial load)
              const answeredQuestionIds = allQuestions(board)
                .filter((q) => (q as { answered?: boolean }).answered)
                .map((q) => q.id);
              gameState.setBoard(board, answeredQuestionIds);
            }
          } catch (error) {
            console.error('Error fetching board:', error);
          }
        })();
      }
    } else if (data.type === 'select_question') {
      gameState.selectQuestion(data.question, data.slideIndex);
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
    } else if (data.type === 'client_connection_status') {
      // Track all client types, not just buzzer
      gameState.setClientConnection(data.client_type, data.client_id, data.connected);

      // Keep existing buzzer-specific logic for backwards compatibility
      if (data.client_type === 'buzzer' && data.connected && this.mode === UiMode.Host) {
        this.toggleBuzzers(gameState.buzzersEnabled);
      }
    } else if (data.type === 'update_score') {
      if (shouldUpdatePlayer(data.player_id, data.version)) {
        gameState.updateScore(data.player_id, data.score);
      }
    }
  }

  revealCategory(categoryId: number) {
    this.send({
      type: 'reveal_category',
      categoryId,
    });
  }

  selectBoard(board: number) {
    this.send({
      type: 'select_board',
      board,
    });
  }

  selectQuestion(question: number | undefined, slideIndex: number = 0) {
    this.send({
      type: 'select_question',
      question,
      slideIndex,
    });
  }

  toggleBuzzers(enabled: boolean) {
    this.send({
      type: 'toggle_buzzers',
      enabled,
    });
  }

  setBuzzerLogLevel(level: 'DEBUG' | 'WARN') {
    this.send({
      type: 'buzzer_set_log_level',
      level,
    });
  }
}
