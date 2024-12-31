from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
import json

from game.models import Player, PlayerAnswer, Question


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

    @database_sync_to_async
    def update_question_status(self, question_id, answered):
        Question.objects.filter(id=question_id).update(answered=answered)

    @database_sync_to_async
    def record_player_answer(self, player_id, question_id, correct, points):
        answer = PlayerAnswer.objects.filter(player_id=player_id, question_id=question_id).first()
        if answer:
            if answer.is_correct != correct:
                answer.delete()
            elif answer.points != points:
                answer.points = points
                answer.save()
        else:
            PlayerAnswer.objects.create(player_id=player_id, question_id=question_id, is_correct=correct, points=points)
        return Player.objects.get(id=player_id).score

    async def receive_json(self, content):
        if content.get('type') == 'toggle_question':
            await self.update_question_status(content['questionId'], content['answered'])

        if content.get('type') == 'record_answer':
            new_score = await self.record_player_answer(
                content['playerId'], content['questionId'], content['isCorrect'], content['points'])
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_message',
                    'message': {
                        'type': 'update_score',
                        'playerId': content['playerId'],
                        'score': new_score
                    }
                }
            )
        else:
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
