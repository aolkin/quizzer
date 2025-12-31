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

async def main():
    client = MyHardwareClient("localhost:8000", 1)
    await client.run()

asyncio.run(main())
```

## Key Features

- **Auto-reconnection**: Reconnects automatically with 1s delay
- **Ping/pong**: Automatic handling for latency monitoring

## Methods to Override

- `handle_message(message)` - **Required.** Process incoming messages
- `on_disconnect()` - **Optional.** Called when connection is lost

See `/hardware/buzzers.py` for a complete example.
