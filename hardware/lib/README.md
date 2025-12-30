# Hardware WebSocket Client Library

A reusable Python library for connecting hardware clients to the Quizzer backend via WebSocket.

## Overview

This library provides a base class `HardwareWebSocketClient` that handles all the WebSocket plumbing, allowing you to focus on hardware-specific logic.

**Features:**
- Automatic connection and reconnection with exponential backoff
- Ping/pong handling for latency monitoring
- Message routing and serialization
- Connection status tracking
- Structured logging
- Graceful error handling

## Quick Start

1. **Subclass `HardwareWebSocketClient`**
2. **Implement `handle_message(message)`** to process incoming messages
3. **Optionally override `setup()` and `teardown()`** for hardware initialization/cleanup
4. **Call `run()` in your main function**

## Example

```python
from lib.websocket_client import HardwareWebSocketClient
import asyncio
import logging

class MyHardwareClient(HardwareWebSocketClient):
    def __init__(self, host: str, game_id: int):
        super().__init__(
            host=host,
            game_id=game_id,
            client_type="my_hardware",
            client_id="main"
        )

    async def handle_message(self, message: dict):
        """Handle incoming messages from the server."""
        if message["type"] == "do_something":
            # Handle the message
            print(f"Received: {message}")
            
            # Send a response
            await self.send_message("response", status="ok")

    async def setup(self):
        """Initialize hardware when connection is established."""
        print("Hardware initialized")

    async def teardown(self):
        """Cleanup hardware when connection is lost."""
        print("Hardware cleaned up")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = MyHardwareClient(host="localhost:8000", game_id=1)
    asyncio.run(client.run())
```

## API Reference

### `HardwareWebSocketClient`

#### Constructor

```python
def __init__(
    self,
    host: str,
    game_id: int,
    client_type: str,
    client_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None
)
```

**Parameters:**
- `host`: Server host and port (e.g., `"localhost:8000"`)
- `game_id`: Game ID to connect to
- `client_type`: Type of client (e.g., `"buzzer"`, `"osc"`)
- `client_id`: Optional client identifier (defaults to channel name)
- `logger`: Optional logger instance

#### Methods to Override

##### `async def handle_message(message: dict)`

**Required.** Process incoming messages from the server.

**Parameters:**
- `message`: Parsed JSON message dictionary

**Example:**
```python
async def handle_message(self, message: dict):
    if message["type"] == "command":
        await self.do_something()
```

##### `async def setup()`

**Optional.** Called when connection is established. Use this to initialize hardware.

##### `async def teardown()`

**Optional.** Called when connection is lost. Use this to cleanup hardware.

#### Utility Methods

##### `async def send_message(message_type: str, **kwargs)`

Send a message to the server.

**Parameters:**
- `message_type`: Message type string
- `**kwargs`: Additional message fields

**Example:**
```python
await self.send_message("buzzer_pressed", buzzerId=3)
```

##### `async def run()`

**Main entry point.** Connects to the server and runs forever.

**Example:**
```python
asyncio.run(client.run())
```

##### `def stop()`

Stop the client gracefully.

## Connection Behavior

### Auto-Reconnection

The client automatically reconnects on connection failure with exponential backoff:
- Initial delay: 100ms
- Maximum delay: 5 seconds
- Backoff multiplier: 2x

### Ping/Pong

The library automatically handles ping/pong messages for latency monitoring. You don't need to implement this yourself.

### Logging

Connection events are logged at INFO level:
- `Connected to ws://...`
- `Connection closed, attempting to reconnect...`
- `Reconnecting in X.Xs...`

## WebSocket Protocol

### Query Parameters

The client connects with these query parameters:
- `client_type`: Your client type (e.g., "buzzer")
- `client_id`: Your client ID (optional)

### Message Format

All messages are JSON with a `type` field:

```json
{
  "type": "message_type",
  "field1": "value1",
  "field2": "value2"
}
```

## Examples

### GPIO Buzzer Client

See `/hardware/buzzers.py` for a complete example of using the library with GPIO hardware.

### Future: OSC Bridge Client

The library is designed to support future hardware integrations like OSC bridges, MIDI controllers, etc.

## Dependencies

- `websockets` >= 15.0
- Python 3.12+

## Testing

To test your hardware client:

1. Start the Quizzer backend server
2. Create a game and note the game ID
3. Run your client: `python my_client.py <game_id>`

## Best Practices

1. **Use structured logging**: The library provides a logger for each client
2. **Handle errors gracefully**: The library catches and logs errors
3. **Keep `handle_message()` simple**: Dispatch to separate methods for complex logic
4. **Use `setup()` and `teardown()` properly**: Initialize/cleanup hardware resources
5. **Don't block the event loop**: Use `async/await` for I/O operations

## Troubleshooting

### Client won't connect

- Check that the server URL is correct
- Verify the game ID exists
- Check firewall settings

### Connection keeps dropping

- Check network stability
- Increase ping timeout if needed
- Review server logs for errors

### Messages not being received

- Verify message type handling in `handle_message()`
- Check server is broadcasting messages
- Enable DEBUG logging to see all messages
