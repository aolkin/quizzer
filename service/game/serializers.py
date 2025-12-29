from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import Game, Board, Category, Player, Question, Team, PlayerAnswer


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "type",
            "text",
            "answer",
            "points",
            "special",
            "order",
            "media_url",
            "answered",
        ]


class CategorySerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Category
        fields = ["id", "name", "order", "questions"]


class BoardSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True)

    class Meta:
        model = Board
        fields = ["id", "name", "order", "categories"]


class BoardMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ["id", "name", "order"]


class PlayerSerializer(serializers.ModelSerializer):
    score = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ["id", "name", "buzzer", "score"]

    def get_score(self, obj):
        """
        Get score from annotated computed_score if available, otherwise fall back to property.
        This prevents N+1 queries when players are annotated with scores in the view.
        """
        if hasattr(obj, "computed_score"):
            return obj.computed_score
        return obj.score


class TeamSerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True)

    class Meta:
        model = Team
        fields = ["id", "name", "color", "players"]


class GameSerializer(serializers.ModelSerializer):
    boards = BoardMetaSerializer(many=True)
    teams = TeamSerializer(many=True)

    class Meta:
        model = Game
        fields = ["id", "name", "mode", "boards", "teams"]


# API request serializers for mutations
class RecordAnswerRequestSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    is_correct = serializers.BooleanField()
    points = serializers.IntegerField(required=False, allow_null=True)


class ToggleQuestionRequestSerializer(serializers.Serializer):
    answered = serializers.BooleanField()


# Export serializers
class QuestionExportSerializer(serializers.Serializer):
    """Serializer for exporting questions, omitting null and default values."""

    text = serializers.CharField()
    answer = serializers.CharField()
    points = serializers.IntegerField()
    type = serializers.CharField(required=False)
    media_url = serializers.URLField(required=False)
    special = serializers.BooleanField(required=False)

    def to_representation(self, instance):
        """Custom representation to omit null fields and defaults."""
        data = {
            "text": instance.text,
            "answer": instance.answer,
            "points": instance.points,
        }
        # Only include type if it's not the default "text"
        if instance.type and instance.type != "text":
            data["type"] = instance.type
        # Only include media_url if it's not null/empty
        if instance.media_url:
            data["media_url"] = instance.media_url
        # Only include special if it's True
        if instance.special:
            data["special"] = instance.special
        return data


class CategoryExportSerializer(serializers.Serializer):
    """Serializer for exporting categories, omitting order field."""

    name = serializers.CharField()
    questions = QuestionExportSerializer(many=True)


class BoardExportSerializer(serializers.Serializer):
    """Serializer for exporting boards, omitting order field."""

    name = serializers.CharField()
    categories = CategoryExportSerializer(many=True)


class PlayerAnswerExportSerializer(serializers.Serializer):
    """Serializer for exporting player answers in full mode."""

    question_index = serializers.IntegerField()
    is_correct = serializers.BooleanField()
    points = serializers.IntegerField(required=False)
    answered_at = serializers.DateTimeField()

    def to_representation(self, instance):
        """Custom representation to omit null points."""
        data = {
            "question_index": instance.question_index,
            "is_correct": instance.is_correct,
            "answered_at": instance.answered_at.isoformat(),
        }
        if instance.points is not None:
            data["points"] = instance.points
        return data


class PlayerExportSerializer(serializers.Serializer):
    """Serializer for exporting players in full mode."""

    name = serializers.CharField()
    buzzer = serializers.IntegerField(required=False, allow_null=True)
    answers = PlayerAnswerExportSerializer(many=True, required=False)

    def to_representation(self, instance):
        """Custom representation to omit null buzzer and empty answers."""
        data = {"name": instance.name}
        if instance.buzzer is not None:
            data["buzzer"] = instance.buzzer
        if hasattr(instance, "answers_export") and instance.answers_export:
            # answers_export is already a list of dicts with the right format
            data["answers"] = instance.answers_export
        return data


class TeamExportSerializer(serializers.Serializer):
    """Serializer for exporting teams in full mode."""

    name = serializers.CharField()
    color = serializers.CharField()
    players = PlayerExportSerializer(many=True)


class GameExportSerializer(serializers.Serializer):
    """Serializer for exporting complete game data."""

    export_version = serializers.CharField(default="1.0")
    mode = serializers.CharField()
    exported_at = serializers.DateTimeField()
    game = serializers.SerializerMethodField()

    def get_game(self, obj):
        """Build the game structure for export."""
        game_data = {
            "name": obj.name,
            "mode": obj.mode,
            "boards": BoardExportSerializer(obj.boards.all(), many=True).data,
        }

        # Add metadata
        game_data["metadata"] = {
            "original_game_id": obj.id,
            "created_at": obj.created_at.isoformat(),
        }

        # Include teams only in full mode
        export_mode = self.context.get("export_mode", "template")
        if export_mode == "full" and hasattr(obj, "teams"):
            teams_data = TeamExportSerializer(obj.teams.all(), many=True).data
            if teams_data:
                game_data["teams"] = teams_data

        return game_data


