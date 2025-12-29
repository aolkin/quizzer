"""
Tests for serializers.

These tests verify that serializers correctly serialize model data,
handle nested relationships, and use annotated scores efficiently.
"""

from ..models import PlayerAnswer
from ..serializers import GameSerializer, BoardSerializer, PlayerSerializer
from .test_fixtures import BaseGameTestCase


class GameSerializerTestCase(BaseGameTestCase):
    """Tests for GameSerializer nested serialization."""

    def test_game_serialization_includes_boards_and_teams(self):
        """Test that game serialization includes nested boards and teams."""
        serializer = GameSerializer(self.game)
        data = serializer.data

        self.assertEqual(data["id"], self.game.id)
        self.assertEqual(data["name"], "Test Game")
        self.assertEqual(data["mode"], "jeopardy")
        self.assertEqual(data["points_term"], "points")

        # Should have boards
        self.assertEqual(len(data["boards"]), 1)
        self.assertEqual(data["boards"][0]["name"], "Test Board")

        # Should have teams with players
        self.assertEqual(len(data["teams"]), 2)
        team1_data = next(t for t in data["teams"] if t["name"] == "Team 1")
        self.assertEqual(len(team1_data["players"]), 2)
        self.assertEqual(team1_data["color"], "#FF0000")


class BoardSerializerTestCase(BaseGameTestCase):
    """Tests for BoardSerializer nested serialization."""

    def test_board_serialization_includes_categories_and_questions(self):
        """Test that board serialization includes nested categories and questions."""
        serializer = BoardSerializer(self.board)
        data = serializer.data

        self.assertEqual(data["id"], self.board.id)
        self.assertEqual(data["name"], "Test Board")

        # Should have categories
        self.assertEqual(len(data["categories"]), 1)
        category_data = data["categories"][0]
        self.assertEqual(category_data["name"], "Test Category")

        # Should have questions
        self.assertEqual(len(category_data["questions"]), 3)
        q1_data = next(q for q in category_data["questions"] if q["points"] == 100)
        self.assertEqual(q1_data["text"], "Question 1")
        self.assertEqual(q1_data["answer"], "Answer 1")
        self.assertFalse(q1_data["answered"])


class PlayerSerializerTestCase(BaseGameTestCase):
    """Tests for PlayerSerializer score handling."""

    def test_player_serializer_uses_annotated_score(self):
        """Test that PlayerSerializer uses annotated score when available."""
        # Add some answers
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)
        PlayerAnswer.objects.create(
            player=self.player1, question=self.q2, is_correct=True, points=250
        )

        # Get player with annotated score
        from ..models import Player

        annotated_player = Player.objects.filter(id=self.player1.id).with_scores().first()

        serializer = PlayerSerializer(annotated_player)
        data = serializer.data

        # Should use annotated computed_score
        self.assertEqual(data["score"], 350)
        self.assertEqual(data["name"], "Player 1")
        self.assertEqual(data["buzzer"], 1)

    def test_player_serializer_falls_back_to_property(self):
        """Test that PlayerSerializer falls back to property when not annotated."""
        # Add some answers
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)

        # Get player without annotation
        serializer = PlayerSerializer(self.player1)
        data = serializer.data

        # Should still compute score using property
        self.assertEqual(data["score"], 100)
