from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Game, Board, Player, Question
from .serializers import (
    BoardSerializer, GameSerializer,
    RecordAnswerRequestSerializer, RecordAnswerResponseSerializer,
    ToggleQuestionRequestSerializer, ToggleQuestionResponseSerializer
)
from . import services


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
def record_answer(request, game_id):
    """
    Record a player's answer and broadcast the score update.

    POST /api/games/{game_id}/answers/
    Body: {playerId, questionId, isCorrect, points?}
    Returns: {playerId, score, version}
    """
    # Validate request data
    request_serializer = RecordAnswerRequestSerializer(data=request.data)
    if not request_serializer.is_valid():
        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = request_serializer.validated_data

    # Validate that player and question exist
    try:
        Player.objects.get(id=data['playerId'])
        Question.objects.get(id=data['questionId'])
    except Player.DoesNotExist:
        return Response({'error': 'Player not found'}, status=status.HTTP_404_NOT_FOUND)
    except Question.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

    # Call service layer to record answer
    result = services.record_player_answer(
        player_id=data['playerId'],
        question_id=data['questionId'],
        is_correct=data['isCorrect'],
        points=data.get('points')
    )

    # Broadcast update to all WebSocket clients
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'board_{game_id}',
        {
            'type': 'game_message',
            'message': {
                'type': 'update_score',
                'playerId': result.player_id,
                'score': result.score,
                'version': result.version
            }
        }
    )

    # Return response
    response_data = {
        'playerId': result.player_id,
        'score': result.score,
        'version': result.version
    }
    response_serializer = RecordAnswerResponseSerializer(response_data)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def toggle_question(request, question_id):
    """
    Toggle question answered status and broadcast the update.

    PATCH /api/questions/{question_id}/
    Body: {answered}
    Returns: {questionId, answered, version}
    """
    # Validate request data
    request_serializer = ToggleQuestionRequestSerializer(data=request.data)
    if not request_serializer.is_valid():
        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = request_serializer.validated_data

    # Validate that question exists and get game_id for broadcasting
    try:
        question = Question.objects.select_related(
            'category__board__game'
        ).get(id=question_id)
        game_id = question.category.board.game.id
    except Question.DoesNotExist:
        return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

    # Call service layer to update question status
    result = services.update_question_status(
        question_id=question_id,
        answered=data['answered']
    )

    # Broadcast update to all WebSocket clients
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'board_{game_id}',
        {
            'type': 'game_message',
            'message': {
                'type': 'toggle_question',
                'questionId': result.question_id,
                'answered': result.answered,
                'version': result.version
            }
        }
    )

    # Return response
    response_data = {
        'questionId': result.question_id,
        'answered': result.answered,
        'version': result.version
    }
    response_serializer = ToggleQuestionResponseSerializer(response_data)
    return Response(response_serializer.data, status=status.HTTP_200_OK)
