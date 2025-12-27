# REST API for Persistent Mutations with Versioning

## Overview
Move database-mutating operations from WebSocket to REST APIs while preserving the WebSocket relay pattern for ephemeral coordination.

## The Problem
Current WebSocket-only approach for database mutations has issues:
- No proper error handling (crashes connection instead of returning errors)
- Race conditions when multiple updates happen quickly
- Client can get stuck waiting for broadcast that never arrives
- Out-of-order broadcasts can temporarily revert UI state

## The Solution: Hybrid Architecture

### REST API for Persistence
```
Client → POST /api/games/{id}/answers/
  ↓
Server: Validates, updates DB with versioning
  ↓
Returns: {success: true, score: 600, version: 42}
  ↓
Broadcasts: {type: 'update_score', playerId: 1, score: 600, version: 42}
  ↓
All clients update UI using version number to prevent race conditions
```

### WebSocket Relay for Coordination
```
Client → {type: 'select_question', question: 5}
  ↓
Server: Forwards as-is (no processing)
  ↓
All clients update UI
```

## Versioning Strategy

### Option 1: Sequence Numbers (Recommended)
Add version field to models:
```python
class Player(models.Model):
    # ...
    score_version = models.IntegerField(default=0)

class Question(models.Model):
    # ...
    state_version = models.IntegerField(default=0)
```

Increment atomically on each update:
```python
@transaction.atomic
def record_player_answer(...):
    player = Player.objects.select_for_update().get(id=player_id)
    # ... update logic ...
    player.score_version = F('score_version') + 1
    player.save(update_fields=['score_version'])
    player.refresh_from_db()
    return {'score': player.score, 'version': player.score_version}
```

Client tracks versions:
```javascript
const playerVersions = new Map();

function handleScoreUpdate(playerId, score, version) {
    const currentVersion = playerVersions.get(playerId) || 0;
    if (version >= currentVersion) {
        updatePlayerScore(playerId, score);
        playerVersions.set(playerId, version);
    } else {
        console.log('Ignoring stale update');
    }
}
```

### Option 2: Timestamps
Use existing `answered_at` / `updated_at` fields and compare timestamps.

**Pros:** No schema change
**Cons:** Clock skew issues, less reliable

## API Endpoints to Create

### Priority 1: Record Answer
```
POST /api/games/{game_id}/answers/
Body: {playerId, questionId, isCorrect, points?}
Returns: {success: true, score: 600, version: 42}
Broadcast: {type: 'update_score', playerId, score, version}
```

### Priority 2: Toggle Question
```
PATCH /api/questions/{id}/
Body: {answered: true}
Returns: {success: true, answered: true, version: 15}
Broadcast: {type: 'toggle_question', questionId, answered, version}
```

### Optional: Buzzer Press
```
POST /api/games/{game_id}/buzzer/
Body: {buzzerId}
Returns: {success: true}
Broadcast: {type: 'buzzer_pressed', buzzerId}
```

## Implementation Steps

### Backend
- [ ] Add version fields to Player and Question models
- [ ] Create migration for version fields
- [ ] Update service layer functions to return version numbers
- [ ] Create REST API endpoints
- [ ] APIs call service layer, then broadcast via channel layer
- [ ] Include version in both API response and broadcast message
- [ ] Add proper error handling (404, 400, validation errors)

### Frontend
- [ ] Create version tracking maps (playerVersions, questionVersions)
- [ ] Update score/question handlers to check versions
- [ ] Switch mutation calls from WebSocket to REST API
- [ ] Handle API errors with user feedback
- [ ] Still listen to broadcasts for updates from other clients
- [ ] Ignore out-of-order broadcasts based on version

### Testing
- [ ] Test rapid successive updates (race condition)
- [ ] Test API error cases (404, validation)
- [ ] Test WebSocket disconnect during API call
- [ ] Test out-of-order broadcast arrival
- [ ] Verify other clients still get synchronized

## Benefits
✅ Robust error handling via HTTP status codes
✅ No stuck states (API always responds)
✅ Race condition protection via versioning
✅ Still real-time (broadcast synchronization)
✅ Simple to test (REST APIs)
✅ Built-in retry mechanisms
✅ Preserves elegant relay pattern for coordination

## Notes
- This is a refinement, not a replacement - WebSocket relay stays for coordination
- All clients still update from broadcasts (single source of truth for UI)
- API response is just for error handling and immediate feedback
- Version numbers prevent temporary UI glitches from out-of-order messages
