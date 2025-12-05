from ninja import Router
from ninja_jwt.authentication import JWTAuth
from .schema import *
from .models import ChessGame
from uuid import UUID
from .redis_utils import redis_client as r

game_router = Router()

# create a game returns gameid so other can join
@game_router.post('create-game/', response=CreateGameResponseSchema, auth=JWTAuth())
def create_game(request, data:CreateGameRequestSchema):
    play_as = data.play_as
    if play_as.strip().lower() == "white":
        new_game = ChessGame.objects.create(player_white=request.user)
    else:
        new_game = ChessGame.objects.create(player_black=request.user)
    
    return {'gameid':new_game.id}

# join a game
@game_router.post('join-game/{gameid}/', response={
    200: JoinGameResponseSchema,
    404: ErrorSchema,
    400: ErrorSchema
    }, auth=JWTAuth())
def join_game(request, gameid:UUID):
    print("inside join", gameid)
    try:
        game = ChessGame.objects.get(id=gameid, status='waiting')
        if game.player_black is not None and game.player_white is not None:
            return 400, {'message': "Game is already Full"}
        if game.player_white == request.user or game.player_black == request.user:
            return 400, {'message': "Your are already in the game"}
        if game.player_white is not None:
            game.player_black = request.user
        else:
            game.player_white = request.user
        game.status = "active"
        game.save()
        return {
            'message':"You joined successfully",
            'gameid':game.id
        }
    except ChessGame.DoesNotExist:
        return 404, {'message':'Game doesnot exists'}

@game_router.get("game-status/{gameid}/", auth=JWTAuth())
def game_status(request, gameid):
    try:
        game = ChessGame.objects.get(id=gameid)
        return {"status":game.status}
    except ChessGame.DoesNotExist:
        return 404, {"message":"Game Not Found"}
    
@game_router.get("player-side/{gameid}/", auth=JWTAuth())
def player_side(request, gameid):
    try:
        game = ChessGame.objects.get(id=gameid)
        if game.player_white == request.user:
            return {"orientation":"white", "white":game.player_white.username, "black":game.player_black.username}
        elif game.player_black == request.user:
            return {"orientation":"black", "white":game.player_white.username, "black":game.player_black.username}
        return {"message":"invalid request"}
    except ChessGame.DoesNotExist:
        return 404, {"message":"Game Not Found"}
    
@game_router.post("join-a-random-game/", auth=JWTAuth())
def join_a_random_game(request):
    user = request.user
    # check if user is already in the queue
    print("Users Waiting", r.lrange("matchmaking_queue", 0, -1))
    if str(user.id) in r.lrange("matchmaking_queue", 0, -1):
        return {'message': "Already waiting for Match", 'success':True}
    # now push the user to radis
    r.lpush("matchmaking_queue", user.id)
    print("user pushed to radis queue")
    return {'message': "Waiting for Match", 'success':True}

@game_router.post("quit-waiting-for-a-random-game/", auth=JWTAuth())
def quit_waiting_for_random_match(request):
    print("Quit waiting for a random game")
    print(r.lrange("matchmaking_queue", 0, -1))
    user = request.user
    r.lrem("matchmaking_queue", 0, user.id)
    return {"message":"Removed successfully"}

# not used currently
# list all my games
@game_router.get("my-games/", response=MyGamesDetailschema, auth=JWTAuth())
def my_games(request):
    waiting_white = request.user.games_as_white.filter(status='waiting')
    waiting_black = request.user.games_as_black.filter(status='waiting')

    active_white = request.user.games_as_white.filter(status='active')
    active_black = request.user.games_as_black.filter(status='active')

    finished_white = request.user.games_as_white.filter(status='finished')
    finished_black = request.user.games_as_black.filter(status='finished')

    waiting = waiting_white.union(waiting_black)
    active = active_white.union(active_black)
    finished = finished_white.union(finished_black)
    return {
        'waiting':list(waiting),
        'active':list(active),
        'finished':list(finished)
    }


#get a game details
@game_router.get("game/{gameid}/", response={
    200: GameDetailSchema,
    404: ErrorSchema,
    401: ErrorSchema
    }, auth=JWTAuth())
def game_detail(request, gameid:UUID):
    try:
        game = ChessGame.objects.get(id=gameid)
        if not game.player_black == request.user and not game.player_white == request.user:
            return 401, {'message':"Not a player of this game"}
        return game
    except ChessGame.DoesNotExist:
        return 404, {'message':'Game doesnot exists'}


# not used currently
# resign a game
@game_router.post("game/{gameid}/resign/", auth=JWTAuth())
def resign_game(request, gameid:UUID):
    try:
        game = ChessGame.objects.get(id=gameid, status="active")
        if not game.player_black == request.user and not game.player_white == request.user:
            return 401, {'message':"Not a player of this game"}
        game.status = 'finished'
        if game.player_black == request.user:
            game.winner = game.player_white
        else:
            game.winner = game.player_black
        game.save()
        return 200, {'message':'Game resigned successfully'}
    except ChessGame.DoesNotExist:
        return 404, {'message':'Game doesnot exists'}
    
# the chess room creater is tired of waiting for other player and clicks on quit
@game_router.post("/i-am-bored/{gameid}/", auth=JWTAuth())
def i_am_bored(request, gameid:UUID):
    try:
        game = ChessGame.objects.get(id=gameid, status="waiting")
        if not game.player_black == request.user and not game.player_white == request.user:
            return 401, {'message':"Not a player of this game"}
        game.delete()
        return 200, {'message':'Its frustrating to wait for long.'}
    except ChessGame.DoesNotExist:
        return 404, {'message':'Game doesnot exists'}