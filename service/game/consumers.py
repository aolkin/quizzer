from channels.generic.websocket import AsyncJsonWebsocketConsumer


class GameConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time game coordination.

    Handles ephemeral coordination messages (select_question, reveal_category, etc.)
    using the relay/broadcast pattern. Database mutations (scores, question status)
    are handled by REST API endpoints which broadcast updates via the channel layer.
    """

    # Class-level dictionary to track buzzer client connections per board
    buzzer_clients = {}

    async def connect(self):
        self.board_id = self.scope["url_route"]["kwargs"]["board_id"]
        self.room_group_name = f"board_{self.board_id}"
        self.is_buzzer_client = False

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # If this was the buzzer client, broadcast disconnection status
        if self.is_buzzer_client:
            GameConsumer.buzzer_clients.pop(self.board_id, None)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "game_message",
                    "message": {"type": "buzzer_connection_status", "connected": False},
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

        # Identify buzzer client when it sends buzzer_pressed messages
        if content["type"] == "buzzer_pressed" and not self.is_buzzer_client:
            self.is_buzzer_client = True
            GameConsumer.buzzer_clients[self.board_id] = self.channel_name
            # Broadcast that buzzer client is now connected
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "game_message",
                    "message": {"type": "buzzer_connection_status", "connected": True},
                },
            )

        # Handle buzzer_set_log_level messages - relay only to buzzer client
        if content["type"] == "buzzer_set_log_level":
            buzzer_channel = GameConsumer.buzzer_clients.get(self.board_id)
            if buzzer_channel:
                await self.channel_layer.send(
                    buzzer_channel, {"type": "game_message", "message": content}
                )
            return  # Don't broadcast to all clients

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
