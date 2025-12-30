# Hardware WebSocket Client Library

## Problem

Currently, hardware integration requires duplicating WebSocket connection logic:

- **Existing**: `/hardware/buzzers.py` - GPIO buzzer client with custom WebSocket handling
- **Planned**: `/hardware/osc_bridge.py` (TODO #22) - Will need similar WebSocket logic
- **Future**: Additional hardware integrations (MIDI controllers, DMX bridges, etc.)

Each hardware client reimplements:
- WebSocket connection and auto-reconnection
- Connection status tracking
- Message serialization/deserialization
- Ping/pong handling (once TODO #23 latency monitoring is implemented)
- Error handling and logging

**Issue:** Code duplication, inconsistent behavior, harder to maintain.

## Current State

**Existing Hardware Client:** `/hardware/buzzers.py`

Current implementation has:
- Manual WebSocket connection with `websockets` library
- Custom reconnection logic with exponential backoff
- Query parameters for `client_type=buzzer`
- GPIO-specific message handling
- No `client_id` parameter (only `client_type`)
- No ping/pong handling (not yet implemented in backend)

**Code Structure:**
```python
async def main():
    while True:  # Reconnection loop
        try:
            uri = f"ws://{host}/ws/game/{game_id}/?client_type=buzzer"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps({...}))
                # Message handling loop
        except Exception:
            # Backoff and retry
```

**Duplication Risk:**
- OSC bridge (TODO #22) will need nearly identical WebSocket setup
- Future hardware clients will copy this pattern again
- Bug fixes need to be applied to multiple files

## Proposed Solution

Create a **reusable Python library** for hardware WebSocket clients:

**Location:** `/hardware/lib/websocket_client.py`

**Design:** Base class that handles WebSocket plumbing, allowing hardware-specific logic in subclasses.

### Library Architecture

```python
# /hardware/lib/websocket_client.py

class HardwareWebSocketClient:
    """
    Base class for hardware clients connecting to quizzer backend.

    Handles:
    - WebSocket connection management
    - Auto-reconnection with exponential backoff
    - Ping/pong for latency monitoring
    - Connection status reporting
    - Message routing

    Subclasses implement:
    - handle_message(message) - Process incoming messages
    - setup() - Initialize hardware (optional)
    - teardown() - Cleanup hardware (optional)
    """

    def __init__(
        self,
        host: str,
        game_id: int,
        client_type: str,
        client_id: str | None = None,
        logger: logging.Logger | None = None
    ):
        self.host = host
        self.game_id = game_id
        self.client_type = client_type
        self.client_id = client_id
        self.logger = logger or logging.getLogger(__name__)
        self.websocket = None
        self.running = False

    async def connect(self):
        """Connect to WebSocket server with auto-reconnect."""
        # Build URI with query parameters
        # Handle reconnection loop with exponential backoff
        # Call setup() hook on connection

    async def send_message(self, message_type: str, **kwargs):
        """Send a message to the server."""
        # Serialize and send JSON
        # Handle connection errors

    async def handle_ping(self, message: dict):
        """Respond to ping with pong (for latency monitoring)."""
        # Automatic pong response with target_sender_id

    async def run(self):
        """Main loop: connect, listen, reconnect on failure."""
        # Reconnection loop
        # Message dispatch to handle_message()

    # Abstract methods for subclasses
    async def handle_message(self, message: dict):
        """Override to handle incoming messages."""
        raise NotImplementedError

    async def setup(self):
        """Override to initialize hardware on connection."""
        pass

    async def teardown(self):
        """Override to cleanup hardware on disconnection."""
        pass
```

### Example Usage: GPIO Buzzers

**Refactored:** `/hardware/buzzers.py`

```python
from lib.websocket_client import HardwareWebSocketClient

class BuzzerClient(HardwareWebSocketClient):
    def __init__(self, host: str, game_id: int, client_id: str = "main"):
        super().__init__(
            host=host,
            game_id=game_id,
            client_type="buzzer",
            client_id=client_id
        )
        self.buzzers_enabled = False
        # GPIO setup

    async def handle_message(self, message: dict):
        """Handle buzzer-specific messages."""
        if message["type"] == "toggle_buzzers":
            self.buzzers_enabled = message["enabled"]
            self.logger.info(f"Buzzers {'enabled' if self.enabled else 'disabled'}")

        elif message["type"] == "buzzer_set_log_level":
            level = message["level"]
            self.logger.setLevel(logging.DEBUG if level == "DEBUG" else logging.WARN)

    async def setup(self):
        """Initialize GPIO on connection."""
        # GPIO setup code

    async def teardown(self):
        """Cleanup GPIO on disconnection."""
        # GPIO cleanup

    async def poll_buzzers(self):
        """Poll GPIO and send buzzer_pressed events."""
        # Existing buzzer polling logic
        if buzzer_detected:
            await self.send_message("buzzer_pressed", buzzerId=buzzer_id)

# Usage
if __name__ == "__main__":
    client = BuzzerClient(host="localhost:8000", game_id=1)
    asyncio.run(client.run())
```

### Example Usage: OSC Bridge

**Future:** `/hardware/osc_bridge.py` (TODO #22)

```python
from lib.websocket_client import HardwareWebSocketClient

class OSCBridgeClient(HardwareWebSocketClient):
    def __init__(self, host: str, game_id: int, client_id: str, config: dict):
        super().__init__(
            host=host,
            game_id=game_id,
            client_type="osc",
            client_id=client_id
        )
        self.config = config  # OSC mappings from YAML

    async def handle_message(self, message: dict):
        """Translate WebSocket messages to OSC."""
        # Check config for matching WebSocket → OSC mappings
        # Send OSC commands based on config

    async def setup(self):
        """Start OSC server."""
        # Initialize OSC server component

    async def teardown(self):
        """Stop OSC server."""
        # Cleanup OSC server
```

## Implementation Details

### Connection Management

**Auto-Reconnection:**
```python
async def connect(self):
    backoff = 0.1  # Start at 100ms
    max_backoff = 5.0

    while self.running:
        try:
            uri = self._build_uri()
            async with websockets.connect(uri) as ws:
                self.websocket = ws
                self.logger.info(f"Connected as {self.client_type}:{self.client_id}")

                await self.setup()  # Initialize hardware
                await self._message_loop()  # Listen for messages

        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
        finally:
            await self.teardown()  # Cleanup hardware

def _build_uri(self) -> str:
    """Build WebSocket URI with query parameters."""
    params = f"client_type={self.client_type}"
    if self.client_id:
        params += f"&client_id={self.client_id}"
    return f"ws://{self.host}/ws/game/{self.game_id}/?{params}"
```

### Message Handling

**Automatic Ping/Pong:**
```python
async def _message_loop(self):
    """Listen for messages and dispatch."""
    async for message in self.websocket:
        data = json.loads(message)

        # Automatic ping/pong handling
        if data.get("type") == "ping":
            await self._handle_ping(data)
            continue

        # Dispatch to subclass
        await self.handle_message(data)

async def _handle_ping(self, message: dict):
    """Respond to ping with pong for latency monitoring."""
    await self.send_message(
        "pong",
        timestamp=message["timestamp"],
        target_sender_id=message.get("sender_id")
    )
```

### Logging Support

**Configurable Logging:**
```python
def __init__(self, ..., log_level: str = "INFO"):
    self.logger = logging.getLogger(f"hardware.{client_type}")
    self.logger.setLevel(getattr(logging, log_level.upper()))

    # Format: [2025-01-15 10:30:45] [buzzer:main] INFO: Connected
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(name)s] %(levelname)s: %(message)s"
    )
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)
```

## Implementation Steps

### Phase 1: Core Library

- [ ] Create `/hardware/lib/` directory
- [ ] Create `/hardware/lib/__init__.py`
- [ ] Create `/hardware/lib/websocket_client.py` with `HardwareWebSocketClient` base class:
  - [ ] `__init__()` - Store connection parameters
  - [ ] `_build_uri()` - Construct WebSocket URI with query params
  - [ ] `connect()` - Connection loop with exponential backoff
  - [ ] `_message_loop()` - Listen and dispatch messages
  - [ ] `send_message()` - Send JSON messages to server
  - [ ] `_handle_ping()` - Automatic pong response
  - [ ] `handle_message()` - Abstract method for subclasses
  - [ ] `setup()` / `teardown()` - Optional hooks
  - [ ] `run()` - Main entry point

### Phase 2: Refactor Existing Buzzer Client

- [ ] Update `/hardware/buzzers.py` to extend `HardwareWebSocketClient`
- [ ] Move GPIO-specific logic to `handle_message()` override
- [ ] Move GPIO initialization to `setup()` override
- [ ] Move GPIO cleanup to `teardown()` override
- [ ] Add `client_id` parameter (default: "main")
- [ ] Test that existing functionality still works
- [ ] Update documentation and comments

### Phase 3: Enhanced Features

- [ ] Add connection state callbacks:
  - [ ] `on_connected()` - Called after successful connection
  - [ ] `on_disconnected()` - Called after connection loss
  - [ ] `on_message(type, data)` - Alternative to subclassing
- [ ] Add health check / heartbeat monitoring
- [ ] Add message queue for sending when disconnected
- [ ] Add graceful shutdown handling (SIGINT, SIGTERM)

### Phase 4: Testing & Documentation

- [ ] Create unit tests for `HardwareWebSocketClient`:
  - [ ] Test connection and reconnection logic
  - [ ] Test ping/pong handling
  - [ ] Test message serialization
  - [ ] Test error handling
- [ ] Create integration tests with mock WebSocket server
- [ ] Write library documentation:
  - [ ] API reference for `HardwareWebSocketClient`
  - [ ] Tutorial for creating custom hardware clients
  - [ ] Migration guide for existing buzzer client
- [ ] Add example hardware client templates

## Benefits

1. **Code Reuse:** Common WebSocket logic written once, used everywhere
2. **Consistency:** All hardware clients behave the same way
3. **Maintainability:** Bug fixes and features apply to all clients
4. **Testability:** Library can be tested independently
5. **Extensibility:** Easy to add new hardware clients
6. **Best Practices:** Reconnection, error handling, logging built-in

## Design Principles

- **Subclass-friendly:** Easy to extend with `handle_message()` override
- **Minimal dependencies:** Only `websockets`, `asyncio`, standard library
- **Async-first:** Built on asyncio for efficient I/O
- **Logging-aware:** Structured logging for debugging
- **Configurable:** Connection params, log levels, backoff tuning
- **Production-ready:** Error handling, reconnection, graceful shutdown

## Migration Strategy

**Backwards Compatibility:**
- Existing `/hardware/buzzers.py` can be refactored in-place
- Old script can remain as reference until migration is complete
- Library is opt-in; old clients continue to work

**Testing:**
- Test refactored buzzer client against existing backend
- Ensure connection behavior is identical
- Verify all message types still work

**Rollout:**
1. Create library and tests
2. Refactor buzzer client
3. Test in development environment
4. Deploy to production (no backend changes needed)
5. Use library for OSC bridge (TODO #22)

## Dependencies

- `websockets` library (already used by `/hardware/buzzers.py`)
- Python 3.10+ (for type hints, `|` union syntax)
- `asyncio` (standard library)
- No backend changes required

## Priority

**High** - Foundation for TODO #22 (OSC Bridge) and TODO #23 (latency monitoring). Should be implemented before either of those.

## Related TODOs

- **TODO #22** (WebSocket ↔ OSC Bridge) - Will use this library
- **TODO #23** (Connection Status Overlay) - Ping/pong support needed
- Enables future hardware integrations (MIDI, DMX, custom controllers)

## Future Enhancements (Out of Scope)

- **Multiple backend support:** Connect to multiple games simultaneously
- **HTTP fallback:** Use long-polling if WebSocket unavailable
- **Message buffering:** Store messages when disconnected, replay on reconnect
- **Compression:** Support WebSocket compression (permessage-deflate)
- **TLS/SSL:** Secure WebSocket connections (wss://)
- **Authentication:** API key or token-based auth (depends on TODO #16, #17)

## Example Directory Structure

```
/hardware/
├── lib/
│   ├── __init__.py
│   ├── websocket_client.py     # HardwareWebSocketClient base class
│   └── test_websocket_client.py  # Unit tests
├── buzzers.py                   # Refactored to use library
├── osc_bridge.py               # Future: uses library (TODO #22)
├── requirements.txt            # websockets, etc.
└── README.md                   # Hardware integration guide
```

## Documentation Outline

### `/hardware/lib/README.md`

```markdown
# Hardware WebSocket Client Library

Base class for connecting hardware to the quizzer backend.

## Quick Start

1. Subclass `HardwareWebSocketClient`
2. Implement `handle_message(message)`
3. Optionally override `setup()` / `teardown()`
4. Call `run()` in main

## Example

(Include minimal example here)

## API Reference

- `__init__(host, game_id, client_type, client_id)`
- `async run()` - Main entry point
- `async send_message(type, **kwargs)` - Send message
- `async handle_message(message)` - Override this
- `async setup()` - Optional: init hardware
- `async teardown()` - Optional: cleanup hardware

## Connection Behavior

- Auto-reconnects with exponential backoff (100ms → 5s)
- Automatic ping/pong handling for latency monitoring
- Logs connection events at INFO level
- Graceful shutdown on SIGINT/SIGTERM
```
