from celery import shared_task
from .redis_utils import redis_client as r
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import ChessGame

channel_layer = get_channel_layer()

@shared_task
def matchmaking_task():
    queue = r.lrange("matchmaking_queue", 0, -1)  # peek at all users
    # check if queue has more than 2 users
    if len(queue) >= 2:
        user1 = r.rpop("matchmaking_queue") # they will be a string
        user2 = r.rpop("matchmaking_queue")

        # remove int conversion if later i used uuid --------------Reminder (wasted 3 hrs because i didnot set the status to active)
        game = ChessGame.objects.create(player_white_id=str(user1), player_black_id=str(user2), status="active")

        # sending match found message (well its just an event and it will send the message)
        print("USERS FOUND SENDING THE GAMEID")
        async_to_sync(channel_layer.group_send)(
            f"user-{user1}",
            {
                "type": "match_found",
                "gameid": f"{game.id}"
            }
        )
        async_to_sync(channel_layer.group_send)(
            f"user-{user2}",
            {
                "type": "match_found",
                "gameid": f"{game.id}"
            }
        )