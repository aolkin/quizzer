from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from typing import Dict, Any

from .models import Game, Board, Player, Question
from .serializers import (
    BoardSerializer, GameSerializer,
    RecordAnswerRequestSerializer, RecordAnswerResponseSerializer,
    ToggleQuestionRequestSerializer, ToggleQuestionResponseSerializer
)
from . import services


def broadcast_to_board(board_id: int, message_type: str, data: Dict[str, Any]) -> None:
    """Broadcast a message to all WebSocket clients connected to a board."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'board_{board_id}',
        {
            'type': 'game_message',
            'message': {
                'type': message_type,
                **data
            }
        }
    )


@api_view(['GET'])
def get_board(request, board_id):
    board = Board.objects.select_related('game').prefetch_related(
        'categories',
        'categories__questions'
    ).get(id=board_id)
    return Response(BoardSerializer(board).data)


@api_view(['GET'])
def get_game(request, game_id):
    game = Game.objects.prefetch_related(
        'boards',
        'teams',
        'teams__players'
    ).get(id=game_id)
    return Response(GameSerializer(game).data)


@api_view(['POST'])
def record_answer(request, board_id):
    """
    Record a player's answer and broadcast the score update.

    POST /api/boards/{board_id}/answers/
    Body: {playerId, questionId, isCorrect, points?}
    Returns: {playerId, score, version}
    """
    request_serializer = RecordAnswerRequestSerializer(data=request.data)
    if not request_serializer.is_valid():
        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = request_serializer.validated_data

    try:
        board = Board.objects.select_related('game').get(id=board_id)
    except Board.DoesNotExist:
        return Response({'error': 'Board not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        player = Player.objects.select_related('team__game').get(id=data['playerId'])
        if player.team.game_id != board.game_id:
            return Response(
                {'error': 'Player does not belong to this game'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Player.DoesNotExist:
        return Response({'error': 'Player not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        question = Question.objects.select_related('category__board').get(id=data['questionId'])
        if question.category.board_id != board_id:
            return Response(
                {'error': 'Question does not belong to this board'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Question.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

    result = services.record_player_answer(
        player_id=data['playerId'],
        question_id=data['questionId'],
        is_correct=data['isCorrect'],
        points=data.get('points')
    )

    broadcast_to_board(board_id, 'update_score', {
        'playerId': result.player_id,
        'score': result.score,
        'version': result.version
    })

    return Response(RecordAnswerResponseSerializer({
        'playerId': result.player_id,
        'score': result.score,
        'version': result.version
    }).data)


@api_view(['PATCH'])
def toggle_question(request, question_id):
    """
    Toggle question answered status and broadcast the update.

    PATCH /api/questions/{question_id}/
    Body: {answered}
    Returns: {questionId, answered, version}
    """
    request_serializer = ToggleQuestionRequestSerializer(data=request.data)
    if not request_serializer.is_valid():
        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = request_serializer.validated_data

    try:
        question = Question.objects.select_related('category__board').get(id=question_id)
        board_id = question.category.board_id
    except Question.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

    result = services.update_question_status(
        question_id=question_id,
        answered=data['answered']
    )

    broadcast_to_board(board_id, 'toggle_question', {
        'questionId': result.question_id,
        'answered': result.answered,
        'version': result.version
    })

    return Response(ToggleQuestionResponseSerializer({
        'questionId': result.question_id,
        'answered': result.answered,
        'version': result.version
    }).data)
