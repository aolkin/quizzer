from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
import json


class GameConsumer(AsyncJsonWebsocketConsumer):
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
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_message',
                'message': content
            }
        )

    async def game_message(self, event):
        message = event['message']
        await self.send_json(message)
