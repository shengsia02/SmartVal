# 讓 Django 啟動時自動載入 Celery（如果有安裝的話）
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery 沒有安裝，跳過
    pass

