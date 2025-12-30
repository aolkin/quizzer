# Hardware WebSocket Client Library

Base class for connecting hardware clients to the Quizzer backend via WebSocket.

## Usage

```python
from lib.websocket_client import HardwareWebSocketClient

class MyHardwareClient(HardwareWebSocketClient):
    def __init__(self, host: str, game_id: int):
        super().__init__(host, game_id, client_type="my_hardware")

    async def handle_message(self, message: dict):
        if message["type"] == "command":
            await self.send_message("response", status="ok")

    async def setup(self):
        # Initialize hardware on connection
        pass

asyncio.run(MyHardwareClient("localhost:8000", 1).run())
```

## Key Features

- **Auto-reconnection**: Exponential backoff (100ms → 5s)
- **Ping/pong**: Automatic handling for latency monitoring
- **Hooks**: Override `setup()` and `teardown()` for hardware init/cleanup

## Methods to Override

- `handle_message(message)` - **Required.** Process incoming messages
- `setup()` - **Optional.** Initialize hardware on connection
- `teardown()` - **Optional.** Cleanup hardware on disconnection

See `/hardware/buzzers.py` for a complete example.
