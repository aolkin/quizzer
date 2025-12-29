"""
Tests for game models.

These tests verify model properties, constraints, and database behavior.
"""

from ..models import PlayerAnswer, Game
from .test_fixtures import BaseGameTestCase


class GameTestCase(BaseGameTestCase):
    """Tests for Game model."""

    def test_points_term_default(self):
        """Test that points_term defaults to 'points'."""
        game = Game.objects.create(name="Test Game", mode="jeopardy")
        self.assertEqual(game.points_term, "points")

    def test_points_term_custom(self):
        """Test that points_term can be customized."""
        game = Game.objects.create(name="Test Game", mode="jeopardy", points_term="eggs")
        self.assertEqual(game.points_term, "eggs")


class PlayerScoreTestCase(BaseGameTestCase):
    """Tests for Player.score property and queryset methods."""

    def test_score_calculation(self):
        """Test score calculation with multiple answers and annotated queries."""
        # Create answers with default and custom points
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)
        PlayerAnswer.objects.create(
            player=self.player1, question=self.q2, is_correct=True, points=250
        )
        PlayerAnswer.objects.create(player=self.player1, question=self.q3, is_correct=False)

        # Verify property score
        self.assertEqual(self.player1.score, 650)  # 100 + 250 + 300

        # Verify annotated score matches property
        annotated_player = (
            self.player1.__class__.objects.filter(id=self.player1.id).with_scores().first()
        )
        self.assertEqual(annotated_player.computed_score, 650)


class TeamScoreTestCase(BaseGameTestCase):
    """Tests for Team.total_score property."""

    def test_team_total_score(self):
        """Test team total score sums all players correctly across teams."""
        # Team 1 players score
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)  # 100
        PlayerAnswer.objects.create(
            player=self.player2, question=self.q2, is_correct=True, points=250
        )  # 250

        # Team 2 player scores
        PlayerAnswer.objects.create(player=self.player3, question=self.q3, is_correct=True)  # 300

        self.assertEqual(self.team1.total_score, 350)
        self.assertEqual(self.team2.total_score, 300)
