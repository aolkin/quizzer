"""
URL configuration for quizzer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from game.views import get_board, get_game, record_answer, toggle_question

urlpatterns = [
    path("api/game/<int:game_id>/", get_game),
    path("api/board/<int:board_id>/", get_board),
    path("api/board/<int:board_id>/answers/", record_answer),
    path("api/question/<int:question_id>/", toggle_question),
    path("admin/", admin.site.urls),
]
