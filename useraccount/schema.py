from ninja import Schema, ModelSchema
from pydantic import EmailStr
from typing import List
from .models import User, UserProfile, FriendRequest

class UserRegisterRequestSchema(Schema):
    email: EmailStr
    password: str
    confirm_password: str

class UserDetailSchema(ModelSchema):
    class Meta:
        model = User
        fields = ['id', 'username']

class UserProfileDetailSchema(ModelSchema):
    user: UserDetailSchema
    class Meta:
        model = UserProfile
        fields = "__all__"

class ErrorSchema(Schema):
    message: str

class FriendRequestSchema(ModelSchema):
    class Meta:
        model = FriendRequest
        fields=['id', 'sender', 'receiver', 'status']

class MeResponseSchema(Schema):
    profile: UserProfileDetailSchema
    friends: List[UserDetailSchema] = []
    pending_requests: List[FriendRequestSchema] = []
    friends_count: int

class UserDashboardResponseSchema(Schema):
    username:str
    total_game_played:int = 0
    total_game_win:int = 0
    total_game_loss:int = 0
    total_game_draw:int = 0