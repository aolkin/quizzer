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

Create a **write-only** endpoint to broadcast buzzer state commands:

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
  "enabled": true,
  "broadcast": true
}
```

**Behavior:**
- **No database persistence** - pure command/broadcast endpoint
- Broadcasts state change to all WebSocket clients connected to this game
- WebSocket clients (including hardware) handle the state change
- Write-only (no GET endpoint - state lives only in connected clients)
- Requires authentication (account or API key)
- Requires game access permission

## Design Note: Stateless Commands

This endpoint does NOT store buzzer state in the database. It's a pure command endpoint that:
1. Validates the request
2. Broadcasts to WebSocket clients
3. Returns success

Clients (web UI, hardware controllers) maintain their own state based on WebSocket messages. This matches the existing architecture where game control is primarily WebSocket-based.

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
  "enabled": boolean,
  "broadcast": true
}
```

**Error Responses:**
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - No access to this game
- `404 Not Found` - Game does not exist
- `400 Bad Request` - Invalid request body

**Side Effects:**
- Broadcasts WebSocket message to all game clients (all boards in the game):
  ```json
  {
    "type": "buzzer_state_command",
    "game_id": 123,
    "enabled": true
  }
  ```
- No database changes

## Implementation Steps

### High Priority
- [ ] Create `BuzzerStateSerializer` for request validation
- [ ] Create `POST /api/game/{game_id}/buzzers/state` view
- [ ] Add authentication and game access checks to view
- [ ] Implement WebSocket broadcast helper to send to all game boards
- [ ] Update `GameConsumer` to relay `buzzer_state_command` messages to clients

### Testing
- [ ] Integration tests for API endpoint
- [ ] Tests for authentication/authorization
- [ ] Tests for WebSocket broadcast to all game boards
- [ ] Tests that no database changes occur

### Documentation
- [ ] API endpoint documentation
- [ ] WebSocket message format for `buzzer_state_command`
- [ ] Example usage for CLI clients
- [ ] Example usage for hardware controllers
- [ ] Document that no state is persisted (clients maintain state)

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

1. **No Persistence**: REST endpoints are pure command/broadcast - no database state
2. **Write-Only**: Commands only; no GET endpoints (state lives in connected clients)
3. **Broadcast Changes**: All commands broadcast to WebSocket clients
4. **Stateless**: REST endpoints don't maintain connection state or store data
5. **Idempotent**: Sending same command multiple times is safe (broadcasts each time)
6. **Client-Side State**: WebSocket clients maintain state based on received messages

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
