from rest_framework import serializers
from .models import Game, Board, Category, Player, Question, Team


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'type', 'text', 'answer', 'points', 'order', 'media_url', 'answered']


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
