"""
ASGI config for config project.

支援 HTTP 和 WebSocket 協定
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# 必須先初始化 Django
django_asgi_app = get_asgi_application()

# 導入 WebSocket 路由（Django 初始化後才能導入）
from apps.house.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP 請求：使用標準 Django ASGI 處理
    'http': django_asgi_app,

    # WebSocket 請求：使用 Channels 處理
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
