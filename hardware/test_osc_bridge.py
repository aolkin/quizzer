#!/usr/bin/env python3
"""
Basic tests for OSC Bridge configuration and message translation.

Note: These are unit tests for the message translation logic. Full integration
testing requires running WebSocket server and OSC endpoints.
"""

import unittest
from unittest.mock import MagicMock
import sys

# Mock all external dependencies that may not be available in test environment
sys.modules['pythonosc'] = MagicMock()
sys.modules['pythonosc.udp_client'] = MagicMock()
sys.modules['pythonosc.dispatcher'] = MagicMock()
sys.modules['pythonosc.osc_server'] = MagicMock()
sys.modules['websockets'] = MagicMock()

from osc_bridge import OSCBridgeClient


class TestOSCBridge(unittest.TestCase):
    """Test cases for OSC Bridge."""

    def setUp(self):
        """Set up test configuration."""
        self.test_config = {
            "websocket": {
                "host": "localhost:8000",
                "game_id": 1,
                "client_id": "test-osc"
            },
            "osc": {
                "listen_host": "0.0.0.0",
                "listen_port": 7400
            },
            "outgoing": [
                {
                    "websocket_type": "toggle_buzzers",
                    "osc_destinations": [
                        {
                            "host": "192.168.1.100",
                            "port": 53000,
                            "address": "/quizzer/buzzers/state",
                            "args": [
                                {"field": "enabled", "type": "int"}
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
                        {"osc_index": 0, "websocket_field": "buzzerId", "type": "int"}
                    ]
                }
            ]
        }

    def test_type_conversion(self):
        """Test type conversion between WebSocket and OSC."""
        client = OSCBridgeClient(
            host="localhost:8000",
            game_id=1,
            client_id="test",
            config=self.test_config
        )

        # Test WebSocket to OSC: bool to int conversion (OSC convention)
        self.assertEqual(client._convert_type(True, "int", "to_osc"), 1)
        self.assertEqual(client._convert_type(False, "int", "to_osc"), 0)

        # Test OSC to WebSocket: float to bool conversion (threshold at 0.5)
        self.assertTrue(client._convert_type(1.0, "bool", "to_websocket"))
        self.assertFalse(client._convert_type(0.0, "bool", "to_websocket"))
        self.assertFalse(client._convert_type(0.3, "bool", "to_websocket"))
        self.assertTrue(client._convert_type(0.7, "bool", "to_websocket"))


if __name__ == "__main__":
    unittest.main()
