# Refactor Frontend API Methods Out of WebSocket Class

## Problem

The `GameWebSocket` class in `app/src/lib/websocket.ts` currently mixes two concerns:

1. **WebSocket communication** (real-time message passing)
2. **REST API calls** (database mutations)

Methods like `recordPlayerAnswer()` and `updateQuestionStatus()` call REST API endpoints directly from within the WebSocket class, which violates separation of concerns.

## Current Structure

```typescript
// app/src/lib/websocket.ts
class GameWebSocket {
  // WebSocket methods (appropriate)
  send(message) { ... }
  selectBoard(board) { ... }
  selectQuestion(question) { ... }
  toggleBuzzers(enabled) { ... }

  // REST API methods (should be elsewhere)
  async recordPlayerAnswer(...) {
    await apiRecordPlayerAnswer(...);  // Calls REST API
  }
  async updateQuestionStatus(...) {
    await apiToggleQuestion(...);  // Calls REST API
  }
}
```

## Proposed Solutions

### Option 1: Move API Calls to Game State

Move the REST API orchestration to `game-state.svelte.ts`:

```typescript
// game-state.svelte.ts
class GameState {
  async recordAnswer(playerId, questionId, isCorrect, points?) {
    const boardId = this.currentBoard;
    if (!boardId) throw new Error('No board selected');
    await apiRecordPlayerAnswer(boardId, playerId, questionId, isCorrect, points);
  }
}
```

Components would call `gameState.recordAnswer()` instead of `gameState.websocket.recordPlayerAnswer()`.

### Option 2: Create Separate Game Actions Module

Create a dedicated module for game actions that coordinates between state and APIs:

```typescript
// app/src/lib/game-actions.ts
export async function recordAnswer(playerId, questionId, isCorrect, points?) {
  const boardId = gameState.currentBoard;
  if (!boardId) throw new Error('No board selected');
  await apiRecordPlayerAnswer(boardId, playerId, questionId, isCorrect, points);
}
```

### Option 3: Thin WebSocket Wrapper

Keep WebSocket class purely for WebSocket operations, have components call API functions directly:

```typescript
// Component
import { recordPlayerAnswer } from '$lib/api';

async function handleAnswer() {
  await recordPlayerAnswer(gameState.currentBoard, playerId, questionId, isCorrect);
}
```

## Recommendation

**Option 1** seems cleanest since `gameState` already manages the current board and other state needed for API calls. This keeps the WebSocket class focused on real-time communication only.

## Priority

**Low** - Current structure works, this is a code organization improvement for maintainability.
