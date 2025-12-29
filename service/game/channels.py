"""
WebSocket channel utilities.

This module provides the single source of truth for channel/room naming
and broadcasting utilities used by both WebSocket consumers and REST views.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from typing import Dict, Any


def get_game_room_name(game_id: int) -> str:
    """Get the WebSocket room name for a game."""
    return f"game_{game_id}"


def broadcast_to_game(game_id: int, message_type: str, data: Dict[str, Any]) -> None:
    """Broadcast a message to all WebSocket clients connected to a game."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        get_game_room_name(game_id),
        {"type": "game_message", "message": {"type": message_type, **data}},
    )
