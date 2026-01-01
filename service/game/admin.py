from django.contrib import admin

from .models import Board, Category, Game, MediaFile, Player, PlayerAnswer, Question, Team


class BoardInline(admin.TabularInline):
    model = Board
    extra = 2
    max_num = 2


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 6
    max_num = 6
    fields = ("name", "description", "order")


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 5
    max_num = 5
    fields = ("text", "answer", "points", "flags", "order")


class TeamInline(admin.TabularInline):
    model = Team
    extra = 1


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("name", "mode", "created_at")
    list_filter = ("created_at", "mode")
    search_fields = ("name",)
    inlines = [BoardInline, TeamInline]


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("game", "name", "order")
    list_filter = ("game",)
    search_fields = ("name",)
    inlines = [CategoryInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "board", "order")
    list_filter = ("board__game", "board")
    search_fields = ("name", "description")
    fields = ("board", "name", "description", "order")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("category", "points", "order", "text", "flags_display", "has_slides")
    list_filter = ("category__board__game", "category__board", "category")
    search_fields = ("text", "answer")

    def flags_display(self, obj):
        return ", ".join(obj.flags) if obj.flags else ""

    flags_display.short_description = "Flags"

    def has_slides(self, obj):
        return bool(obj.slides)

    has_slides.boolean = True
    has_slides.short_description = "Has Slides"


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 1


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "game", "total_score", "created_at")
    list_filter = ("game",)
    search_fields = ("name",)
    inlines = [PlayerInline]


class PlayerAnswerInline(admin.TabularInline):
    model = PlayerAnswer
    readonly_fields = ("player", "question", "is_correct", "points")
    extra = 0


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "team", "score", "created_at")
    list_filter = ("team__game", "team")
    search_fields = ("name",)
    inlines = [PlayerAnswerInline]


@admin.register(PlayerAnswer)
class PlayerAnswerAdmin(admin.ModelAdmin):
    list_display = ("player", "question", "is_correct", "answered_at")
    list_filter = ("is_correct", "player__team__game", "player__team", "player")
    search_fields = ("player__name", "question__text")


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "file_size_display", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("original_filename",)
    fields = ("file", "original_filename", "file_size", "uploaded_at")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("file", "original_filename", "file_size", "uploaded_at")
        return ("original_filename", "file_size", "uploaded_at")

    def save_model(self, request, obj, form, change):
        if not change:
            if obj.file:
                obj.original_filename = obj.file.name
                obj.file_size = obj.file.size
        super().save_model(request, obj, form, change)

    def file_size_display(self, obj):
        size_bytes = obj.file_size
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    file_size_display.short_description = "Size"
