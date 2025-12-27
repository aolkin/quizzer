# Implementation Plan: REST API with Versioning (To-Do #3)

## Overview
Migrate database-mutating operations from WebSocket to REST APIs while preserving the WebSocket relay pattern for ephemeral coordination. This will add proper error handling, prevent race conditions, and eliminate stuck states.

## Current Architecture Analysis

### Existing Components
- **Models** (`service/game/models.py`):
  - `Player`: Tracks team membership, buzzer assignment, score (calculated from answers)
  - `Question`: Stores question data and `answered` boolean
  - `PlayerAnswer`: Junction table tracking player responses

- **Services** (`service/game/services.py`):
  - `record_player_answer()`: Creates/updates/deletes PlayerAnswer with undo logic
  - `update_question_status()`: Toggles Question.answered field

- **WebSocket Consumer** (`service/game/consumers.py`):
  - Currently handles BOTH mutations (`record_answer`, `toggle_question`) AND coordination messages
  - Mutations are processed via `database_sync_to_async` calls to services
  - Broadcasts score updates after mutations

- **Frontend** (`app/src/lib/websocket.ts`):
  - `recordPlayerAnswer()`: Sends `record_answer` via WebSocket (lines 157-165)
  - `updateQuestionStatus()`: Sends `toggle_question` via WebSocket (lines 149-155)
  - Handles `update_score` and `toggle_question` broadcasts (lines 95-125)

### Problems Being Solved
1. **No error handling**: WebSocket mutations crash connection on errors
2. **Race conditions**: Multiple rapid updates can arrive out-of-order
3. **Stuck states**: Client waits for broadcast that may never arrive
4. **No retry mechanism**: Failed mutations are lost

## Implementation Plan

### Phase 1: Database Schema Changes

#### 1.1 Add Version Fields to Models
**File**: `service/game/models.py`

Add version tracking fields:
```python
class Player(models.Model):
    # ... existing fields ...
    score_version = models.IntegerField(default=0)

class Question(models.Model):
    # ... existing fields ...
    state_version = models.IntegerField(default=0)
```

**Why**: Enables atomic version increments to detect out-of-order updates

#### 1.2 Create Database Migration
**Command**: `python manage.py makemigrations game`

**Migration will**:
- Add `Player.score_version` with default=0
- Add `Question.state_version` with default=0
- Backfill existing records with version=0

### Phase 2: Update Service Layer

#### 2.1 Modify `record_player_answer()` to Return Version
**File**: `service/game/services.py`

Current signature:
```python
def record_player_answer(...) -> int:
    # Returns only score
```

New signature:
```python
def record_player_answer(...) -> dict:
    # Returns {'score': int, 'version': int}
```

Implementation changes:
1. Get player with `select_for_update()` for atomic lock
2. After score update, increment version: `player.score_version = F('score_version') + 1`
3. Save and refresh to get new version number
4. Return dict with both score and version

**Why**: Atomic version increment prevents race conditions

#### 2.2 Modify `update_question_status()` to Return Version
**File**: `service/game/services.py`

Current signature:
```python
def update_question_status(...) -> None:
```

New signature:
```python
def update_question_status(...) -> dict:
    # Returns {'answered': bool, 'version': int}
```

Implementation changes:
1. Get question with `select_for_update()` for atomic lock
2. Update answered status
3. Increment version: `question.state_version = F('state_version') + 1`
4. Save and refresh
5. Return dict with answered status and version

### Phase 3: Create REST API Endpoints

#### 3.1 Add Answer Recording Endpoint
**File**: `service/game/views.py`

Endpoint: `POST /api/games/{game_id}/answers/`

Request body:
```json
{
  "playerId": 123,
  "questionId": 456,
  "isCorrect": true,
  "points": 400  // optional
}
```

Response (200 OK):
```json
{
  "success": true,
  "score": 600,
  "version": 42
}
```

Error responses:
- `404 Not Found`: Player or Question doesn't exist
- `400 Bad Request`: Invalid data (missing fields, wrong types)
- `500 Internal Server Error`: Database error

Implementation:
1. Validate request data
2. Call `services.record_player_answer()`
3. Broadcast update via channel layer
4. Return response with score and version

**Broadcast message**:
```json
{
  "type": "update_score",
  "playerId": 123,
  "score": 600,
  "version": 42
}
```

#### 3.2 Add Question Toggle Endpoint
**File**: `service/game/views.py`

Endpoint: `PATCH /api/questions/{question_id}/`

Request body:
```json
{
  "answered": true
}
```

Response (200 OK):
```json
{
  "success": true,
  "answered": true,
  "version": 15
}
```

Error responses:
- `404 Not Found`: Question doesn't exist
- `400 Bad Request`: Invalid data

Implementation:
1. Validate request data
2. Call `services.update_question_status()`
3. Broadcast update via channel layer
4. Return response with status and version

