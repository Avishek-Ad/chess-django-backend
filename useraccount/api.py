from ninja import Router
from .schema import *
from .models import User, UserProfile, FriendRequest
from ninja_jwt.authentication import JWTAuth
from django.db.models import Q
from game.models import ChessGame

user_router = Router()

# register
@user_router.post("/auth/register/", response={
    200: UserDetailSchema,
    400: ErrorSchema
    })
def user_registration(request, data:UserRegisterRequestSchema):
    print(data)
    email = data.email
    password = data.password
    confirm_password = data.confirm_password

    if not email or not password or not confirm_password:
        return 400, {'message': "Please provide required fields"}

    if password != confirm_password:
        return 400, {'message':"Passwords doesnot match"}
    
    if User.objects.filter(email=email).exists():
        return 400, {'message': "Email alerady exists"}

    user = User.objects.create_user(email=email, password=password)

    return user

@user_router.get("/auth/stats/", response=UserDashboardResponseSchema, auth=JWTAuth())
def dashboard_details(request):
    user = request.user
    # Games played as white, black, or both
    all_games_played = ChessGame.objects.filter(
        Q(player_white=user) | Q(player_black=user)
    )
    total_game_played = all_games_played.count()
    # Wins
    total_game_won = all_games_played.filter(winner=user).count()
    # Draws
    total_game_draw = all_games_played.filter(
        winner=None, status="finished"
    ).count()
    # Loss = played - win - draw
    total_game_loss = total_game_played - (total_game_won + total_game_draw)
    return {
        "username": user.username,
        "total_game_played": total_game_played,
        "total_game_win": total_game_won,
        "total_game_loss": total_game_loss,
        "total_game_draw": total_game_draw,
    }

# currently not using will add the friend option in the later version

# me
@user_router.get("/auth/me/", response=MeResponseSchema, auth=[JWTAuth()])
def me(request):
    userProfile = UserProfile.objects.get(user=request.user)
    friends = User.objects.filter(
            Q(sent_friend_requests__receiver=request.user, sent_friend_requests__status='accepted') |
            Q(received_friend_requests__sender=request.user, received_friend_requests__status='accepted')
        ).distinct()
    pending_requests = FriendRequest.objects.filter(receiver=request.user, status='pending')
    friends_count = friends.count()

    return {
        'profile':userProfile,
        'friends':friends,
        'pending_requests':pending_requests,
        'friends_count':friends_count
    }

# show other user's profile
@user_router.get("/auth/user/{id}", response={
    200: UserProfileDetailSchema,
    404: ErrorSchema
    })
def user_info(request, id):
    try:
        user = User.objects.get(id=id)
        userProfile = UserProfile.objects.get(user=user)
        return userProfile
    except User.DoesNotExist:
       return 404, {'message':'User doesnot exists'} 

# send friend request
@user_router.post("/send-friend-request/{otherid}", auth=JWTAuth())
def send_friend_request(request, otherid):
    user = request.user
    try:
        other_user = User.objects.get(id=id)
    except User.DoesNotExist:
        return 404, {'message':'User Not Found'}
    
    if user.id == other_user.id:
        return 400, {'message':'You cannot send friend request to yourself'}
   
    if FriendRequest.objects.filter(sender=user, receiver=other_user).exists():
        return 400, {'message':'you already sent a friend request'}
    
    FriendRequest.objects.create(sender=user, receiver=other_user)
    return 201, {'message':'Friend Request sent successfully'}

# accept friend request
@user_router.post("/accept-friend-request/{requestid}", auth=JWTAuth())
def accept_friend_request(request, requestid):
    try:
        friend_request = FriendRequest.objects.get(id=requestid, receiver=request.user)
        if friend_request.status == 'accepted':
            return 400, {'message':'Friend Request is already accepted'}
        
        # i will be deleting rejected request directly
        # if friend_request.status == 'rejected':
        #     return 400, {'message':'Friend Request is already rejected'}
        
        friend_request.status = 'accepted'
        friend_request.save()
        return 200, {'message':'Friend request accepted'}
    except FriendRequest.DoesNotExist:
        return 404, {'message':'Friend request doesnot exists'}

# reject friend request
@user_router.post("/reject-friend-request/{requestid}", auth=JWTAuth())
def reject_friend_request(request, requestid):
    try:
        friend_request = FriendRequest.objects.get(id=requestid, receiver=request.user)

        # i will be deleting rejected request directly
        # if friend_request.status == 'rejected':
        #     return 400, {'message':'Friend Request is already rejected'}
        if friend_request.status == 'accepted':
            return 400, {'message':'Friend Request is already accepted'}
        # friend_request.status = 'rejected'
        
        friend_request.delete()
        return 200, {'message':'Friend request rejected'}
    except FriendRequest.DoesNotExist:
        return 404, {'message':'Friend request doesnot exists'}

#un-friend
@user_router.post("/un-friend/{otherid}", auth=JWTAuth())
def un_friend(request, otherid):
    try:
        other_user = User.objects.get(id=otherid)
        friend_request = FriendRequest.objects.filter(sender__in=[request.user, other_user], receiver__in=[request.user, other_user], status='accepted')
        if not friend_request.exists():
            return 404, {'message':'Friendship doesnot exists'}
        friend_request.delete()
        return 200, {'message': "Successfully Unfriended"}
    except User.DoesNotExist:
        return 404, {'message':'User Not Found'}

# list friends
# @router.post()