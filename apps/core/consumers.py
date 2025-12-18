# apps/core/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 取得當前登入的使用者
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
        else:
            # 建立專屬群組名稱，例如 "user_1"
            self.group_name = f"user_{self.user.id}"

            # 加入群組
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        # 離開群組
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # 接收來自 Celery 或其他地方的推播訊息
    async def task_message(self, event):
        # event 是 Celery 送過來的字典
        message = event['message']
        status = event['status']

        # 發送給前端 WebSocket
        await self.send(text_data=json.dumps({
            'status': status,
            'message': message
        }))