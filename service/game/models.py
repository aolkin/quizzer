from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, Case, When, Value, IntegerField
from colorfield.fields import ColorField


def get_score_annotation():
    """
    Returns the annotation expression for computing player scores on a Player queryset.

    This can be used in Player querysets to annotate scores efficiently.
    For each answer, uses answer.points if not null, otherwise question.points.
    """
    return Sum(
        Case(
            When(answers__points__isnull=False, then="answers__points"),
            default="answers__question__points",
        ),
        default=Value(0, output_field=IntegerField()),
    )


class Game(models.Model):
    GAME_MODES = [
        ("jeopardy", "Jeopardy"),
    ]

    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    mode = models.CharField(max_length=20, choices=GAME_MODES, default="jeopardy")
    points_term = models.CharField(max_length=50, default="points")

    def __str__(self):
        return self.name


class Board(models.Model):
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="boards")
    name = models.CharField(max_length=200, blank=True)
    order = models.SmallIntegerField()

    class Meta:
        ordering = ["game", "order"]
        unique_together = ["game", "order"]

    def __str__(self):
        return f"{self.game.name} - Board {self.order}: {self.name}"


class Category(models.Model):
    board = models.ForeignKey(Board, on_delete=models.PROTECT, related_name="categories")
    name = models.CharField(max_length=200)
    order = models.SmallIntegerField()

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "categories"
        unique_together = ["board", "order"]

    def __str__(self):
        return f"{self.board} - {self.name}"


class Question(models.Model):
    QUESTION_TYPES = [
        ("text", "Text Only"),
        ("image", "Image"),
        ("video", "Video"),
        ("audio", "Audio"),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="questions")
    flags = models.JSONField(default=list)
    type = models.CharField(max_length=5, choices=QUESTION_TYPES, default="text")
    text = models.TextField()
    answer = models.TextField()
    points = models.IntegerField(validators=[MinValueValidator(0)])
    answered = models.BooleanField(default=False)
    order = models.PositiveIntegerField(blank=True, null=True)
    media_url = models.URLField(blank=True, null=True)
    media_answer_url = models.URLField(blank=True, null=True)
    state_version = models.IntegerField(default=0)

    class Meta:
        ordering = ["category", "order", "points"]
        unique_together = ["category", "order"]

    def __str__(self):
        return f"{self.category.name} - {self.points}"


class Team(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=200)
    color = ColorField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["game", "name"]

    def __str__(self):
        return f"{self.game.name} - {self.name}"

    @property
    def total_score(self):
        return sum(player.score for player in self.players.all())


class PlayerQuerySet(models.QuerySet):
    def with_scores(self):
        """
        Annotate players with computed scores to avoid N+1 queries.

        Uses database aggregation to compute scores efficiently instead of the
        Player.score property which triggers a query for each player.

        For each answer, uses answer.points if not null, otherwise question.points.
        """
        return self.annotate(computed_score=get_score_annotation())


class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=200)
    buzzer = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    score_version = models.IntegerField(default=0)

    objects = PlayerQuerySet.as_manager()

    @property
    def score(self):
        return sum(
            answer.points if answer.points is not None else answer.question.points
            for answer in self.answers.all()
        )

    class Meta:
        unique_together = ["team", "name"]

    def __str__(self):
        return f"{self.team.name} - {self.name}"


class PlayerAnswer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="player_answers")
    is_correct = models.BooleanField()
    points = models.IntegerField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["player", "question"]

    def __str__(self):
        status = "Correct" if self.is_correct else "Incorrect"
        return f"{self.player.name} - {self.question} - {status}"
