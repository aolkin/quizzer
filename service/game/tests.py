from django.test import TestCase
from django.db.models import Case, When, Sum, Value, IntegerField
from .models import Game, Board, Category, Question, Team, Player, PlayerAnswer


class PlayerScoreTestCase(TestCase):
    def setUp(self):
        """Set up test data."""
        self.game = Game.objects.create(name="Test Game")
        self.board = Board.objects.create(game=self.game, name="Test Board", order=1)
        self.category = Category.objects.create(board=self.board, name="Test Category", order=1)
        
        self.q1 = Question.objects.create(
            category=self.category,
            text="Question 1",
            answer="Answer 1",
            points=100,
            order=1
        )
        self.q2 = Question.objects.create(
            category=self.category,
            text="Question 2",
            answer="Answer 2",
            points=200,
            order=2
        )
        self.q3 = Question.objects.create(
            category=self.category,
            text="Question 3",
            answer="Answer 3",
            points=300,
            order=3
        )
        
        self.team = Team.objects.create(game=self.game, name="Test Team", color="#FF0000")
        self.player = Player.objects.create(team=self.team, name="Test Player")
    
    def test_score_with_default_points(self):
        """Test score calculation when using question's default points."""
        # Answer with default points (points=None)
        PlayerAnswer.objects.create(
            player=self.player,
            question=self.q1,
            is_correct=True,
            points=None
        )
        
        # Score should be question's points (100)
        self.assertEqual(self.player.score, 100)
    
    def test_score_with_custom_points(self):
        """Test score calculation when using custom points."""
        # Answer with custom points
        PlayerAnswer.objects.create(
            player=self.player,
            question=self.q1,
            is_correct=True,
            points=150
        )
        
        # Score should be custom points (150)
        self.assertEqual(self.player.score, 150)
    
    def test_score_with_multiple_answers(self):
        """Test score calculation with multiple answers."""
        # Answer 1 with default points
        PlayerAnswer.objects.create(
            player=self.player,
            question=self.q1,
            is_correct=True,
            points=None
        )
        # Answer 2 with custom points
        PlayerAnswer.objects.create(
            player=self.player,
            question=self.q2,
            is_correct=True,
            points=250
        )
        # Answer 3 with default points
        PlayerAnswer.objects.create(
            player=self.player,
            question=self.q3,
            is_correct=False,
            points=None
        )
        
        # Score should be 100 + 250 + 300 = 650
        self.assertEqual(self.player.score, 650)
    
    def test_annotated_score_matches_property(self):
        """Test that annotated score matches the property score."""
        # Create some answers
        PlayerAnswer.objects.create(
            player=self.player,
            question=self.q1,
            is_correct=True,
            points=None
        )
        PlayerAnswer.objects.create(
            player=self.player,
            question=self.q2,
            is_correct=True,
            points=250
        )
        
        # Get player with annotated score
        annotated_player = Player.objects.filter(id=self.player.id).annotate(
            computed_score=Sum(
                Case(
                    When(answers__points__isnull=False, then='answers__points'),
                    default='answers__question__points',
                ),
                default=Value(0, output_field=IntegerField())
            )
        ).first()
        
        # Verify annotated score matches property
        self.assertEqual(annotated_player.computed_score, self.player.score)
        self.assertEqual(annotated_player.computed_score, 350)  # 100 + 250

