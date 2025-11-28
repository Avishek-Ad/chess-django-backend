import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_core.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
# using custom middleware cause the custom on sucks or i didnot know how to use it
from game.middleware import TokenAuthMiddlewareStack

django_asgi_application = get_asgi_application()

from game import routing

application = ProtocolTypeRouter({
    "http": django_asgi_application,
    'websocket': TokenAuthMiddlewareStack(
            URLRouter(routing.websocket_urlpatterns)
    )
})

