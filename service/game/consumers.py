from channels.generic.websocket import AsyncJsonWebsocketConsumer
from urllib.parse import parse_qs


class GameConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time game coordination.

    Handles ephemeral coordination messages (select_question, reveal_category, etc.)
    using the relay/broadcast pattern. Database mutations (scores, question status)
    are handled by REST API endpoints which broadcast updates via the channel layer.
    """

    # Class-level dictionary to track clients by type per board
    # Structure: {board_id: {client_type: channel_name}}
    clients_by_type = {}

    async def connect(self):
        self.board_id = self.scope["url_route"]["kwargs"]["board_id"]
        self.room_group_name = f"board_{self.board_id}"

        # Parse query params to identify client type
        query_string = self.scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        self.client_type = query_params.get("client_type", [None])[0]

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Track client by type and broadcast connection status
        if self.client_type:
            if self.board_id not in GameConsumer.clients_by_type:
                GameConsumer.clients_by_type[self.board_id] = {}
            GameConsumer.clients_by_type[self.board_id][self.client_type] = self.channel_name

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "game_message",
                    "message": {
                        "type": "client_connection_status",
                        "client_type": self.client_type,
                        "connected": True,
                    },
                },
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Broadcast disconnection status for tracked client types
        if self.client_type and self.board_id in GameConsumer.clients_by_type:
            if self.client_type in GameConsumer.clients_by_type[self.board_id]:
                del GameConsumer.clients_by_type[self.board_id][self.client_type]

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "game_message",
                        "message": {
                            "type": "client_connection_status",
                            "client_type": self.client_type,
                            "connected": False,
                        },
                    },
                )

    async def receive_json(self, content):
        """
        Relay coordination messages to all clients.

        Database mutations (record_answer, toggle_question) are handled by REST API.
        This only handles ephemeral coordination messages.
        """
        # Basic validation - reject obviously malformed messages
        if not isinstance(content, dict):
            return

        if "type" not in content or not isinstance(content["type"], str):
            return

        # Simple broadcast relay - no special handling
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "game_message", "message": content}
        )

    async def game_message(self, event):
        """
        Send message to WebSocket client.

        Called when a message is broadcast to the group (from REST API or other clients).
        """
        message = event["message"]
        await self.send_json(message)
