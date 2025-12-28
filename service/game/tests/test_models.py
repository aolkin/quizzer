"""
Tests for game models.

These tests verify model properties, constraints, and database behavior.
"""
from django.db import IntegrityError
from django.test import TestCase
from ..models import PlayerAnswer
from .test_fixtures import BaseGameTestCase


class PlayerScoreTestCase(BaseGameTestCase):
    """Tests for Player.score property and queryset methods."""
    
    def test_score_with_multiple_answers(self):
        """Test score calculation with multiple answers (default and custom points)."""
        # Answer with default points
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)
        # Answer with custom points
        PlayerAnswer.objects.create(player=self.player1, question=self.q2, is_correct=True, points=250)
        # Another answer with default points
        PlayerAnswer.objects.create(player=self.player1, question=self.q3, is_correct=False)
        
        # Score should be 100 + 250 + 300 = 650
        self.assertEqual(self.player1.score, 650)
    
    def test_score_empty(self):
        """Test that score is 0 when player has no answers."""
        self.assertEqual(self.player1.score, 0)
    
    def test_annotated_score_matches_property(self):
        """Test that annotated score matches the property score."""
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)
        PlayerAnswer.objects.create(player=self.player1, question=self.q2, is_correct=True, points=250)
        
        # Get player with annotated score
        annotated_player = self.player1.__class__.objects.filter(
            id=self.player1.id
        ).with_scores().first()
        
        # Verify annotated score matches property
        self.assertEqual(annotated_player.computed_score, self.player1.score)
        self.assertEqual(annotated_player.computed_score, 350)  # 100 + 250


class TeamScoreTestCase(BaseGameTestCase):
    """Tests for Team.total_score property."""
    
    def test_team_total_score_multiple_players(self):
        """Test team total score sums all players correctly."""
        # Player 1 scores
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)  # 100
        
        # Player 2 scores
        PlayerAnswer.objects.create(player=self.player2, question=self.q2, is_correct=True, points=250)  # 250
        
        # Team 1 total should be 100 + 250 = 350
        self.assertEqual(self.team1.total_score, 350)
    
    def test_team_total_score_empty(self):
        """Test team total score is 0 when no players have scored."""
        self.assertEqual(self.team1.total_score, 0)
    
    def test_team_total_score_different_teams(self):
        """Test that team scores are independent."""
        # Team 1 player scores
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)  # 100
        
        # Team 2 player scores
        PlayerAnswer.objects.create(player=self.player3, question=self.q2, is_correct=True)  # 200
        
        self.assertEqual(self.team1.total_score, 100)
        self.assertEqual(self.team2.total_score, 200)


class PlayerAnswerConstraintTestCase(BaseGameTestCase):
    """Tests for PlayerAnswer unique constraints."""
    
    def test_cannot_answer_same_question_twice(self):
        """Test that a player cannot answer the same question twice."""
        PlayerAnswer.objects.create(
            player=self.player1,
            question=self.q1,
            is_correct=True
        )
        
        # Attempting to create another answer for the same player/question should fail
        with self.assertRaises(IntegrityError):
            PlayerAnswer.objects.create(
                player=self.player1,
                question=self.q1,
                is_correct=False
            )
    
    def test_different_players_can_answer_same_question(self):
        """Test that different players can answer the same question."""
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)
        PlayerAnswer.objects.create(player=self.player2, question=self.q1, is_correct=False)
        
        # Both answers should exist
        self.assertEqual(PlayerAnswer.objects.filter(question=self.q1).count(), 2)
