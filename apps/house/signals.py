"""
Django Signal 處理 - 房屋資料變更時的自動處理

使用 Signal 的好處：
1. 程式碼解耦：View 只管核心邏輯，通知由 Signal 處理
2. 不會遺漏：任何地方修改 House 都會觸發
3. 集中管理：所有「資料變更後要做的事」都在這裡
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models.house import House


def notify_house_update(action: str, message: str):
    """
    發送 WebSocket 通知給所有連線的客戶端

    Args:
        action: 'create', 'update', 'delete'
        message: 顯示給使用者的訊息
    """
    channel_layer = get_channel_layer()

    # 發送訊息到 'house_updates' 群組
    # async_to_sync 讓我們可以在同步程式碼中呼叫非同步函數
    async_to_sync(channel_layer.group_send)(
        'house_updates',  # 群組名稱，要與 Consumer 中的一致
        {
            'type': 'house_update',  # 對應 Consumer 中的方法名稱
            'action': action,
            'message': message,
        }
    )

    print(f"[Signal] 已發送 WebSocket 通知: {action} - {message}")


@receiver(post_save, sender=House)
def on_house_saved(sender, instance, created, **kwargs):
    """
    House 儲存後觸發（新增或更新）

    Args:
        sender: 發送信號的 Model（House）
        instance: 被儲存的 House 實例
        created: True 表示新增，False 表示更新
    """
    # 1. 清除快取
    cache.delete('api_house_list')
    print(f"[Signal] 已清除快取: api_house_list")

    # 2. 發送 WebSocket 通知
    if created:
        notify_house_update('create', f'新屋上架：{instance.title}')
    else:
        notify_house_update('update', f'房屋已更新：{instance.title}')


@receiver(post_delete, sender=House)
def on_house_deleted(sender, instance, **kwargs):
    """
    House 刪除後觸發

    Args:
        sender: 發送信號的 Model（House）
        instance: 被刪除的 House 實例
    """
    # 1. 清除快取
    cache.delete('api_house_list')
    print(f"[Signal] 已清除快取: api_house_list")

    # 2. 發送 WebSocket 通知
    notify_house_update('delete', f'房屋已下架：{instance.title}')
