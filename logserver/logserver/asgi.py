import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logserver.settings')
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
# from step 4
from channels.auth import AuthMiddlewareStack


from loggers.routings import websocket_urlpatterns  
application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
