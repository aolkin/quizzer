"""
Tests for game models.

These tests verify model properties, constraints, and database behavior.
"""
from django.db import IntegrityError
from ..models import PlayerAnswer
from .test_fixtures import BaseGameTestCase


class PlayerScoreTestCase(BaseGameTestCase):
    """Tests for Player.score property and queryset methods."""
    
    def test_score_calculation(self):
        """Test score calculation with multiple answers and annotated queries."""
        # Create answers with default and custom points
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)
        PlayerAnswer.objects.create(player=self.player1, question=self.q2, is_correct=True, points=250)
        PlayerAnswer.objects.create(player=self.player1, question=self.q3, is_correct=False)
        
        # Verify property score
        self.assertEqual(self.player1.score, 650)  # 100 + 250 + 300
        
        # Verify annotated score matches property
        annotated_player = self.player1.__class__.objects.filter(
            id=self.player1.id
        ).with_scores().first()
        self.assertEqual(annotated_player.computed_score, 650)
    
    def test_score_empty(self):
        """Test that score is 0 when player has no answers."""
        self.assertEqual(self.player1.score, 0)


class TeamScoreTestCase(BaseGameTestCase):
    """Tests for Team.total_score property."""
    
    def test_team_total_score(self):
        """Test team total score sums all players correctly across teams."""
        # Team 1 players score
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)  # 100
        PlayerAnswer.objects.create(player=self.player2, question=self.q2, is_correct=True, points=250)  # 250
        
        # Team 2 player scores
        PlayerAnswer.objects.create(player=self.player3, question=self.q3, is_correct=True)  # 300
        
        self.assertEqual(self.team1.total_score, 350)
        self.assertEqual(self.team2.total_score, 300)
    
    def test_team_total_score_empty(self):
        """Test team total score is 0 when no players have scored."""
        self.assertEqual(self.team1.total_score, 0)


class PlayerAnswerConstraintTestCase(BaseGameTestCase):
    """Tests for PlayerAnswer unique constraints."""
    
    def test_cannot_answer_same_question_twice(self):
        """Test that a player cannot answer the same question twice."""
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)
        
        # Same player, same question should fail
        with self.assertRaises(IntegrityError):
            PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=False)
    
    def test_different_players_can_answer_same_question(self):
        """Test that different players can answer the same question."""
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)
        PlayerAnswer.objects.create(player=self.player2, question=self.q1, is_correct=False)
        self.assertEqual(PlayerAnswer.objects.filter(question=self.q1).count(), 2)
