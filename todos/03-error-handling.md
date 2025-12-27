# No Error Handling

## Backend Issues

### Views (`service/game/views.py`)
- Lines 9 & 17: Using `.get()` without error handling
- Will raise `DoesNotExist` exception instead of proper 404
- Should use `get_object_or_404` helper

### WebSocket Consumer
- No try/catch around database operations
- Could crash WebSocket connection on database errors
- No validation of incoming message data

## Frontend Issues

### API Calls
- No error boundaries or try/catch blocks
- `websocket.ts:67-68`: Fetches board data without error handling
- Failed API calls will crash the app

### WebSocket
- `websocket.ts:45`: Throws error when socket closed, but no caller handles it
- No retry logic for failed sends
- Reconnection only handles close events, not errors

### Hardware Client
- `buzzers.py:99-104`: Exits on disconnect instead of reconnecting
- Exit call on line 101 makes subsequent reconnect code unreachable (dead code)

## Action Items

### Backend
- [ ] Replace `.get()` with `get_object_or_404()` in views
- [ ] Add try/catch in WebSocket consumer database operations
- [ ] Add message validation in consumer

### Frontend
- [ ] Add error boundaries to components
- [ ] Wrap API calls in try/catch with user feedback
- [ ] Handle WebSocket send errors gracefully
- [ ] Add exponential backoff to reconnection logic

### Hardware
- [ ] Fix disconnect handling to actually reconnect
- [ ] Remove exit(1) call
- [ ] Add graceful shutdown handling
