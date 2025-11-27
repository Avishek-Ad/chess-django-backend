from ninja import Schema, ModelSchema
from .models import ChessGame
from useraccount.schema import UserDetailSchema
from typing import List
from uuid import UUID
from typing import Optional

class CreateGameResponseSchema(Schema):
    gameid:UUID

class CreateGameRequestSchema(Schema):
    play_as:str

class JoinGameResponseSchema(Schema):
    message:str
    gameid:UUID

class ErrorSchema(Schema):
    message:str

class GameDetailSchema(ModelSchema):
    player_white: Optional[UserDetailSchema]
    player_black:Optional[UserDetailSchema]
    winner:Optional[UserDetailSchema]
    class Meta:
        model=ChessGame
        fields=['player_white', 'player_black', 'board_fen', 'move_history', 'status', 'winner']

class MyGamesDetailschema(Schema):
    ongoing: List[GameDetailSchema] = []
    finished: List[GameDetailSchema] = []
    waiting: List[GameDetailSchema] = []