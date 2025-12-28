"""
Tests for REST API views.

These tests verify API endpoint behavior, validation, and integration
with the service layer.
"""
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status
from ..models import PlayerAnswer, Player, Game, Team, Board, Category, Question
from .test_fixtures import BaseGameTestCase


class RecordAnswerViewTestCase(BaseGameTestCase):
    """Tests for the record_answer API endpoint."""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = f'/api/board/{self.board.id}/answers/'
    
    def _post_answer(self, player_id, question_id, is_correct, points=None):
        """Helper to post an answer to the API."""
        data = {
            'player_id': player_id,
            'question_id': question_id,
            'is_correct': is_correct
        }
        if points is not None:
            data['points'] = points
        return self.client.post(self.url, data, format='json')
    
    @patch('game.views.broadcast_to_board')
    def test_record_answer_success(self, mock_broadcast):
        """Test recording an answer successfully broadcasts score update."""
        response = self._post_answer(self.player1.id, self.q1.id, True, 150)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['player_id'], self.player1.id)
        self.assertEqual(response.data['score'], 150)
        self.assertIn('version', response.data)
        
        # Verify broadcast was called
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        self.assertEqual(call_args.args[0], self.board.id)
        self.assertEqual(call_args.args[1], 'update_score')
    
    def test_record_answer_validation_errors(self):
        """Test validation errors for invalid data and cross-game violations."""
        # Invalid data type
        response = self.client.post(self.url, {
            'player_id': 'invalid',
            'question_id': self.q1.id,
            'is_correct': True
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Player not in game
        other_game = Game.objects.create(name="Other Game")
        other_team = Team.objects.create(game=other_game, name="Other Team")
        other_player = Player.objects.create(team=other_team, name="Other Player")
        
        response = self._post_answer(other_player.id, self.q1.id, True)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Question not on board
        other_board = Board.objects.create(game=self.game, name="Other Board", order=2)
        other_category = Category.objects.create(board=other_board, name="Other Category", order=1)
        other_question = Question.objects.create(
            category=other_category, text="Q", answer="A", points=100, order=1
        )
        
        response = self._post_answer(self.player1.id, other_question.id, True)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class ToggleQuestionViewTestCase(BaseGameTestCase):
    """Tests for the toggle_question API endpoint."""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = f'/api/question/{self.q1.id}/'
    
    @patch('game.views.broadcast_to_board')
    def test_toggle_question_success(self, mock_broadcast):
        """Test toggling question status broadcasts update."""
        response = self.client.patch(self.url, {'answered': True}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['question_id'], self.q1.id)
        self.assertTrue(response.data['answered'])
        self.assertIn('version', response.data)
        
        # Verify broadcast
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        self.assertEqual(call_args.args[1], 'toggle_question')
    
    def test_toggle_question_invalid_data(self):
        """Test that invalid data returns validation errors."""
        response = self.client.patch(self.url, {'answered': 'not_a_boolean'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetEndpointsTestCase(BaseGameTestCase):
    """Tests for GET endpoints (board and game)."""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
    
    def test_get_board_with_nested_data(self):
        """Test retrieving board includes categories and questions."""
        response = self.client.get(f'/api/board/{self.board.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Board')
        self.assertEqual(len(response.data['categories']), 1)
        self.assertEqual(len(response.data['categories'][0]['questions']), 3)
    
    def test_get_game_with_nested_data(self):
        """Test retrieving game includes boards, teams, players with efficient score queries."""
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)
        
        response = self.client.get(f'/api/game/{self.game.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['boards']), 1)
        self.assertEqual(len(response.data['teams']), 2)
        
        # Verify annotated scores work
        team1 = next(t for t in response.data['teams'] if t['name'] == 'Team 1')
        player1_data = next(p for p in team1['players'] if p['name'] == 'Player 1')
        self.assertEqual(player1_data['score'], 100)
    
    def test_get_nonexistent_resources(self):
        """Test 404 for nonexistent board and game."""
        self.assertEqual(self.client.get('/api/board/99999/').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get('/api/game/99999/').status_code, status.HTTP_404_NOT_FOUND)
