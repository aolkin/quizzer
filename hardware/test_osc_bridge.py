#!/usr/bin/env python3
"""
Basic tests for OSC Bridge configuration and message translation.

Note: These are unit tests for the message translation logic. Full integration
testing requires running WebSocket server and OSC endpoints.
"""

import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os
import sys

# Mock all external dependencies that may not be available in test environment
sys.modules['pythonosc'] = MagicMock()
sys.modules['pythonosc.udp_client'] = MagicMock()
sys.modules['pythonosc.dispatcher'] = MagicMock()
sys.modules['pythonosc.osc_server'] = MagicMock()
sys.modules['websockets'] = MagicMock()

import yaml

from osc_bridge import OSCBridgeClient, load_config


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

    def test_load_config(self):
        """Test YAML configuration loading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.test_config, f)
            config_path = f.name

        try:
            config = load_config(config_path)
            self.assertEqual(config["websocket"]["host"], "localhost:8000")
            self.assertEqual(config["websocket"]["game_id"], 1)
            self.assertEqual(len(config["outgoing"]), 1)
            self.assertEqual(len(config["incoming"]), 1)
        finally:
            os.unlink(config_path)

    def test_websocket_to_osc_conversion(self):
        """Test WebSocket value to OSC type conversion."""
        client = OSCBridgeClient(
            host="localhost:8000",
            game_id=1,
            client_id="test",
            config=self.test_config
        )

        # Test bool to int conversion
        self.assertEqual(client._convert_websocket_to_osc(True, "int"), 1)
        self.assertEqual(client._convert_websocket_to_osc(False, "int"), 0)

        # Test numeric conversions
        self.assertEqual(client._convert_websocket_to_osc(42, "int"), 42)
        self.assertEqual(client._convert_websocket_to_osc(3.14, "float"), 3.14)
        self.assertEqual(client._convert_websocket_to_osc(42, "float"), 42.0)

        # Test string conversion
        self.assertEqual(client._convert_websocket_to_osc("test", "string"), "test")

    def test_osc_to_websocket_conversion(self):
        """Test OSC value to WebSocket type conversion."""
        client = OSCBridgeClient(
            host="localhost:8000",
            game_id=1,
            client_id="test",
            config=self.test_config
        )

        # Test bool conversion
        self.assertTrue(client._convert_osc_to_websocket(1.0, "bool"))
        self.assertFalse(client._convert_osc_to_websocket(0.0, "bool"))
        self.assertFalse(client._convert_osc_to_websocket(0.3, "bool"))
        self.assertTrue(client._convert_osc_to_websocket(0.7, "bool"))

        # Test numeric conversions
        self.assertEqual(client._convert_osc_to_websocket(42.5, "int"), 42)
        self.assertEqual(client._convert_osc_to_websocket(3.14, "float"), 3.14)

        # Test string conversion
        self.assertEqual(client._convert_osc_to_websocket("test", "string"), "test")


if __name__ == "__main__":
    unittest.main()
