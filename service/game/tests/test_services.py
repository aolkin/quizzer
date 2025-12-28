"""
Tests for service layer business logic.

These tests verify the core business logic in services.py, including:
- Recording player answers with undo mechanism
- Updating question status
- Version number management
"""
from django.test import TransactionTestCase
from ..models import PlayerAnswer
from .. import services
from .test_fixtures import BaseGameTestCase


class RecordPlayerAnswerTestCase(BaseGameTestCase, TransactionTestCase):
    """Tests for record_player_answer service function."""
    
    def test_record_new_answers(self):
        """Test recording new correct and incorrect answers."""
        # Correct answer with default points
        result = services.record_player_answer(
            player_id=self.player1.id,
            question_id=self.q1.id,
            is_correct=True
        )
        
        self.assertEqual(result.player_id, self.player1.id)
        self.assertEqual(result.score, 100)  # Question default points
        self.assertEqual(result.version, 1)  # First version increment
        
        answer = PlayerAnswer.objects.get(player=self.player1, question=self.q1)
        self.assertTrue(answer.is_correct)
        self.assertIsNone(answer.points)  # No custom points
        
        # Incorrect answer with custom points
        result = services.record_player_answer(
            player_id=self.player1.id,
            question_id=self.q2.id,
            is_correct=False,
            points=0
        )
        
        self.assertEqual(result.score, 100)  # Previous score still counts
        answer = PlayerAnswer.objects.get(player=self.player1, question=self.q2)
        self.assertFalse(answer.is_correct)
        self.assertEqual(answer.points, 0)
    
    def test_correctness_change_deletes_answer(self):
        """Test that changing correctness deletes the answer (undo mechanism)."""
        # Record initial correct answer
        services.record_player_answer(
            player_id=self.player1.id,
            question_id=self.q1.id,
            is_correct=True
        )
        self.assertEqual(PlayerAnswer.objects.filter(player=self.player1).count(), 1)
        
        # Change to incorrect - should delete the answer
        result = services.record_player_answer(
            player_id=self.player1.id,
            question_id=self.q1.id,
            is_correct=False
        )
        
        # Answer should be deleted, score should be 0
        self.assertEqual(result.score, 0)
        self.assertEqual(PlayerAnswer.objects.filter(player=self.player1).count(), 0)
    
    def test_points_change_updates_answer(self):
        """Test that changing only points (same correctness) updates the answer."""
        # Record initial answer with custom points
        services.record_player_answer(
            player_id=self.player1.id,
            question_id=self.q1.id,
            is_correct=True,
            points=150
        )
        
        # Update points (same correctness)
        result = services.record_player_answer(
            player_id=self.player1.id,
            question_id=self.q1.id,
            is_correct=True,
            points=200
        )
        
        # Should still have exactly one answer, but with updated points
        self.assertEqual(PlayerAnswer.objects.filter(player=self.player1).count(), 1)
        answer = PlayerAnswer.objects.get(player=self.player1, question=self.q1)
        self.assertEqual(answer.points, 200)
        self.assertEqual(result.score, 200)
    
    def test_multiple_answers_and_version_increments(self):
        """Test multiple answers accumulate correctly and versions increment."""
        # Answer q1 correctly (100 points)
        result1 = services.record_player_answer(self.player1.id, self.q1.id, True)
        self.assertEqual(result1.version, 1)
        
        # Answer q2 with custom points
        result2 = services.record_player_answer(self.player1.id, self.q2.id, True, points=250)
        self.assertEqual(result2.version, 2)
        
        # Answer q3 incorrectly (300 points still counted)
        result3 = services.record_player_answer(self.player1.id, self.q3.id, False)
        
        # Total score should be 100 + 250 + 300 = 650
        self.assertEqual(result3.score, 650)
        self.assertEqual(result3.version, 3)


class UpdateQuestionStatusTestCase(BaseGameTestCase, TransactionTestCase):
    """Tests for update_question_status service function."""
    
    def test_toggle_question_and_version_increments(self):
        """Test toggling question status and version increments."""
        self.assertFalse(self.q1.answered)
        
        # Mark as answered
        result1 = services.update_question_status(self.q1.id, True)
        self.assertEqual(result1.question_id, self.q1.id)
        self.assertTrue(result1.answered)
        self.assertEqual(result1.version, 1)
        
        self.q1.refresh_from_db()
        self.assertTrue(self.q1.answered)
        
        # Mark as unanswered
        result2 = services.update_question_status(self.q1.id, False)
        self.assertFalse(result2.answered)
        self.assertEqual(result2.version, 2)
        
        self.q1.refresh_from_db()
        self.assertFalse(self.q1.answered)

