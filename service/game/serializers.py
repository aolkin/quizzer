from rest_framework import serializers
from .models import Game, Board, Category, Player, Question, Team


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
