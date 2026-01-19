from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework.generics import CreateAPIView, RetrieveAPIView
from .serilizers import UserRegistrationSerializer, CustomTokenObtainPairSerilizer
from game.models import ChessGame

class UserCreateView(CreateAPIView):
    serializer_class = UserRegistrationSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerilizer

class UserDashboardStatsView(RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        user = request.user
        username = user.username
        total_game_played = ChessGame.objects.total_game_played(user=user)
        total_game_won = ChessGame.objects.total_game_won(user=user)
        total_game_loss = ChessGame.objects.total_game_loss(user=user)
        total_game_draw = ChessGame.objects.total_game_draw(user=user)
        return Response({
        "username": username,
        "total_game_played": total_game_played,
        "total_game_win": total_game_won,
        "total_game_loss": total_game_loss,
        "total_game_draw": total_game_draw,
    })