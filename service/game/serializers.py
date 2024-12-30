from rest_framework import serializers
from .models import Game, Board, Category, Question


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'type', 'text', 'answer', 'points', 'order', 'media_url']


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
