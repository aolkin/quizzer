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
    
    def test_record_new_correct_answer(self):
        """Test recording a new correct answer with default points."""
        result = services.record_player_answer(
            player_id=self.player1.id,
            question_id=self.q1.id,
            is_correct=True
        )
        
        self.assertEqual(result.player_id, self.player1.id)
        self.assertEqual(result.score, 100)  # Question default points
        self.assertEqual(result.version, 1)  # First version increment
        
        # Verify answer was created
        answer = PlayerAnswer.objects.get(player=self.player1, question=self.q1)
        self.assertTrue(answer.is_correct)
        self.assertIsNone(answer.points)  # No custom points
    
    def test_record_new_incorrect_answer(self):
        """Test recording a new incorrect answer with custom points."""
        result = services.record_player_answer(
            player_id=self.player1.id,
            question_id=self.q1.id,
            is_correct=False,
            points=0
        )
        
        self.assertEqual(result.score, 0)
        
        # Verify answer was created with custom points
        answer = PlayerAnswer.objects.get(player=self.player1, question=self.q1)
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
    
    def test_multiple_answers_score_accumulation(self):
        """Test that multiple answers to different questions accumulate correctly."""
        # Answer q1 correctly (100 points)
        services.record_player_answer(self.player1.id, self.q1.id, True)
        
        # Answer q2 with custom points
        services.record_player_answer(self.player1.id, self.q2.id, True, points=250)
        
        # Answer q3 incorrectly (300 points still counted)
        result = services.record_player_answer(self.player1.id, self.q3.id, False)
        
        # Total score should be 100 + 250 + 300 = 650
        self.assertEqual(result.score, 650)
    
    def test_version_increments_on_each_change(self):
        """Test that score_version increments on each record operation."""
        # First answer
        result1 = services.record_player_answer(self.player1.id, self.q1.id, True)
        self.assertEqual(result1.version, 1)
        
        # Second answer to different question
        result2 = services.record_player_answer(self.player1.id, self.q2.id, True)
        self.assertEqual(result2.version, 2)
        
        # Undo first answer
        result3 = services.record_player_answer(self.player1.id, self.q1.id, False)
        self.assertEqual(result3.version, 3)


class UpdateQuestionStatusTestCase(BaseGameTestCase, TransactionTestCase):
    """Tests for update_question_status service function."""
    
    def test_mark_question_as_answered(self):
        """Test marking a question as answered."""
        self.assertFalse(self.q1.answered)
        
        result = services.update_question_status(
            question_id=self.q1.id,
            answered=True
        )
        
        self.assertEqual(result.question_id, self.q1.id)
        self.assertTrue(result.answered)
        self.assertEqual(result.version, 1)
        
        # Verify in database
        self.q1.refresh_from_db()
        self.assertTrue(self.q1.answered)
    
    def test_mark_question_as_unanswered(self):
        """Test marking a question as unanswered."""
        self.q1.answered = True
        self.q1.save()
        
        result = services.update_question_status(
            question_id=self.q1.id,
            answered=False
        )
        
        self.assertFalse(result.answered)
        
        # Verify in database
        self.q1.refresh_from_db()
        self.assertFalse(self.q1.answered)
    
    def test_version_increments_on_status_change(self):
        """Test that state_version increments each time status is updated."""
        # First change
        result1 = services.update_question_status(self.q1.id, True)
        self.assertEqual(result1.version, 1)
        
        # Second change
        result2 = services.update_question_status(self.q1.id, False)
        self.assertEqual(result2.version, 2)
        
        # Third change
        result3 = services.update_question_status(self.q1.id, True)
        self.assertEqual(result3.version, 3)
