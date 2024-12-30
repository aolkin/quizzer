from django.contrib import admin

from .models import Board, Category, Game, Player, PlayerAnswer, Question, Team


class BoardInline(admin.TabularInline):
    model = Board
    extra = 2
    max_num = 2


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 5
    max_num = 5


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 5
    max_num = 5


class TeamInline(admin.TabularInline):
    model = Team
    extra = 1


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'mode', 'created_at')
    list_filter = ('created_at', 'mode')
    search_fields = ('name',)
    inlines = [BoardInline, TeamInline]


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('game', 'name', 'order')
    list_filter = ('game',)
    search_fields = ('name',)
    inlines = [CategoryInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'board', 'order')
    list_filter = ('board__game', 'board')
    search_fields = ('name',)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('category', 'type', 'points', 'order', 'text')
    list_filter = ('category__board__game', 'category__board', 'category', 'type')
    search_fields = ('text', 'answer')

class PlayerInline(admin.TabularInline):
    model = Player
    extra = 1

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'total_score', 'created_at')
    list_filter = ('game',)
    search_fields = ('name',)
    inlines = [PlayerInline]


class PlayerAnswerInline(admin.TabularInline):
    model = PlayerAnswer
    readonly_fields = ('player', 'question', 'is_correct', 'points')
    extra = 0

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'score', 'created_at')
    list_filter = ('team__game', 'team')
    search_fields = ('name',)
    inlines = [PlayerAnswerInline]


@admin.register(PlayerAnswer)
class PlayerAnswerAdmin(admin.ModelAdmin):
    list_display = ('player', 'question', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'player__team__game', 'player__team', 'player')
    search_fields = ('player__name', 'question__text')