**Broadcast message**:
```json
{
  "type": "toggle_question",
  "questionId": 456,
  "answered": true,
  "version": 15
}
```

#### 3.3 Create Serializers
**File**: `service/game/serializers.py`

Add request/response serializers:
```python
class RecordAnswerRequestSerializer(serializers.Serializer):
    playerId = serializers.IntegerField()
    questionId = serializers.IntegerField()
    isCorrect = serializers.BooleanField()
    points = serializers.IntegerField(required=False, allow_null=True)

class RecordAnswerResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    score = serializers.IntegerField()
    version = serializers.IntegerField()

class ToggleQuestionRequestSerializer(serializers.Serializer):
    answered = serializers.BooleanField()

class ToggleQuestionResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    answered = serializers.BooleanField()
    version = serializers.IntegerField()
```

#### 3.4 Update URL Configuration
**File**: `service/quizzer/urls.py`

Add new routes:
```python
urlpatterns = [
    # ... existing routes ...
    path('api/games/<int:game_id>/answers/', record_answer),
    path('api/questions/<int:question_id>/', toggle_question),
]
```

### Phase 4: Update WebSocket Consumer

#### 4.1 Remove Mutation Handling from Consumer
**File**: `service/game/consumers.py`

Current behavior:
- `receive_json()` handles `record_answer` and `toggle_question` directly
- Calls service layer and broadcasts result

New behavior:
- Remove `record_answer` handling (will come via REST API)
- Remove `toggle_question` handling (will come via REST API)
- Keep relay pattern for coordination messages (select_question, reveal_category, etc.)
- Keep broadcast relay for messages from REST API

**Why**: Separates concerns - WebSocket for real-time coordination, REST for persistence

### Phase 5: Update Frontend

#### 5.1 Add Version Tracking
**File**: `app/src/lib/state.svelte.ts` or create new file

Add version tracking maps:
```typescript
const playerVersions = new Map<number, number>();
const questionVersions = new Map<number, number>();

export function shouldUpdatePlayer(playerId: number, version: number): boolean {
  const currentVersion = playerVersions.get(playerId) ?? 0;
  if (version >= currentVersion) {
    playerVersions.set(playerId, version);
    return true;
  }
  console.log(`Ignoring stale player update: version ${version} < ${currentVersion}`);
  return false;
}

export function shouldUpdateQuestion(questionId: number, version: number): boolean {
  const currentVersion = questionVersions.get(questionId) ?? 0;
  if (version >= currentVersion) {
    questionVersions.set(questionId, version);
    return true;
  }
  console.log(`Ignoring stale question update: version ${version} < ${currentVersion}`);
  return false;
}
```

#### 5.2 Create REST API Client Functions
**File**: `app/src/lib/api.ts` (new file)

```typescript
import { ENDPOINT } from './state.svelte';

export async function recordPlayerAnswer(
  gameId: number,
  playerId: number,
  questionId: number,
  isCorrect: boolean,
  points?: number
): Promise<{ score: number; version: number }> {
  const response = await fetch(`http://${ENDPOINT}/api/games/${gameId}/answers/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ playerId, questionId, isCorrect, points })
  });

  if (!response.ok) {
    throw new Error(`Failed to record answer: ${response.statusText}`);
  }

  const data = await response.json();
  return { score: data.score, version: data.version };
}

