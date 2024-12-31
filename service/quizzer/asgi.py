"""
ASGI config for quizzer project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

from game.consumers import GameConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzer.settings')

django_asgi_application = get_asgi_application()

application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_application,

    # WebSocket chat handler
    "websocket":
        URLRouter([
            path("ws/game/<int:board_id>/", GameConsumer.as_asgi()),
        ])
})
