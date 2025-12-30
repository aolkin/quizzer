#!/usr/bin/env python3

import asyncio
import json
import logging
from typing import Optional

import websockets


class HardwareWebSocketClient:
    """
    Base class for hardware clients connecting to Quizzer backend.

    Handles:
    - WebSocket connection management
    - Auto-reconnection with exponential backoff
    - Ping/pong for latency monitoring
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
        client_id: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the hardware WebSocket client.

        Args:
            host: Server host and port (e.g., "localhost:8000")
            game_id: Game ID to connect to
            client_type: Type of client (e.g., "buzzer", "osc")
            client_id: Optional client identifier
            logger: Optional logger instance
        """
        self.host = host
        self.game_id = game_id
        self.client_type = client_type
        self.client_id = client_id
        self.logger = logger or logging.getLogger(
            f"hardware.{client_type}.{client_id or 'default'}"
        )
        self.websocket = None
        self.running = False
        self.loop = None

    def _build_uri(self) -> str:
        """Build WebSocket URI with query parameters."""
        params = f"client_type={self.client_type}"
        if self.client_id:
            params += f"&client_id={self.client_id}"
        return f"ws://{self.host}/ws/game/{self.game_id}/?{params}"

    async def send_message(self, message_type: str, **kwargs):
        """
        Send a message to the server.

        Args:
            message_type: Type of message to send
            **kwargs: Additional message fields
        """
        if not self.websocket:
            self.logger.warning(f"Cannot send message '{message_type}': not connected")
            return

        try:
            message = {"type": message_type, **kwargs}
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            self.logger.error(f"Failed to send message '{message_type}': {e}")

    async def _handle_ping(self, message: dict):
        """Respond to ping with pong for latency monitoring."""
        await self.send_message(
            "pong",
            timestamp=message.get("timestamp"),
            recipient=message.get("sender_id"),
        )

    async def _message_loop(self):
        """Listen for messages and dispatch to handlers."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)

                    if data.get("type") == "ping":
                        await self._handle_ping(data)
                        continue

                    await self.handle_message(data)

                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON received: {e}")
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")

        except websockets.ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            raise

    async def connect(self):
        """Connect to WebSocket server with auto-reconnect."""
        backoff = 0.1  # Start at 100ms
        max_backoff = 5.0

        while self.running:
            try:
                uri = self._build_uri()
                async with websockets.connect(
                    uri, ping_interval=15, ping_timeout=5
                ) as ws:
                    self.websocket = ws
                    self.logger.info(f"Connected to {uri}")

                    # Call setup hook
                    await self.setup()

                    # Reset backoff on successful connection
                    backoff = 0.1

                    # Listen for messages
                    await self._message_loop()

            except websockets.ConnectionClosed:
                self.logger.warning("Connection closed, attempting to reconnect...")
            except Exception as e:
                self.logger.error(f"Connection error: {e}")
            finally:
                # Call teardown hook
                await self.teardown()
                self.websocket = None

            # Wait before reconnecting
            if self.running:
                self.logger.info(f"Reconnecting in {backoff:.1f}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)

    async def run(self):
        """Main entry point: connect and run forever."""
        self.running = True
        self.loop = asyncio.get_running_loop()
        try:
            await self.connect()
        finally:
            self.running = False

    def stop(self):
        """Stop the client."""
        self.running = False

    # Abstract methods for subclasses

    async def handle_message(self, message: dict):
        """
        Override to handle incoming messages.

        Args:
            message: Parsed JSON message from server
        """
        self.logger.warning(
            f"Unhandled message type '{message.get('type')}': {message}"
        )

    async def setup(self):
        """Override to initialize hardware on connection."""
        pass

    async def teardown(self):
        """Override to cleanup hardware on disconnection."""
        pass
