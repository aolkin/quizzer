#!/usr/bin/env python3

import asyncio
import json
import logging
from typing import Optional
from urllib.parse import urlencode

import websockets


class HardwareWebSocketClient:
    """
    Base class for hardware clients connecting to Quizzer backend.

    Handles:
    - WebSocket connection management
    - Auto-reconnection with fixed delay
    - Ping/pong for latency monitoring
    - Message routing

    Subclasses implement:
    - handle_message(message) - Process incoming messages
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

    def _build_uri(self) -> str:
        params = {"client_type": self.client_type}
        if self.client_id:
            params["client_id"] = self.client_id
        query_string = urlencode(params)
        return f"ws://{self.host}/ws/game/{self.game_id}/?{query_string}"

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
            recipient=message.get("channel_id"),
        )

    async def _connect(self):
        uri = self._build_uri()
        self.websocket = await websockets.connect(
            uri, ping_interval=15, ping_timeout=5
        )
        self.logger.info(f"Connected to {uri}")

    async def _listen_for_messages(self):
        while True:
            if not self.websocket:
                await asyncio.sleep(1)
                try:
                    await self._connect()
                except Exception as e:
                    self.logger.error(f"Reconnection failed: {e}")
                continue

            try:
                message = await self.websocket.recv()
                try:
                    data = json.loads(message)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON received: {e}")
                    continue

                if data.get("type") == "ping":
                    await self._handle_ping(data)
                    continue

                try:
                    await self.handle_message(data)
                except Exception as handler_error:
                    self.logger.exception(
                        f"Error while handling message {data}: {handler_error}"
                    )

            except websockets.ConnectionClosed:
                self.logger.warning("Connection closed, attempting to reconnect...")
                self.websocket = None
                await self.on_disconnect()
            except (OSError, websockets.WebSocketException) as e:
                self.logger.error(f"Network error: {e}")
                self.websocket = None
                await self.on_disconnect()

    async def on_disconnect(self):
        """Override to handle disconnection events."""
        pass

    async def run(self):
        """Main entry point: connect and listen for messages."""
        await self._connect()
        await self._listen_for_messages()

    async def handle_message(self, message: dict):
        """
        Override to handle incoming messages.

        Args:
            message: Parsed JSON message from server
        """
        self.logger.warning(
            f"Unhandled message type '{message.get('type')}': {message}"
        )
