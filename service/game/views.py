from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Game, Board
from .serializers import BoardSerializer

@api_view(['GET'])
def get_board(request, board_id):
    board = Board.objects.select_related('game').prefetch_related(
        'categories',
        'categories__questions'
    ).get(id=board_id)
    return Response(BoardSerializer(board).data)
