"""
Tests for REST API views.

These tests verify API endpoint behavior, validation, and integration
with the service layer.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from ..models import PlayerAnswer, Player
from .test_fixtures import BaseGameTestCase


class RecordAnswerViewTestCase(BaseGameTestCase):
    """Tests for the record_answer API endpoint."""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = f'/api/board/{self.board.id}/answers/'
    
    @patch('game.views.broadcast_to_board')
    def test_record_answer_success(self, mock_broadcast):
        """Test recording an answer successfully."""
        data = {
            'player_id': self.player1.id,
            'question_id': self.q1.id,
            'is_correct': True,
            'points': 150
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['player_id'], self.player1.id)
        self.assertEqual(response.data['score'], 150)
        self.assertIn('version', response.data)
        
        # Verify broadcast was called
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        self.assertEqual(call_args[0][0], self.board.id)
        self.assertEqual(call_args[0][1], 'update_score')
    
    def test_record_answer_player_not_in_game(self):
        """Test that recording answer fails when player not in game."""
        # Create a different game with a player
        other_game = self.game.__class__.objects.create(name="Other Game")
        other_team = self.team1.__class__.objects.create(game=other_game, name="Other Team")
        other_player = Player.objects.create(team=other_team, name="Other Player")
        
        data = {
            'player_id': other_player.id,
            'question_id': self.q1.id,
            'is_correct': True
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_record_answer_question_not_on_board(self):
        """Test that recording answer fails when question not on board."""
        # Create a different board with a question
        other_board = self.board.__class__.objects.create(game=self.game, name="Other Board", order=2)
        other_category = self.category.__class__.objects.create(
            board=other_board, name="Other Category", order=1
        )
        other_question = self.q1.__class__.objects.create(
            category=other_category, text="Q", answer="A", points=100, order=1
        )
        
        data = {
            'player_id': self.player1.id,
            'question_id': other_question.id,
            'is_correct': True
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_record_answer_invalid_data(self):
        """Test that invalid data returns validation errors."""
        data = {
            'player_id': 'invalid',
            'question_id': self.q1.id,
            'is_correct': True
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ToggleQuestionViewTestCase(BaseGameTestCase):
    """Tests for the toggle_question API endpoint."""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = f'/api/question/{self.q1.id}/'
    
    @patch('game.views.broadcast_to_board')
    def test_toggle_question_success(self, mock_broadcast):
        """Test toggling question status successfully."""
        data = {'answered': True}
        
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['question_id'], self.q1.id)
        self.assertTrue(response.data['answered'])
        self.assertIn('version', response.data)
        
        # Verify broadcast was called
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        self.assertEqual(call_args[0][0], self.board.id)
        self.assertEqual(call_args[0][1], 'toggle_question')
    
    def test_toggle_question_invalid_data(self):
        """Test that invalid data returns validation errors."""
        data = {'answered': 'not_a_boolean'}
        
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetBoardViewTestCase(BaseGameTestCase):
    """Tests for the get_board API endpoint."""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = f'/api/board/{self.board.id}/'
    
    def test_get_board_with_nested_data(self):
        """Test retrieving board with categories and questions."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.board.id)
        self.assertEqual(response.data['name'], 'Test Board')
        
        # Should include categories
        self.assertEqual(len(response.data['categories']), 1)
        category = response.data['categories'][0]
        self.assertEqual(category['name'], 'Test Category')
        
        # Should include questions
        self.assertEqual(len(category['questions']), 3)
    
    def test_get_board_not_found(self):
        """Test retrieving non-existent board returns 404."""
        response = self.client.get('/api/board/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetGameViewTestCase(BaseGameTestCase):
    """Tests for the get_game API endpoint."""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = f'/api/game/{self.game.id}/'
    
    def test_get_game_with_nested_data(self):
        """Test retrieving game with boards, teams, and players."""
        # Add some scores to verify score annotation
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.game.id)
        self.assertEqual(response.data['name'], 'Test Game')
        
        # Should include boards
        self.assertEqual(len(response.data['boards']), 1)
        
        # Should include teams with players
        self.assertEqual(len(response.data['teams']), 2)
        team1 = next(t for t in response.data['teams'] if t['name'] == 'Team 1')
        self.assertEqual(len(team1['players']), 2)
        
        # Should include player scores (using annotated score to avoid N+1)
        player1_data = next(p for p in team1['players'] if p['name'] == 'Player 1')
        self.assertEqual(player1_data['score'], 100)
    
    def test_get_game_not_found(self):
        """Test retrieving non-existent game returns 404."""
        response = self.client.get('/api/game/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
