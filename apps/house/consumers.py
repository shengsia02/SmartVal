"""
WebSocket Consumer - 房屋列表即時更新

Consumer 就像是 WebSocket 版本的 View：
- View 處理 HTTP 請求
- Consumer 處理 WebSocket 連線
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class HouseListConsumer(AsyncWebsocketConsumer):
    """
    房屋列表 WebSocket Consumer

    功能：
    1. 客戶端連線時，加入 'house_updates' 群組
    2. 收到群組訊息時，轉發給客戶端
    3. 客戶端斷線時，從群組移除
    """

    # 群組名稱（所有連線的客戶端都會加入這個群組）
    GROUP_NAME = 'house_updates'

    async def connect(self):
        """
        WebSocket 連線建立時觸發

        相當於 View 的 GET 請求
        """
        # 將此連線加入群組（像是加入聊天室）
        await self.channel_layer.group_add(
            self.GROUP_NAME,
            self.channel_name  # 每個連線都有唯一的 channel_name
        )

        # 接受連線（很重要！不呼叫就會拒絕連線）
        await self.accept()

        print(f"[WebSocket] 新連線加入: {self.channel_name}")

    async def disconnect(self, close_code):
        """
        WebSocket 連線斷開時觸發

        close_code: 斷線原因代碼
        """
        # 從群組移除此連線
        await self.channel_layer.group_discard(
            self.GROUP_NAME,
            self.channel_name
        )

        print(f"[WebSocket] 連線離開: {self.channel_name}, code={close_code}")

    async def receive(self, text_data):
        """
        收到客戶端傳來的訊息時觸發

        這個範例中客戶端不需要發送訊息，
        但如果需要（例如聊天功能），可以在這裡處理
        """
        data = json.loads(text_data)
        print(f"[WebSocket] 收到客戶端訊息: {data}")

    async def house_update(self, event):
        """
        處理房屋更新事件

        這個方法名稱對應 group_send 中的 'type': 'house_update'
        當有人呼叫 group_send 時，這個方法會被觸發
        """
        # 將訊息發送給客戶端（瀏覽器）
        await self.send(text_data=json.dumps({
            'type': 'house_update',
            'action': event['action'],    # 'create', 'update', 'delete'
            'message': event['message'],  # 顯示給使用者的訊息
        }))

        print(f"[WebSocket] 已發送給客戶端: {event['action']}")

# 【新增】AgentListConsumer
class AgentListConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = 'agent_updates'

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    # 對應 Signal 中的 event_type='agent_update'
    async def agent_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'agent_update',
            'action': event['action'],
            'message': event['message'],
        }))

# 【新增】BuyerListConsumer
class BuyerListConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = 'buyer_updates'

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    # 對應 Signal 中的 event_type='buyer_update'
    async def buyer_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'buyer_update',
            'action': event['action'],
            'message': event['message'],
        }))