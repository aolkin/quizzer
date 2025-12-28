"""
Shared test fixtures and utilities for the game app.
"""

from django.test import TestCase
from ..models import Game, Board, Category, Question, Team, Player


class BaseGameTestCase(TestCase):
    """Base test case with common game fixtures."""

    def setUp(self):
        """Set up test data used by multiple test cases."""
        self.game = Game.objects.create(name="Test Game", mode="jeopardy")
        self.board = Board.objects.create(game=self.game, name="Test Board", order=1)
        self.category = Category.objects.create(
            board=self.board, name="Test Category", order=1
        )

        # Create questions with varying point values
        self.q1 = Question.objects.create(
            category=self.category,
            text="Question 1",
            answer="Answer 1",
            points=100,
            order=1,
        )
        self.q2 = Question.objects.create(
            category=self.category,
            text="Question 2",
            answer="Answer 2",
            points=200,
            order=2,
        )
        self.q3 = Question.objects.create(
            category=self.category,
            text="Question 3",
            answer="Answer 3",
            points=300,
            order=3,
        )

        # Create teams and players
        self.team1 = Team.objects.create(game=self.game, name="Team 1", color="#FF0000")
        self.team2 = Team.objects.create(game=self.game, name="Team 2", color="#0000FF")
        self.player1 = Player.objects.create(team=self.team1, name="Player 1", buzzer=1)
        self.player2 = Player.objects.create(team=self.team1, name="Player 2", buzzer=2)
        self.player3 = Player.objects.create(team=self.team2, name="Player 3", buzzer=3)
