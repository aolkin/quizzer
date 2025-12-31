from channels.generic.websocket import AsyncJsonWebsocketConsumer
from urllib.parse import parse_qs

from .channels import get_game_room_name


class GameConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time game coordination.

    Handles ephemeral coordination messages (select_question, reveal_category, etc.)
    using the relay/broadcast pattern. Database mutations (scores, question status)
    are handled by REST API endpoints which broadcast updates via the channel layer.
    """

    async def broadcast_client_status(self, connected: bool):
        """Broadcast client connection status to the group."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_message",
                "message": {
                    "type": "client_connection_status",
                    "client_type": self.client_type,
                    "client_id": self.client_id,
                    "connected": connected,
                },
            },
        )

    async def connect(self):
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.room_group_name = get_game_room_name(self.game_id)

        # Parse query params to identify client type and ID
        query_string = self.scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        self.client_type = query_params.get("client_type", [None])[0]
        self.client_id = query_params.get("client_id", [None])[0]

        # Fallback to channel_name if no client_id provided
        if self.client_type and not self.client_id:
            self.client_id = self.channel_name

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Broadcast connection status for clients with a type
        if self.client_type:
            await self.broadcast_client_status(connected=True)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Broadcast disconnection status for clients with a type
        if self.client_type and self.client_id:
            await self.broadcast_client_status(connected=False)

    async def receive_json(self, content):
        """
        Relay messages with optional recipient targeting.

        - No recipient: Broadcast to all clients in room
        - recipient.channel_id: Send to specific channel
        - recipient.client_id: Send to all connections with matching client_id
        - recipient.client_type: Send to all connections with matching client_type
        """
        if not isinstance(content, dict) or "type" not in content:
            return

        recipient = content.get("recipient")

        if not recipient:
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "game_message", "message": content}
            )
            return

        if not isinstance(recipient, dict):
            return

        if "channel_id" in recipient and len(recipient) == 1:
            target_channel = recipient["channel_id"]
            await self.channel_layer.send(
                target_channel, {"type": "game_message", "message": content}
            )
        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "game_message",
                    "message": content,
                    "recipient": recipient,
                },
            )

    async def game_message(self, event):
        """
        Send message to WebSocket client with optional recipient filtering.

        Filters messages based on recipient criteria if present.
        All criteria must match (AND logic).
        """
        message = event["message"]
        recipient = event.get("recipient")

        if recipient:
            if "channel_id" in recipient and self.channel_name != recipient["channel_id"]:
                return

            if "client_id" in recipient and self.client_id != recipient["client_id"]:
                return

            if "client_type" in recipient and self.client_type != recipient["client_type"]:
                return

        message["channel_id"] = self.channel_name
        await self.send_json(message)
