from channels.generic.websocket import AsyncJsonWebsocketConsumer


class GameConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time game coordination.

    Handles ephemeral coordination messages (select_question, reveal_category, etc.)
    using the relay/broadcast pattern. Database mutations (scores, question status)
    are handled by REST API endpoints which broadcast updates via the channel layer.
    """

    async def connect(self):
        self.board_id = self.scope['url_route']['kwargs']['board_id']
        self.room_group_name = f'board_{self.board_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
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

        if 'type' not in content or not isinstance(content['type'], str):
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_message',
                'message': content
            }
        )

    async def game_message(self, event):
        """
        Send message to WebSocket client.

        Called when a message is broadcast to the group (from REST API or other clients).
        """
        message = event['message']
        await self.send_json(message)
