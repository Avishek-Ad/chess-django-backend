from django.urls import path
from . import views

urlpatterns = [
    path("create-game/", views.create_game, name="create-game"),
    path("join-game/<uuid:gameid>/", views.join_game, name="join-game"),
    path("game-status/<uuid:gameid>/", views.game_status, name="game-status"),
    path("player-side/<uuid:gameid>/", views.player_side, name="player-side"),
    path("join-a-random-game/", views.join_a_random_game, name="join-a-random-game"),
    path("quit-waiting-for-a-random-game/", views.quit_waiting_for_random_match, name="quit-waiting-for-a-random-game")
]
