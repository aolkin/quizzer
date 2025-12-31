#!/usr/bin/env python3
"""
Tests for HardwareWebSocketClient library.

Note: These are basic unit tests. Full integration testing requires
a running WebSocket server.
"""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock
from .websocket_client import HardwareWebSocketClient


class TestHardwareClient(HardwareWebSocketClient):
    """Test implementation of HardwareWebSocketClient."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages_received = []

    async def handle_message(self, message: dict):
        """Track received messages."""
        self.messages_received.append(message)


class TestHardwareWebSocketClient(unittest.TestCase):
    """Test cases for HardwareWebSocketClient."""

    def test_uri_building(self):
        """Test URI building with and without client_id."""
        client_with_id = TestHardwareClient(
            host="localhost:8000", game_id=42, client_type="buzzer", client_id="main"
        )
        self.assertEqual(
            client_with_id._build_uri(),
            "ws://localhost:8000/ws/game/42/?client_type=buzzer&client_id=main"
        )

        client_without_id = TestHardwareClient(
            host="localhost:8000", game_id=42, client_type="buzzer"
        )
        self.assertEqual(
            client_without_id._build_uri(),
            "ws://localhost:8000/ws/game/42/?client_type=buzzer"
        )

    async def async_test_messaging(self):
        """Test sending messages and ping/pong handling."""
        client = TestHardwareClient(host="localhost:8000", game_id=1, client_type="test")
        mock_ws = AsyncMock()
        client.websocket = mock_ws

        await client.send_message("test_message", key="value")
        sent_data = json.loads(mock_ws.send.call_args[0][0])
        self.assertEqual(sent_data["type"], "test_message")
        self.assertEqual(sent_data["key"], "value")

        mock_ws.reset_mock()
        await client._handle_ping({"type": "ping", "timestamp": 12345, "channel_id": "server"})
        pong_data = json.loads(mock_ws.send.call_args[0][0])
        self.assertEqual(pong_data["type"], "pong")
        self.assertEqual(pong_data["recipient"], "server")
        self.assertEqual(pong_data["timestamp"], 12345)

    def test_messaging(self):
        """Wrapper for async messaging test."""
        asyncio.run(self.async_test_messaging())


if __name__ == "__main__":
    unittest.main()
