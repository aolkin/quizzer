#!/usr/bin/env python3
"""
Tests for OSC Bridge rule handling and message translation.

Focuses on testing the complex rule matching and argument mapping logic.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Mock all external dependencies that may not be available in test environment
sys.modules['pythonosc'] = MagicMock()
sys.modules['pythonosc.udp_client'] = MagicMock()
sys.modules['pythonosc.dispatcher'] = MagicMock()
sys.modules['pythonosc.osc_server'] = MagicMock()
sys.modules['websockets'] = MagicMock()

from osc_bridge import OSCBridgeClient


class TestOSCBridgeRules(unittest.TestCase):
    """Test cases for OSC Bridge rule handling."""

    def setUp(self):
        """Set up test configuration."""
        self.test_config = {
            "websocket": {
                "host": "localhost:8000",
                "client_id": "test-osc"
            },
            "default_destination": {
                "host": "192.168.1.100",
                "port": 53000
            },
            "outgoing": [
                {
                    "websocket_type": "toggle_buzzers",
                    "conditions": {"enabled": True},
                    "osc_destinations": [
                        {
                            "address": "/buzzers/enable",
                            "args": [{"field": "enabled", "type": "int"}]
                        }
                    ]
                },
                {
                    "websocket_type": "test_message",
                    "osc_destinations": [
                        {
                            "address": "/test",
                            "args": [
                                {"field": "value1"},  # No type - passthrough
                                {"field": "value2", "type": "int"},
                                {"field": "missing", "default": 42}
                            ]
                        }
                    ]
                }
            ],
            "incoming": [
                {
                    "osc_address": "/buzzer/press",
                    "websocket_type": "buzzer_pressed",
                    "args": [
                        {"osc_index": 0, "websocket_field": "buzzerId", "type": "int"},
                        {"osc_index": 1, "websocket_field": "pressure", "type": "float"}
                    ]
                }
            ]
        }

    def test_outgoing_rule_matching(self):
        """Test that outgoing rules match correct WebSocket message types."""
        client = OSCBridgeClient(
            host="localhost:8000",
            game_id=1,
            client_id="test",
            config=self.test_config
        )
        
        # Mock the OSC client
        mock_osc_client = MagicMock()
        client._get_osc_client = MagicMock(return_value=mock_osc_client)
        
        # Test message matching with condition
        message = {"type": "toggle_buzzers", "enabled": True}
        asyncio.run(client.handle_message(message))
        
        # Should send OSC message because condition matches
        mock_osc_client.send_message.assert_called_once()
        call_args = mock_osc_client.send_message.call_args[0]
        self.assertEqual(call_args[0], "/buzzers/enable")
        self.assertEqual(call_args[1], [1])  # True converted to 1

    def test_condition_filtering(self):
        """Test that conditions properly filter messages."""
        client = OSCBridgeClient(
            host="localhost:8000",
            game_id=1,
            client_id="test",
            config=self.test_config
        )
        
        mock_osc_client = MagicMock()
        client._get_osc_client = MagicMock(return_value=mock_osc_client)
        
        # Test message that doesn't match condition
        message = {"type": "toggle_buzzers", "enabled": False}
        asyncio.run(client.handle_message(message))
        
        # Should NOT send OSC message because condition doesn't match
        mock_osc_client.send_message.assert_not_called()

    def test_argument_mapping_with_defaults(self):
        """Test argument mapping with type passthrough and default values."""
        client = OSCBridgeClient(
            host="localhost:8000",
            game_id=1,
            client_id="test",
            config=self.test_config
        )
        
        mock_osc_client = MagicMock()
        client._get_osc_client = MagicMock(return_value=mock_osc_client)
        
        # Test message with partial fields
        message = {"type": "test_message", "value1": "hello", "value2": 3.14}
        asyncio.run(client.handle_message(message))
        
        # Should send with passthrough value1, converted value2, and default for missing
        mock_osc_client.send_message.assert_called_once()
        call_args = mock_osc_client.send_message.call_args[0]
        self.assertEqual(call_args[0], "/test")
        self.assertEqual(call_args[1], ["hello", 3, 42])

    def test_incoming_rule_matching(self):
        """Test that incoming OSC messages match rules and map to WebSocket."""
        client = OSCBridgeClient(
            host="localhost:8000",
            game_id=1,
            client_id="test",
            config=self.test_config
        )
        
        # Mock the send_message method
        client.send_message = AsyncMock()
        
        # Simulate receiving OSC message
        asyncio.run(client._handle_osc_message("/buzzer/press", 5, 0.75))
        
        # Should send WebSocket message with mapped fields
        client.send_message.assert_called_once_with(
            "buzzer_pressed",
            buzzerId=5,
            pressure=0.75
        )

    def test_default_destination_merge(self):
        """Test that default destination is merged with rule destination."""
        client = OSCBridgeClient(
            host="localhost:8000",
            game_id=1,
            client_id="test",
            config=self.test_config
        )
        
        mock_osc_client = MagicMock()
        client._get_osc_client = MagicMock(return_value=mock_osc_client)
        
        # Test message - rule only specifies address, should use default host/port
        message = {"type": "toggle_buzzers", "enabled": True}
        asyncio.run(client.handle_message(message))
        
        # Check that OSC client was created with default host/port
        client._get_osc_client.assert_called_with("192.168.1.100", 53000)

    def test_missing_required_field_skips_message(self):
        """Test that missing required field causes message to be skipped."""
        client = OSCBridgeClient(
            host="localhost:8000",
            game_id=1,
            client_id="test",
            config=self.test_config
        )
        
        mock_osc_client = MagicMock()
        client._get_osc_client = MagicMock(return_value=mock_osc_client)
        
        # Test message missing required field (value1 is required, no default)
        message = {"type": "test_message", "value2": 3.14}
        asyncio.run(client.handle_message(message))
        
        # Should NOT send OSC message because required field is missing
        mock_osc_client.send_message.assert_not_called()

    def test_malformed_osc_skips_websocket(self):
        """Test that malformed OSC messages skip sending to WebSocket."""
        client = OSCBridgeClient(
            host="localhost:8000",
            game_id=1,
            client_id="test",
            config=self.test_config
        )
        
        # Mock the send_message method
        client.send_message = AsyncMock()
        
        # Simulate receiving OSC message with insufficient arguments
        asyncio.run(client._handle_osc_message("/buzzer/press", 5))  # Missing second arg
        
        # Should NOT send WebSocket message because OSC args are insufficient
        client.send_message.assert_not_called()


if __name__ == "__main__":
    unittest.main()
