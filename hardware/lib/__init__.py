"""
Hardware WebSocket client library for Quizzer.

This package provides a reusable base class for hardware clients
that connect to the Quizzer backend via WebSocket.
"""

from .websocket_client import HardwareWebSocketClient

__all__ = ["HardwareWebSocketClient"]
