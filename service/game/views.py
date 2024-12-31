from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Game, Board
from .serializers import BoardSerializer, GameSerializer


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
