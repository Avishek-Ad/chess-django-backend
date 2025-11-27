from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from useraccount.api import user_router
from game.api import game_router

# for custom return
from ninja_extra import api_controller, route
from ninja_jwt.controller import TokenObtainPairController, TokenVerificationController
from ninja_jwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from ninja import Schema
from django.http import HttpRequest
from ninja.errors import HttpError
from pydantic import EmailStr

class TokenPairSchema(Schema):
    email:EmailStr
    password:str

@api_controller('token', tags=['Auth'])
class CustomTokenController(TokenObtainPairController, TokenVerificationController):
    
    @route.post('/pair/')
    def obtain_token(self, request:HttpRequest, data:TokenPairSchema):
        user = authenticate(email=data.email, password=data.password)
        if user is None:
            raise HttpError(401, "Invalid credentials")
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        return {
            "id":user.id,
            "access":str(access),
            "refresh":str(refresh)
        }

api = NinjaExtraAPI()
api.register_controllers(CustomTokenController)
api.add_router("", user_router)
api.add_router("/chess/", game_router)

@api.get('/health/')
def status(request):
    print(request)
    return {'message':'api currently online'}