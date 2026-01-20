from rest_framework.views import APIView
from rest_framework.response import Response
from .redis_utils import redis_client as r
from .models import ChessGame

class CreateGame(APIView):
    def post(self, request):
        play_as = request.data.get('play_as', 'white')
        if play_as.strip().lower() == "white":
            new_game = ChessGame.objects.create(player_white=request.user)
        else:
            new_game = ChessGame.objects.create(player_black=request.user)
        
        return Response({'gameid':new_game.id}, status=201)

create_game = CreateGame.as_view()

class JoinGame(APIView):
    def post(self, request, gameid):
        try:
            game = ChessGame.objects.get(id=gameid, status='waiting')
            if game.player_black is not None and game.player_white is not None:
                return Response({'message': "Game is already Full"}, status=400)
            if game.player_white == request.user or game.player_black == request.user:
                return Response({'message': "Your are already in the game"}, status=400)
            if game.player_white is not None:
                game.player_black = request.user
            else:
                game.player_white = request.user
            game.status = "active"
            game.save()
            return Response({
                'message':"You joined successfully",
                'gameid':game.id
            })
        except ChessGame.DoesNotExist:
            return Response({'message':'Game doesnot exists'}, status=404)

join_game = JoinGame.as_view()

class GameStatus(APIView):
    def get(self, request, gameid):
        try:
            game = ChessGame.objects.get(id=gameid)
            return Response({"status":game.status})
        except ChessGame.DoesNotExist:
            return Response({"message":"Game Not Found"}, status=404)

game_status = GameStatus.as_view()

class PlayerSide(APIView):
    def get(self, request, gameid):
        try:
            game = ChessGame.objects.get(id=gameid)
            if game.player_white == request.user:
                return Response({"orientation":"white", "white":game.player_white.username, "black":game.player_black.username})
            elif game.player_black == request.user:
                return Response({"orientation":"black", "white":game.player_white.username, "black":game.player_black.username})
            return Response({"message":"invalid request"}, status=400)
        except ChessGame.DoesNotExist:
            return Response({"message":"Game Not Found"}, status=404)

player_side = PlayerSide.as_view()

class JoinARandomGame(APIView):
    def post(self, request):
        user = request.user
        if str(user.id) in r.lrange("matchmaking_queue", 0, -1):
            return Response({'message': "Already waiting for Match", 'success':True})
        
        r.lpush("matchmaking_queue", user.id)
        return Response({'message': "Waiting for Match", 'success':True})
    
join_a_random_game = JoinARandomGame.as_view()

class QuitWaitingForRandomMatch(APIView):
    def post(self, request):
        user = request.user
        r.lrem("matchmaking_queue", 0, user.id)
        return Response({"message":"Removed successfully"})
    
quit_waiting_for_random_match = QuitWaitingForRandomMatch.as_view()
