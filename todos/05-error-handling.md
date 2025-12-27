# Error Handling Strategy

## Current Issues

### Views (`service/game/views.py`)
- Lines 9 & 17: Using `.get()` without error handling
- Will raise `DoesNotExist` exception instead of proper 404
- Should use `get_object_or_404` helper

### WebSocket Consumer (Coordination Messages)
- No validation of incoming relay messages
- Could crash if malformed messages arrive
- Currently accepts and forwards anything

### Frontend Issues
- `websocket.ts:67-68`: Fetches board data without error handling
- `websocket.ts:45`: Throws error when socket closed, but no caller handles it
- No retry logic for failed sends
- Reconnection only handles close events, not errors

### Hardware Client
- `buzzers.py:99-104`: Exits on disconnect instead of reconnecting
- Exit call on line 101 makes subsequent reconnect code unreachable (dead code)

## Architectural Approach: Hybrid REST + WebSocket

### Strategy
**Persistent mutations → REST APIs** (proper error handling via HTTP)
- Record player answers
- Toggle question status
- Any database changes

**Ephemeral coordination → WebSocket relay** (preserve simple broadcast pattern)
- select_question, reveal_category, select_board
- UI state synchronization
- No database changes, just forwarding

### Why This Split
- REST gives us HTTP status codes (404, 400, 500)
- REST has built-in retry mechanisms
- WebSocket relay stays simple and fast
- Best of both worlds

## Action Items

### Backend
- [ ] Replace `.get()` with `get_object_or_404()` in views
- [ ] Create REST API endpoints for persistent mutations (see TODO #11)
- [ ] Add basic validation to WebSocket relay (reject obviously malformed messages)
- [ ] Keep WebSocket relay simple - don't add complex error handling there

### Frontend
- [ ] Add error boundaries to components
- [ ] Wrap REST API calls in try/catch with user feedback
- [ ] Handle WebSocket send errors gracefully (log, but don't crash)
- [ ] Add exponential backoff to reconnection logic

### Hardware
- [ ] Fix disconnect handling to actually reconnect
- [ ] Remove exit(1) call
- [ ] Add graceful shutdown handling

## Notes
- WebSocket relay pattern (forwarding coordination messages) is intentional and valuable
- Don't over-engineer error handling for relay messages - they're ephemeral UI state
- Focus error handling effort on REST APIs where data persistence matters
