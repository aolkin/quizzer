#!/usr/bin/env python3
"""
Tests for HardwareWebSocketClient library.

Note: These are basic unit tests. Full integration testing requires
a running WebSocket server.
"""

import asyncio
import json
import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from websocket_client import HardwareWebSocketClient


class TestHardwareClient(HardwareWebSocketClient):
    """Test implementation of HardwareWebSocketClient."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages_received = []
        self.setup_called = False
        self.teardown_called = False

    async def handle_message(self, message: dict):
        """Track received messages."""
        self.messages_received.append(message)

    async def setup(self):
        """Track setup calls."""
        self.setup_called = True

    async def teardown(self):
        """Track teardown calls."""
        self.teardown_called = True


class TestHardwareWebSocketClient(unittest.TestCase):
    """Test cases for HardwareWebSocketClient."""

    def test_build_uri_with_client_id(self):
        """Test URI building with client_id."""
        client = TestHardwareClient(
            host="localhost:8000",
            game_id=42,
            client_type="buzzer",
            client_id="main",
        )

        uri = client._build_uri()
        self.assertEqual(
            uri, "ws://localhost:8000/ws/game/42/?client_type=buzzer&client_id=main"
        )

    def test_build_uri_without_client_id(self):
        """Test URI building without client_id."""
        client = TestHardwareClient(
            host="localhost:8000", game_id=42, client_type="buzzer"
        )

        uri = client._build_uri()
        self.assertEqual(uri, "ws://localhost:8000/ws/game/42/?client_type=buzzer")

    async def async_test_send_message(self):
        """Test sending messages."""
        client = TestHardwareClient(
            host="localhost:8000", game_id=1, client_type="test"
        )

        # Mock websocket
        mock_ws = AsyncMock()
        client.websocket = mock_ws

        # Send message
        await client.send_message("test_message", key1="value1", key2="value2")

        # Verify message was sent
        mock_ws.send.assert_called_once()
        sent_data = json.loads(mock_ws.send.call_args[0][0])
        self.assertEqual(sent_data["type"], "test_message")
        self.assertEqual(sent_data["key1"], "value1")
        self.assertEqual(sent_data["key2"], "value2")

    def test_send_message(self):
        """Wrapper for async test."""
        asyncio.run(self.async_test_send_message())

    async def async_test_handle_ping(self):
        """Test automatic ping/pong handling."""
        client = TestHardwareClient(
            host="localhost:8000", game_id=1, client_type="test"
        )

        # Mock websocket
        mock_ws = AsyncMock()
        client.websocket = mock_ws

        # Handle ping
        ping_message = {"type": "ping", "timestamp": 12345, "sender_id": "server"}
        await client._handle_ping(ping_message)

        # Verify pong was sent
        mock_ws.send.assert_called_once()
        sent_data = json.loads(mock_ws.send.call_args[0][0])
        self.assertEqual(sent_data["type"], "pong")
        self.assertEqual(sent_data["timestamp"], 12345)
        self.assertEqual(sent_data["recipient"], "server")

    def test_handle_ping(self):
        """Wrapper for async test."""
        asyncio.run(self.async_test_handle_ping())

    async def async_test_message_handling(self):
        """Test message handling and dispatch."""
        client = TestHardwareClient(
            host="localhost:8000", game_id=1, client_type="test"
        )

        # Test regular message
        message = {"type": "command", "data": "test"}
        await client.handle_message(message)

        self.assertEqual(len(client.messages_received), 1)
        self.assertEqual(client.messages_received[0]["type"], "command")

    def test_message_handling(self):
        """Wrapper for async test."""
        asyncio.run(self.async_test_message_handling())

    def test_stop(self):
        """Test stopping the client."""
        client = TestHardwareClient(
            host="localhost:8000", game_id=1, client_type="test"
        )

        client.running = True
        client.stop()
        self.assertFalse(client.running)


if __name__ == "__main__":
    unittest.main()
