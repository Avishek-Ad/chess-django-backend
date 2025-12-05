from django.urls import re_path
from .consumers import ChessConsumer, MatchMakingConsumer

websocket_urlpatterns = [
    re_path(r'ws/chess/(?P<game_id>[0-9a-f-]+)/$', ChessConsumer.as_asgi()),
    re_path(r'ws/find-game/', MatchMakingConsumer.as_asgi()),
]
