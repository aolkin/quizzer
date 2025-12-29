from dataclasses import asdict
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .channels import broadcast_to_game
from .models import Game, Board, Player, Question
from .serializers import (
    BoardSerializer,
    GameSerializer,
    RecordAnswerRequestSerializer,
    ToggleQuestionRequestSerializer,
    GameExportSerializer,
    GameImportSerializer,
)
from . import services


@api_view(["GET"])
def get_board(request, board_id):
    board = get_object_or_404(
        Board.objects.select_related("game").prefetch_related(
            "categories", "categories__questions"
        ),
        id=board_id,
    )
    return Response(BoardSerializer(board).data)


@api_view(["GET"])
def get_game(request, game_id):
    game = get_object_or_404(
        Game.objects.prefetch_related(
            "boards",
            models.Prefetch("teams__players", queryset=Player.objects.with_scores()),
            "teams",
        ),
        id=game_id,
    )
    return Response(GameSerializer(game).data)


@api_view(["POST"])
def record_answer(request, board_id):
    """
    Record a player's answer and broadcast the score update.

    POST /api/boards/{board_id}/answers/
    Body: {player_id, question_id, is_correct, points?}
    Returns: {player_id, score, version}
    """
    request_serializer = RecordAnswerRequestSerializer(data=request.data)
    if not request_serializer.is_valid():
        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = request_serializer.validated_data

    board = get_object_or_404(Board.objects.select_related("game"), id=board_id)

    player = get_object_or_404(Player.objects.select_related("team__game"), id=data["player_id"])
    if player.team.game_id != board.game_id:
        return Response(
            {"error": "Player does not belong to this game"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    question = get_object_or_404(
        Question.objects.select_related("category__board"), id=data["question_id"]
    )
    if question.category.board_id != board_id:
        return Response(
            {"error": "Question does not belong to this board"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = services.record_player_answer(
        player_id=data["player_id"],
        question_id=data["question_id"],
        is_correct=data["is_correct"],
        points=data.get("points"),
    )

    response_data = asdict(result)
    broadcast_to_game(board.game_id, "update_score", response_data)
    return Response(response_data)


@api_view(["PATCH"])
def toggle_question(request, question_id):
    """
    Toggle question answered status and broadcast the update.

    PATCH /api/questions/{question_id}/
    Body: {answered}
    Returns: {question_id, answered, version}
    """
    request_serializer = ToggleQuestionRequestSerializer(data=request.data)
    if not request_serializer.is_valid():
        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = request_serializer.validated_data

    question = get_object_or_404(
        Question.objects.select_related("category__board__game"), id=question_id
    )
    game_id = question.category.board.game_id

    result = services.update_question_status(question_id=question_id, answered=data["answered"])

    response_data = asdict(result)
    broadcast_to_game(game_id, "toggle_question", response_data)
    return Response(response_data)


@api_view(["GET"])
def export_game(request, game_id):
    export_mode = request.GET.get("mode", "template")
    pretty = request.GET.get("pretty", "false").lower() == "true"

    if export_mode not in ["template", "full"]:
        return Response(
            {"error": "Invalid mode. Must be 'template' or 'full'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    game = get_object_or_404(
        Game.objects.prefetch_related(
            "boards__categories__questions",
            "teams__players__answers__question",
        ),
        id=game_id,
    )

    if export_mode == "full":
        question_index_map = {}
        question_index = 0
        for board in game.boards.all():
            for category in board.categories.all():
                for question in category.questions.all():
                    question_index_map[question.id] = question_index
                    question_index += 1

        for team in game.teams.all():
            for player in team.players.all():
                answers_export = []
                for answer in player.answers.all():
                    if answer.question_id in question_index_map:
                        answer_data = {
                            "question_index": question_index_map[answer.question_id],
                            "is_correct": answer.is_correct,
                            "answered_at": answer.answered_at.isoformat(),
                        }
                        if answer.points is not None:
                            answer_data["points"] = answer.points
                        answers_export.append(answer_data)
                if answers_export:
                    player.answers_export = answers_export

    serializer = GameExportSerializer(game, context={"export_mode": export_mode})

    export_data = {
        "export_version": "1.0",
        "mode": export_mode,
        "exported_at": timezone.now().isoformat(),
        "game": serializer.get_game(game),
    }

    timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    safe_game_name = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in game.name)
    filename = f"{safe_game_name}-{timestamp}.json"

    if pretty:
        return JsonResponse(
            export_data,
            json_dumps_params={"indent": 2, "ensure_ascii": False},
        )
    else:
        return JsonResponse(
            export_data,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@api_view(["POST"])
def import_game(request):
    serializer = GameImportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = serializer.save()
        return Response(result, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {"error": f"Import failed: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
