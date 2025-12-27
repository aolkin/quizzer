# Implement REST API with versioning for database mutations

## Summary

This PR implements a hybrid REST + WebSocket architecture that moves database mutations from WebSocket to REST APIs while preserving WebSocket for real-time coordination. The key innovation is version tracking to prevent race conditions from out-of-order updates.

## Problem

The previous WebSocket-only approach had several issues:
- **No error handling**: Mutations crashed the connection instead of returning errors
- **Race conditions**: Multiple rapid updates could arrive out-of-order, causing temporary UI glitches
- **Stuck states**: Clients could wait indefinitely for broadcasts that never arrive
- **No retry mechanism**: Failed mutations were silently lost

## Solution

### Backend Changes

**Database Schema:**
- Added `score_version` to `Player` model
- Added `state_version` to `Question` model
- Both fields increment atomically on each update using `F('field') + 1`

**Service Layer (`game/services.py`):**
- Created dataclasses for structured results:
  - `PlayerAnswerResult(player_id, score, version)`
  - `QuestionStatusResult(question_id, answered, version)`
- Updated `record_player_answer()` to return versioned result
- Updated `update_question_status()` to return versioned result
- Used `select_for_update()` for atomic locking during version increments

**REST API Endpoints (`game/views.py`):**
- `POST /api/games/{game_id}/answers/` - Record player answers
  - Validates request, calls service layer, broadcasts to WebSocket, returns response
- `PATCH /api/questions/{question_id}/` - Toggle question status
  - Validates request, calls service layer, broadcasts to WebSocket, returns response
- Both endpoints use HTTP status codes (no redundant "success" fields)
- Both broadcast updates with version numbers to all WebSocket clients

**WebSocket Consumer (`game/consumers.py`):**
- Removed all mutation handling (`record_answer`, `toggle_question`)
- Simplified to pure relay pattern for coordination messages
- Still receives and forwards broadcasts from REST API to clients

### Frontend Changes

**Version Tracking (`app/src/lib/state.svelte.ts`):**
- `shouldUpdatePlayer(playerId, version)` - Checks if update is newer than current
- `shouldUpdateQuestion(questionId, version)` - Checks if update is newer than current
- Maps track latest version for each player/question
- Logs when stale updates are ignored

**REST API Client (`app/src/lib/api.ts` - NEW):**
- `recordPlayerAnswer()` - Calls POST endpoint with error handling
- `toggleQuestion()` - Calls PATCH endpoint with error handling
- Both throw descriptive errors on failure

**WebSocket Client (`app/src/lib/websocket.ts`):**
- Methods now use REST API for mutations instead of WebSocket
- Broadcast handlers check versions before applying updates
- All updates (including from requestor) come via WebSocket broadcasts

## Architecture

```
Mutation Flow:
  Client → REST API → Service Layer → Database
  REST API → Channel Layer → All WebSocket clients (broadcast with version)
  REST API → HTTP Response → Original client

Coordination Flow:
  Client → WebSocket → All WebSocket clients (relay)
```

## Benefits

✅ **Proper error handling** - HTTP status codes (404, 400, 500) with descriptive messages
✅ **No stuck states** - REST API always responds, even on error
✅ **Race condition protection** - Version numbers prevent out-of-order updates
✅ **Still real-time** - Broadcasts keep all clients synchronized
✅ **Easy to test** - REST endpoints are simpler to test than WebSocket
✅ **Built-in retry** - Failed API calls can be retried
✅ **Clean separation** - WebSocket for coordination, REST for persistence

## Testing

**Backend:**
- ✅ All Python imports successful
- ✅ Django system check passed
- ✅ Database migration applied successfully

**Manual testing needed:**
- [ ] Record answers and verify scores update across clients
- [ ] Toggle questions and verify state syncs across clients
- [ ] Test rapid successive updates (race condition scenario)
- [ ] Test with invalid data to verify error handling
- [ ] Open multiple browser windows and verify synchronization

## Breaking Changes

This is a **breaking change** - the frontend and backend must be deployed together. Old frontend clients will not work with the new backend (mutations via WebSocket no longer supported).

## Migration

1. Backend changes are backward-incompatible
2. Deploy backend first (will break old frontend)
3. Deploy frontend immediately after
4. Database migration runs automatically on backend deployment
