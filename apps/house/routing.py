"""
WebSocket URL 路由設定

類似 urls.py，但用於 WebSocket
"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # ws://127.0.0.1:8000/ws/books/
    path('ws/houses/', consumers.HouseListConsumer.as_asgi()),
    # 新增以下兩行
    path('ws/agents/', consumers.AgentListConsumer.as_asgi()),
    path('ws/buyers/', consumers.BuyerListConsumer.as_asgi()),
]