# Import serializers
class QuestionImportSerializer(serializers.Serializer):
    """Serializer for importing questions."""

    text = serializers.CharField()
    answer = serializers.CharField()
    points = serializers.IntegerField()
    type = serializers.CharField(default="text", required=False)
    media_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    special = serializers.BooleanField(default=False, required=False)


class CategoryImportSerializer(serializers.Serializer):
    """Serializer for importing categories."""

    name = serializers.CharField()
    questions = QuestionImportSerializer(many=True)


class BoardImportSerializer(serializers.Serializer):
    """Serializer for importing boards."""

    name = serializers.CharField()
    categories = CategoryImportSerializer(many=True)


class PlayerAnswerImportSerializer(serializers.Serializer):
    """Serializer for importing player answers."""

    question_index = serializers.IntegerField()
    is_correct = serializers.BooleanField()
    points = serializers.IntegerField(required=False, allow_null=True)
    answered_at = serializers.DateTimeField(required=False)


class PlayerImportSerializer(serializers.Serializer):
    """Serializer for importing players."""

    name = serializers.CharField()
    buzzer = serializers.IntegerField(required=False, allow_null=True)
    answers = PlayerAnswerImportSerializer(many=True, required=False)


class TeamImportSerializer(serializers.Serializer):
    """Serializer for importing teams."""

    name = serializers.CharField()
    color = serializers.CharField()
    players = PlayerImportSerializer(many=True)


class GameImportDataSerializer(serializers.Serializer):
    """Serializer for the game data within an import."""

    name = serializers.CharField()
    mode = serializers.CharField()
    boards = BoardImportSerializer(many=True)
    teams = TeamImportSerializer(many=True, required=False)
    metadata = serializers.DictField(required=False)


class GameImportSerializer(serializers.Serializer):
    """Serializer for importing complete game data."""

    export_version = serializers.CharField()
    mode = serializers.CharField()
    exported_at = serializers.DateTimeField(required=False)
    game = GameImportDataSerializer()

    def validate_export_version(self, value):
        """Validate that the export version is supported."""
        if value != "1.0":
            raise serializers.ValidationError(
                f"Unsupported export version: {value}. Only version 1.0 is supported."
            )
        return value

    def validate_mode(self, value):
        """Validate that the mode is either template or full."""
        if value not in ["template", "full"]:
            raise serializers.ValidationError(
                f"Invalid mode: {value}. Must be 'template' or 'full'."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create a new game from the import data."""
        game_data = validated_data["game"]
        import_mode = validated_data["mode"]

        # Create the game
        game = Game.objects.create(name=game_data["name"], mode=game_data["mode"])

        # Track created objects for the response
        boards_created = 0
        categories_created = 0
        questions_created = 0
        teams_created = 0
        players_created = 0
        answers_imported = 0

        # Create boards, categories, and questions
        question_id_map = {}  # Map question_index to Question objects
        question_index = 0

        for board_order, board_data in enumerate(game_data["boards"]):
            board = Board.objects.create(game=game, name=board_data["name"], order=board_order)
            boards_created += 1

            for category_order, category_data in enumerate(board_data["categories"]):
                category = Category.objects.create(
                    board=board, name=category_data["name"], order=category_order
                )
                categories_created += 1

                for question_order, question_data in enumerate(category_data["questions"]):
                    question = Question.objects.create(
                        category=category,
                        text=question_data["text"],
                        answer=question_data["answer"],
                        points=question_data["points"],
                        type=question_data.get("type", "text"),
                        media_url=question_data.get("media_url", None) or None,
                        special=question_data.get("special", False),
                        order=question_order,
                    )
                    question_id_map[question_index] = question
                    question_index += 1
                    questions_created += 1

        # Create teams and players if in full mode
        if import_mode == "full" and "teams" in game_data:
            for team_data in game_data["teams"]:
                team = Team.objects.create(
                    game=game, name=team_data["name"], color=team_data["color"]
                )
                teams_created += 1

                for player_data in team_data["players"]:
                    player = Player.objects.create(
                        team=team,
                        name=player_data["name"],
                        buzzer=player_data.get("buzzer"),
                    )
                    players_created += 1

                    # Import answers if present
                    if "answers" in player_data:
                        for answer_data in player_data["answers"]:
                            question_idx = answer_data["question_index"]
                            if question_idx in question_id_map:
                                question = question_id_map[question_idx]
                                PlayerAnswer.objects.create(
                                    player=player,
                                    question=question,
                                    is_correct=answer_data["is_correct"],
                                    points=answer_data.get("points"),
                                )
                                answers_imported += 1

        return {
            "game_id": game.id,
            "game_name": game.name,
            "boards_created": boards_created,
            "categories_created": categories_created,
            "questions_created": questions_created,
            "teams_created": teams_created,
            "players_created": players_created,
            "answers_imported": answers_imported,
            "import_mode": import_mode,
            "imported_at": timezone.now().isoformat(),
        }
