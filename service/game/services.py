"""
Business logic for game operations.

This module contains the core business logic for game operations,
separated from WebSocket protocol handling and REST API views.
"""

from dataclasses import dataclass
from django.db import transaction
from django.db.models import F, Sum, Q, Value, IntegerField
from typing import Optional

from .models import Player, PlayerAnswer, Question


@dataclass
class PlayerAnswerResult:
    player_id: int
    score: int
    version: int


@dataclass
class QuestionStatusResult:
    question_id: int
    answered: bool
    version: int


@transaction.atomic
def update_question_status(question_id: int, answered: bool) -> QuestionStatusResult:
    """
    Toggle question answered status.

    Args:
        question_id: ID of the question to update
        answered: Whether the question has been answered

    Returns:
        QuestionStatusResult with question_id, answered status, and version
    """
    question = Question.objects.select_for_update().get(id=question_id)
    question.answered = answered
    question.state_version = F('state_version') + 1
    question.save(update_fields=['answered', 'state_version'])
    question.refresh_from_db()

    return QuestionStatusResult(
        question_id=question.id,
        answered=question.answered,
        version=question.state_version
    )


@transaction.atomic
def record_player_answer(
    player_id: int,
    question_id: int,
    is_correct: bool,
    points: Optional[int] = None
) -> PlayerAnswerResult:
    """
    Record a player's answer and return their updated score with version.

    This handles the business logic for tracking player answers with an undo mechanism:
    - If the correctness changes (e.g., correct→incorrect), delete the existing answer
      This acts as an "undo" - clicking the opposite button removes the scoring entirely
      rather than flipping it, preventing accidental double scoring
    - If only points change (same correctness), update the existing answer
    - If no previous answer exists, create a new one

    Args:
        player_id: ID of the player answering
        question_id: ID of the question being answered
        is_correct: Whether the answer was correct
        points: Optional custom point value (uses question's points if None)

    Returns:
        PlayerAnswerResult with player_id, updated score, and version
    """
    try:
        answer = PlayerAnswer.objects.get(
            player_id=player_id,
            question_id=question_id
        )
        # If correctness changed, delete the answer (undo mechanism)
        if answer.is_correct != is_correct:
            answer.delete()
        # If only points changed (same correctness), update the answer
        elif answer.points != points:
            answer.points = points
            answer.save()
    except PlayerAnswer.DoesNotExist:
        # No previous answer exists, create new one
        PlayerAnswer.objects.create(
            player_id=player_id,
            question_id=question_id,
            is_correct=is_correct,
            points=points
        )

    # Get player with lock and increment version
    player = Player.objects.select_for_update().get(id=player_id)
    player.score_version = F('score_version') + 1
    player.save(update_fields=['score_version'])
    player.refresh_from_db()
    
    # Compute score efficiently using database aggregation
    # For each answer, use answer.points if not null, otherwise question.points
    from django.db.models import Case, When
    
    score_result = PlayerAnswer.objects.filter(player_id=player_id).aggregate(
        total=Sum(
            Case(
                When(points__isnull=False, then='points'),
                default='question__points',
            ),
            default=Value(0, output_field=IntegerField())
        )
    )
    score = score_result['total'] or 0

    return PlayerAnswerResult(
        player_id=player.id,
        score=score,
        version=player.score_version
    )