export async function toggleQuestion(
  questionId: number,
  answered: boolean
): Promise<{ answered: boolean; version: number }> {
  const response = await fetch(`http://${ENDPOINT}/api/questions/${questionId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answered })
  });

  if (!response.ok) {
    throw new Error(`Failed to toggle question: ${response.statusText}`);
  }

  const data = await response.json();
  return { answered: data.answered, version: data.version };
}
```

#### 5.3 Update WebSocket Client to Use Versions
**File**: `app/src/lib/websocket.ts`

Changes to broadcast handlers:

1. Update `update_score` handler (line 117):
```typescript
} else if (data.type === 'update_score') {
  if (shouldUpdatePlayer(data.playerId, data.version)) {
    gameState.update(state => ({
      ...state,
      scores: {
        ...state.scores,
        [data.playerId]: data.score,
      }
    }));
  }
}
```

2. Update `toggle_question` handler (line 95):
```typescript
} else if (data.type === 'toggle_question') {
  if (shouldUpdateQuestion(data.questionId, data.version)) {
    gameState.update((state) => {
      if (data.answered) {
        state.answeredQuestions.add(data.questionId);
      } else if (data.answered === false) {
        state.answeredQuestions.delete(data.questionId);
      }
      return state;
    });
  }
}
```

3. Replace `recordPlayerAnswer()` method (lines 157-165):
```typescript
async recordPlayerAnswer(playerId: number, questionId: number, isCorrect: boolean, points?: number) {
  try {
    const gameId = Number(this.gameId);
    await recordPlayerAnswer(gameId, playerId, questionId, isCorrect, points);
    // Update will come via WebSocket broadcast
  } catch (error) {
    console.error('Failed to record answer:', error);
    // TODO: Show error to user
    throw error;
  }
}
```

4. Replace `updateQuestionStatus()` method (lines 149-155):
```typescript
async updateQuestionStatus(questionId: number, answered: boolean) {
  try {
    await toggleQuestion(questionId, answered);
    // Update will come via WebSocket broadcast
  } catch (error) {
    console.error('Failed to toggle question:', error);
    // TODO: Show error to user
    throw error;
  }
}
```

#### 5.4 Update UI Components to Handle Errors
**Files**: Various Svelte components that call mutation methods

Wrap mutation calls in try-catch:
```typescript
try {
  await websocket.recordPlayerAnswer(playerId, questionId, true);
} catch (error) {
  // Show toast notification or error message
  alert('Failed to record answer. Please try again.');
}
```

### Phase 6: Testing

#### 6.1 Backend Unit Tests
**File**: `service/game/tests.py`

Test cases:
- [ ] Version increments correctly on player answer
- [ ] Version increments correctly on question toggle
- [ ] Concurrent updates maintain correct version sequence
- [ ] API returns 404 for invalid IDs
- [ ] API returns 400 for invalid data
- [ ] Broadcast includes version number

#### 6.2 Integration Tests
- [ ] REST API call triggers WebSocket broadcast
- [ ] Version number prevents out-of-order updates
- [ ] Error responses work correctly
- [ ] Multiple rapid updates handled correctly

#### 6.3 Manual Testing Scenarios
- [ ] **Race condition test**: Rapidly click correct/incorrect multiple times
- [ ] **Network error test**: Disconnect network during API call
- [ ] **Out-of-order broadcast**: Simulate delayed broadcast arrival
- [ ] **Multi-client sync**: Verify updates sync across multiple browser windows
- [ ] **Error handling**: Test with invalid data, verify user sees error

## Migration Strategy

### Step 1: Backend Changes (Non-Breaking)
1. Add version fields to models (migration)
2. Update service layer to return versions
3. Add REST API endpoints
4. Deploy backend (old frontend still works via WebSocket)

### Step 2: Frontend Changes
1. Add version tracking
2. Update WebSocket handlers to check versions
3. Switch mutations to REST API
4. Deploy frontend

### Step 3: Cleanup
1. Remove mutation handling from WebSocket consumer (optional, can keep for backwards compatibility)

## Benefits of This Approach

✅ **Proper error handling**: HTTP status codes provide clear error feedback
✅ **No stuck states**: API always responds, even on error
✅ **Race condition protection**: Version numbers prevent out-of-order updates
✅ **Still real-time**: Broadcasts keep all clients synchronized
✅ **Easy to test**: REST APIs are simpler to test than WebSocket
✅ **Built-in retry**: Can retry failed API calls
✅ **Preserves relay pattern**: Coordination messages still use elegant broadcast relay

## File Changes Summary

### New Files
- `app/src/lib/api.ts` - REST API client functions

### Modified Files
- `service/game/models.py` - Add version fields
- `service/game/services.py` - Return version numbers
- `service/game/views.py` - Add REST endpoints
- `service/game/serializers.py` - Add request/response serializers
- `service/quizzer/urls.py` - Add new routes
- `service/game/consumers.py` - Remove mutation handling (optional)
- `app/src/lib/websocket.ts` - Use REST API for mutations, version checking for broadcasts
- `app/src/lib/state.svelte.ts` - Add version tracking (or create new file)

### Database
- New migration: Add `score_version` and `state_version` fields

## Estimated Complexity

- **Backend**: Medium (3-4 hours)
  - Models + migration: 30 min
  - Service layer updates: 30 min
  - REST endpoints + serializers: 1-2 hours
  - Testing: 1 hour

- **Frontend**: Medium (2-3 hours)
  - Version tracking: 30 min
  - REST API client: 30 min
  - Update WebSocket client: 1 hour
  - Update UI error handling: 30 min
  - Testing: 30 min

**Total**: 5-7 hours

## Open Questions

1. **Buzzer presses**: Should these also move to REST API, or keep via WebSocket?
   - **Recommendation**: Keep via WebSocket - they're ephemeral and don't need persistence

2. **Backwards compatibility**: Should we keep WebSocket mutation handlers for old clients?
   - **Recommendation**: Remove after frontend deployed, simpler code

3. **Error UI**: What should error messages look like? Toast? Modal? Inline?
   - **Recommendation**: Toast notifications for non-blocking feedback

4. **Retry logic**: Should we auto-retry failed mutations?
   - **Recommendation**: Start without auto-retry, add if needed

## Notes

- This is a **refinement**, not a replacement of the WebSocket system
- All coordination messages (select_question, reveal_category, etc.) stay on WebSocket
- The hybrid approach combines simplicity of relay with robustness of REST
- Version numbers are the key innovation preventing race conditions
