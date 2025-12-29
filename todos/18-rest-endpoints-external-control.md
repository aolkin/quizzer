# REST Endpoints for External Control

## Problem

Currently, game control operations (buzzer state, question selection, etc.) are only available through WebSocket messages. This creates limitations:

- **CLI tools** need simple request/response patterns, not persistent connections
- **Hardware controllers** without WebSocket support cannot integrate
- **Automation scripts** prefer stateless HTTP calls
- **Third-party integrations** expect standard REST APIs
- **Debugging** is harder with stateful WebSocket connections

Many control operations don't need real-time bidirectional communication - they're simple commands that can use HTTP.

## Current State

All game control is via WebSocket (`/ws/game/{board_id}/`):
- Buzzer enable/disable (no explicit message, just connection state)
- Question selection (`select_question` message)
- Game state changes (informal messages relayed between clients)
- Score updates (via REST, but limited to specific answer recording)

**Issue**: No REST API for game control operations.

## Proposed Solution

Create REST endpoints for write-only control operations, starting with **buzzer state toggling**.

### Initial Scope: Buzzer State Control

Create a **write-only** endpoint to enable/disable buzzers for a game:

```
POST /api/game/{game_id}/buzzers/state
```

**Request Body:**
```json
{
  "enabled": true
}
```

**Response:**
```json
{
  "game_id": 123,
  "buzzers_enabled": true,
  "updated_at": "2025-12-29T10:30:00Z"
}
```

**Behavior:**
- Updates game-level buzzer state (new `Game.buzzers_enabled` field)
- Broadcasts state change to all WebSocket clients
- Write-only (no GET endpoint in initial implementation)
- Requires authentication (account or API key)
- Requires game access permission

## Data Model Changes

```python
# Add to existing Game model
class Game(models.Model):
    # ... existing fields ...
    buzzers_enabled = models.BooleanField(default=False)
    buzzers_state_version = models.IntegerField(default=0)  # For optimistic updates
```

## API Specification

### Endpoint: Toggle Buzzer State

**URL:** `POST /api/game/{game_id}/buzzers/state`

**Authentication:** Required (cookie or API key)

**Authorization:** User/API key must have access to the game

**Request:**
```json
{
  "enabled": boolean  // required
}
```

**Success Response (200 OK):**
```json
{
  "game_id": integer,
  "buzzers_enabled": boolean,
  "version": integer,
  "updated_at": "ISO 8601 timestamp"
}
```

**Error Responses:**
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - No access to this game
- `404 Not Found` - Game does not exist
- `400 Bad Request` - Invalid request body

**Side Effects:**
- Updates `Game.buzzers_enabled` field
- Increments `Game.buzzers_state_version`
- Broadcasts WebSocket message to all clients:
  ```json
  {
    "type": "buzzer_state_changed",
    "game_id": 123,
    "enabled": true,
    "version": 1
  }
  ```

## Implementation Steps

### High Priority
- [ ] Add `buzzers_enabled` and `buzzers_state_version` fields to Game model
- [ ] Create migration for new Game fields
- [ ] Create `BuzzerStateSerializer` for request validation
- [ ] Implement `toggle_buzzer_state` service function with transaction
- [ ] Create `POST /api/game/{game_id}/buzzers/state` view
- [ ] Add authentication and game access checks to view
- [ ] Implement WebSocket broadcast for buzzer state changes
- [ ] Update `GameConsumer` to handle `buzzer_state_changed` messages

### Testing
- [ ] Unit tests for service function
- [ ] Integration tests for API endpoint
- [ ] Tests for authentication/authorization
- [ ] Tests for WebSocket broadcast
- [ ] Tests for concurrent updates (version conflicts)

### Documentation
- [ ] API endpoint documentation
- [ ] WebSocket message format for `buzzer_state_changed`
- [ ] Example usage for CLI clients
- [ ] Example usage for hardware controllers

## Future Endpoints (Not in Initial Scope)

After buzzer state control is implemented, consider these additional endpoints:

### Game State Control
- `POST /api/game/{game_id}/state` - Start, pause, reset game
- `GET /api/game/{game_id}/state` - Get current game state

### Question Control
- `POST /api/board/{board_id}/question/select` - Select question for play
- `POST /api/question/{question_id}/clear` - Clear question (mark unanswered)

### Score Management
- `POST /api/player/{player_id}/score/adjust` - Manual score adjustment
- `GET /api/game/{game_id}/scores` - Get all current scores

### Board Navigation
- `POST /api/game/{game_id}/board/select` - Switch active board
- `GET /api/game/{game_id}/board/current` - Get currently active board

## Integration Examples

### CLI Usage
```bash
# Enable buzzers for game 123
quizzer-cli game 123 buzzers enable

# Disable buzzers
quizzer-cli game 123 buzzers disable
```

### Hardware Controller
```python
import requests

def set_buzzer_state(game_id: int, enabled: bool):
    response = requests.post(
        f'http://localhost:8000/api/game/{game_id}/buzzers/state',
        headers={
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        },
        json={'enabled': enabled}
    )
    response.raise_for_status()
    return response.json()

# Enable buzzers before round starts
set_buzzer_state(game_id=123, enabled=True)
```

### Automation Script
```bash
#!/bin/bash
GAME_ID=123
API_KEY="qz_prod_..."

# Enable buzzers via curl
curl -X POST "http://localhost:8000/api/game/${GAME_ID}/buzzers/state" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

## Design Principles

1. **Write-Only First**: Start with write operations; read can come later if needed
2. **Broadcast Changes**: All state changes broadcast to WebSocket clients for real-time sync
3. **Versioning**: Use version fields for optimistic concurrency control
4. **Stateless**: REST endpoints should not maintain connection state
5. **Idempotent**: Setting state to current value should succeed (no-op)

## WebSocket vs REST Decision Matrix

| Operation | WebSocket | REST | Reason |
|-----------|-----------|------|--------|
| Buzzer state toggle | ✅ (broadcast) | ✅ (command) | Simple command, REST is easier |
| Buzzer press event | ✅ | ❌ | Real-time event, needs push |
| Question selection | ✅ | ✅ (future) | Command with broadcast |
| Score updates | ✅ | ✅ (exists) | Both needed for different clients |
| Game state changes | ✅ | ✅ (future) | Command with broadcast |

**Pattern**: Commands via REST, events via WebSocket, state sync via both.

## Dependencies

- Depends on TODO #16 (Account Authentication)
- Depends on TODO #17 (API Key Authentication)
- No new packages required

## Priority

**High** - Enables CLI and hardware integration, unblocks external tooling.

## Related TODOs

- TODO #15: Game-Level WebSocket Connections (related architecture)
- TODO #16: Account-Based Authentication (prerequisite)
- TODO #17: API Key Authentication (prerequisite)
