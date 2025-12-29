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
        self.url = f"/api/board/{self.board.id}/answers/"

    def _post_answer(self, player_id, question_id, is_correct, points=None):
        """Helper to post an answer to the API."""
        data = {
            "player_id": player_id,
            "question_id": question_id,
            "is_correct": is_correct,
        }
        if points is not None:
            data["points"] = points
        return self.client.post(self.url, data, format="json")

    @patch("game.views.broadcast_to_game")
    def test_record_answer_success(self, mock_broadcast):
        """Test recording an answer successfully broadcasts score update."""
        response = self._post_answer(self.player1.id, self.q1.id, True, 150)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["player_id"], self.player1.id)
        self.assertEqual(response.data["score"], 150)
        self.assertIn("version", response.data)

        # Verify broadcast was called with game_id
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        self.assertEqual(call_args.args[0], self.game.id)
        self.assertEqual(call_args.args[1], "update_score")

    def test_record_answer_validation_errors(self):
        """Test validation errors for invalid data and cross-game violations."""
        # Invalid data type
        response = self.client.post(
            self.url,
            {"player_id": "invalid", "question_id": self.q1.id, "is_correct": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Player not in game
        other_game = Game.objects.create(name="Other Game")
        other_team = Team.objects.create(game=other_game, name="Other Team")
        other_player = Player.objects.create(team=other_team, name="Other Player")

        response = self._post_answer(other_player.id, self.q1.id, True)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

        # Question not on board
        other_board = Board.objects.create(game=self.game, name="Other Board", order=2)
        other_category = Category.objects.create(board=other_board, name="Other Category", order=1)
        other_question = Question.objects.create(
            category=other_category, text="Q", answer="A", points=100, order=1
        )

        response = self._post_answer(self.player1.id, other_question.id, True)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)


class ToggleQuestionViewTestCase(BaseGameTestCase):
    """Tests for the toggle_question API endpoint."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = f"/api/question/{self.q1.id}/"

    @patch("game.views.broadcast_to_game")
    def test_toggle_question_success(self, mock_broadcast):
        """Test toggling question status broadcasts update."""
        response = self.client.patch(self.url, {"answered": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["question_id"], self.q1.id)
        self.assertTrue(response.data["answered"])
        self.assertIn("version", response.data)

        # Verify broadcast was called with game_id
        mock_broadcast.assert_called_once()
        call_args = mock_broadcast.call_args
        self.assertEqual(call_args.args[0], self.game.id)
        self.assertEqual(call_args.args[1], "toggle_question")

    def test_toggle_question_invalid_data(self):
        """Test that invalid data returns validation errors."""
        response = self.client.patch(self.url, {"answered": "not_a_boolean"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetEndpointsTestCase(BaseGameTestCase):
    """Tests for GET endpoints (board and game)."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_get_board_with_nested_data(self):
        """Test retrieving board includes categories and questions."""
        response = self.client.get(f"/api/board/{self.board.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Board")
        self.assertEqual(len(response.data["categories"]), 1)
        self.assertEqual(len(response.data["categories"][0]["questions"]), 3)

    def test_get_game_with_nested_data(self):
        """Test retrieving game includes boards, teams, players with efficient score queries."""
        PlayerAnswer.objects.create(player=self.player1, question=self.q1, is_correct=True)

        response = self.client.get(f"/api/game/{self.game.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["boards"]), 1)
        self.assertEqual(len(response.data["teams"]), 2)

        # Verify annotated scores work
        team1 = next(t for t in response.data["teams"] if t["name"] == "Team 1")
        player1_data = next(p for p in team1["players"] if p["name"] == "Player 1")
        self.assertEqual(player1_data["score"], 100)


class ExportGameViewTestCase(BaseGameTestCase):
    """Tests for the export_game API endpoint."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_export_template_mode(self):
        """Test exporting game in template mode excludes teams and players."""
        url = f"/api/game/{self.game.id}/export?mode=template"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("attachment", response["Content-Disposition"])

        data = response.json()
        self.assertEqual(data["export_version"], "1.0")
        self.assertEqual(data["mode"], "template")
        self.assertIn("exported_at", data)

        game_data = data["game"]
        self.assertEqual(game_data["name"], "Test Game")
        self.assertEqual(game_data["mode"], "jeopardy")
        self.assertEqual(len(game_data["boards"]), 1)

        # Verify board structure
        board = game_data["boards"][0]
        self.assertEqual(board["name"], "Test Board")
        self.assertEqual(len(board["categories"]), 1)

        # Verify category structure
        category = board["categories"][0]
        self.assertEqual(category["name"], "Test Category")
        self.assertEqual(len(category["questions"]), 3)

        # Verify question structure
        question = category["questions"][0]
        self.assertEqual(question["text"], "Question 1")
        self.assertEqual(question["answer"], "Answer 1")
        self.assertEqual(question["points"], 100)
        # Type should not be present if it's "text" (default)
        self.assertNotIn("type", question)

        # Verify metadata
        self.assertIn("metadata", game_data)
        self.assertEqual(game_data["metadata"]["original_game_id"], self.game.id)

        # Teams should not be present in template mode
        self.assertNotIn("teams", game_data)

    def test_export_full_mode(self):
        """Test exporting game in full mode includes teams, players, and answers."""
        # Add an answer to test answer export
        PlayerAnswer.objects.create(
            player=self.player1, question=self.q1, is_correct=True, points=150
        )

        url = f"/api/game/{self.game.id}/export?mode=full"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["mode"], "full")

        game_data = data["game"]
        # Teams should be present in full mode
        self.assertIn("teams", game_data)
        self.assertEqual(len(game_data["teams"]), 2)

        # Verify team structure
        team1 = game_data["teams"][0]
        self.assertEqual(team1["name"], "Team 1")
        self.assertEqual(team1["color"], "#FF0000")
        self.assertEqual(len(team1["players"]), 2)

        # Verify player structure
        player1 = team1["players"][0]
        self.assertEqual(player1["name"], "Player 1")
        self.assertEqual(player1["buzzer"], 1)

        # Verify answer structure
        self.assertIn("answers", player1)
        self.assertEqual(len(player1["answers"]), 1)
        answer = player1["answers"][0]
        self.assertEqual(answer["question_index"], 0)
        self.assertTrue(answer["is_correct"])
        self.assertEqual(answer["points"], 150)
        self.assertIn("answered_at", answer)

    def test_export_pretty_formatting(self):
        """Test that pretty parameter formats JSON with indentation."""
        url = f"/api/game/{self.game.id}/export?mode=template&pretty=true"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the response content is indented (contains newlines and spaces)
        content = response.content.decode("utf-8")
        self.assertIn("\n", content)
        self.assertIn("  ", content)  # Indentation

    def test_export_invalid_mode(self):
        """Test that invalid mode returns error."""
        url = f"/api/game/{self.game.id}/export?mode=invalid"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())

    def test_export_nonexistent_game(self):
        """Test that exporting nonexistent game returns 404."""
        url = "/api/game/99999/export?mode=template"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_export_question_with_media(self):
        """Test that questions with media_url include it in export."""
        # Add a question with media
        Question.objects.create(
            category=self.category,
            text="Image Question",
            answer="Image Answer",
            points=400,
            type="image",
            media_url="https://example.com/image.jpg",
            order=4,
        )

        url = f"/api/game/{self.game.id}/export?mode=template"
        response = self.client.get(url)

        data = response.json()
        questions = data["game"]["boards"][0]["categories"][0]["questions"]
        image_question = questions[3]  # Fourth question

        self.assertEqual(image_question["type"], "image")
        self.assertEqual(image_question["media_url"], "https://example.com/image.jpg")


class ImportGameViewTestCase(BaseGameTestCase):
    """Tests for the import_game API endpoint."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = "/api/game/import"

    def _get_template_export_data(self):
        """Helper to get a valid template export data structure."""
        return {
            "export_version": "1.0",
            "mode": "template",
            "exported_at": "2025-12-29T10:30:00Z",
            "game": {
                "name": "Imported Game",
                "mode": "jeopardy",
                "boards": [
                    {
                        "name": "Round 1",
                        "categories": [
                            {
                                "name": "Science",
                                "questions": [
                                    {
                                        "text": "What is H2O?",
                                        "answer": "Water",
                                        "points": 100,
                                    },
                                    {
                                        "text": "What is CO2?",
                                        "answer": "Carbon Dioxide",
                                        "points": 200,
                                    },
                                ],
                            },
                            {
                                "name": "History",
                                "questions": [
                                    {
                                        "text": "Who was the first president?",
                                        "answer": "George Washington",
                                        "points": 100,
                                    },
                                ],
                            },
                        ],
                    }
                ],
                "metadata": {"original_game_id": 123, "created_at": "2025-12-20T10:00:00Z"},
            },
        }

    def test_import_template_mode(self):
        """Test importing a template creates game structure without teams."""
        data = self._get_template_export_data()
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.json()

        self.assertIn("game_id", result)
        self.assertEqual(result["game_name"], "Imported Game")
        self.assertEqual(result["boards_created"], 1)
        self.assertEqual(result["categories_created"], 2)
        self.assertEqual(result["questions_created"], 3)
        self.assertEqual(result["teams_created"], 0)
        self.assertEqual(result["players_created"], 0)
        self.assertEqual(result["import_mode"], "template")

        # Verify the game was created in the database
        game = Game.objects.get(id=result["game_id"])
        self.assertEqual(game.name, "Imported Game")
        self.assertEqual(game.mode, "jeopardy")
        self.assertEqual(game.boards.count(), 1)

        # Verify board structure
        board = game.boards.first()
        self.assertEqual(board.name, "Round 1")
        self.assertEqual(board.order, 0)
        self.assertEqual(board.categories.count(), 2)

        # Verify categories
        categories = list(board.categories.all())
        self.assertEqual(categories[0].name, "Science")
        self.assertEqual(categories[0].order, 0)
        self.assertEqual(categories[1].name, "History")
        self.assertEqual(categories[1].order, 1)

        # Verify questions
        science_questions = list(categories[0].questions.all())
        self.assertEqual(len(science_questions), 2)
        self.assertEqual(science_questions[0].text, "What is H2O?")
        self.assertEqual(science_questions[0].answer, "Water")
        self.assertEqual(science_questions[0].points, 100)
        self.assertEqual(science_questions[0].order, 0)

    def test_import_full_mode_with_teams(self):
        """Test importing full mode creates teams, players, and answers."""
        data = self._get_template_export_data()
        data["mode"] = "full"
        data["game"]["teams"] = [
            {
                "name": "Team Alpha",
                "color": "#FF0000",
                "players": [
                    {
                        "name": "Alice",
                        "buzzer": 1,
                        "answers": [
                            {
                                "question_index": 0,
                                "is_correct": True,
                                "points": 150,
                                "answered_at": "2025-12-29T11:00:00Z",
                            }
                        ],
                    },
                    {"name": "Bob"},  # No buzzer or answers
                ],
            }
        ]

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.json()

        self.assertEqual(result["teams_created"], 1)
        self.assertEqual(result["players_created"], 2)
        self.assertEqual(result["answers_imported"], 1)
        self.assertEqual(result["import_mode"], "full")

        # Verify team was created
        game = Game.objects.get(id=result["game_id"])
        team = game.teams.first()
        self.assertEqual(team.name, "Team Alpha")
        self.assertEqual(team.color, "#FF0000")
        self.assertEqual(team.players.count(), 2)

        # Verify players
        players = list(team.players.all())
        alice = players[0]
        self.assertEqual(alice.name, "Alice")
        self.assertEqual(alice.buzzer, 1)

        bob = players[1]
        self.assertEqual(bob.name, "Bob")
        self.assertIsNone(bob.buzzer)

        # Verify answer
        self.assertEqual(alice.answers.count(), 1)
        answer = alice.answers.first()
        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.points, 150)

    def test_import_invalid_version(self):
        """Test that unsupported export version returns error."""
        data = self._get_template_export_data()
        data["export_version"] = "2.0"

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("export_version", response.json())

    def test_import_invalid_mode(self):
        """Test that invalid mode returns error."""
        data = self._get_template_export_data()
        data["mode"] = "invalid"

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_import_missing_required_fields(self):
        """Test that missing required fields returns validation error."""
        data = {"export_version": "1.0", "mode": "template"}
        # Missing 'game' field

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("game", response.json())

    def test_import_question_with_media(self):
        """Test importing questions with media_url and type."""
        data = self._get_template_export_data()
        data["game"]["boards"][0]["categories"][0]["questions"].append(
            {
                "text": "Image question",
                "answer": "Image answer",
                "points": 300,
                "type": "image",
                "media_url": "https://example.com/image.jpg",
            }
        )

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.json()
        self.assertEqual(result["questions_created"], 4)

        # Verify the image question was created correctly
        game = Game.objects.get(id=result["game_id"])
        questions = game.boards.first().categories.first().questions.all()
        image_question = questions[2]
        self.assertEqual(image_question.type, "image")
        self.assertEqual(image_question.media_url, "https://example.com/image.jpg")

    def test_round_trip_export_import(self):
        """Test that exporting and re-importing a game preserves structure."""
        # Export the test game
        export_url = f"/api/game/{self.game.id}/export?mode=template"
        export_response = self.client.get(export_url)
        export_data = export_response.json()

        # Import it back
        import_response = self.client.post(self.url, export_data, format="json")

        self.assertEqual(import_response.status_code, status.HTTP_201_CREATED)
        result = import_response.json()

        # Verify same structure
        original_game = Game.objects.get(id=self.game.id)
        imported_game = Game.objects.get(id=result["game_id"])

        self.assertEqual(imported_game.name, original_game.name)
        self.assertEqual(imported_game.mode, original_game.mode)
        self.assertEqual(imported_game.boards.count(), original_game.boards.count())

        # Verify questions match
        orig_questions = Question.objects.filter(category__board__game=original_game).count()
        imported_questions = Question.objects.filter(category__board__game=imported_game).count()
        self.assertEqual(imported_questions, orig_questions)
