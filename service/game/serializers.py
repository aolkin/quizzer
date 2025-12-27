from rest_framework import serializers
from .models import Game, Board, Category, Player, Question, Team


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'type', 'text', 'answer', 'points', 'special', 'order', 'media_url', 'answered']


class CategorySerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'order', 'questions']


class BoardSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True)

    class Meta:
        model = Board
        fields = ['id', 'name', 'order', 'categories']

class BoardMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ['id', 'name', 'order']

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'name', 'buzzer', 'score']

class TeamSerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'color', 'players']

class GameSerializer(serializers.ModelSerializer):
    boards = BoardMetaSerializer(many=True)
    teams = TeamSerializer(many=True)

    class Meta:
        model = Game
        fields = ['id', 'name', 'mode', 'boards', 'teams']


# API request/response serializers for mutations
class RecordAnswerRequestSerializer(serializers.Serializer):
    playerId = serializers.IntegerField()
    questionId = serializers.IntegerField()
    isCorrect = serializers.BooleanField()
    points = serializers.IntegerField(required=False, allow_null=True)


class RecordAnswerResponseSerializer(serializers.Serializer):
    playerId = serializers.IntegerField()
    score = serializers.IntegerField()
    version = serializers.IntegerField()


class ToggleQuestionRequestSerializer(serializers.Serializer):
    answered = serializers.BooleanField()


class ToggleQuestionResponseSerializer(serializers.Serializer):
    questionId = serializers.IntegerField()
    answered = serializers.BooleanField()
    version = serializers.IntegerField()
