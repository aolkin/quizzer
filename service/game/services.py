"""
Business logic for game operations.

This module contains the core business logic for game operations,
separated from WebSocket protocol handling and REST API views.
"""

from django.db import transaction
from typing import Optional

from .models import Player, PlayerAnswer, Question


def update_question_status(question_id: int, answered: bool) -> None:
    """
    Toggle question answered status.

    Args:
        question_id: ID of the question to update
        answered: Whether the question has been answered
    """
    Question.objects.filter(id=question_id).update(answered=answered)


@transaction.atomic
def record_player_answer(
    player_id: int,
    question_id: int,
    is_correct: bool,
    points: Optional[int] = None
) -> int:
    """
    Record a player's answer and return their updated score.

    This handles the business logic for tracking player answers:
    - If the correctness changes, delete the old answer and create a new one
    - If only points change, update the existing answer
    - If no previous answer exists, create a new one

    Args:
        player_id: ID of the player answering
        question_id: ID of the question being answered
        is_correct: Whether the answer was correct
        points: Optional custom point value (uses question's points if None)

    Returns:
        The player's updated total score
    """
    answer = PlayerAnswer.objects.filter(
        player_id=player_id,
        question_id=question_id
    ).first()

    if answer:
        # If correctness changed, delete and recreate
        if answer.is_correct != is_correct:
            answer.delete()
            PlayerAnswer.objects.create(
                player_id=player_id,
                question_id=question_id,
                is_correct=is_correct,
                points=points
            )
        # If only points changed, update
        elif answer.points != points:
            answer.points = points
            answer.save()
    else:
        # No previous answer, create new one
        PlayerAnswer.objects.create(
            player_id=player_id,
            question_id=question_id,
            is_correct=is_correct,
            points=points
        )

    # Return updated score
    return Player.objects.get(id=player_id).score
