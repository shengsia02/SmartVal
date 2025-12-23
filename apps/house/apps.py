from django.apps import AppConfig


class HouseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.house'

    def ready(self):
        """
        當 Django 應用程式啟動時執行

        在這裡導入 signals 模組，讓 Signal 自動註冊
        """
        from . import signals  # noqa: F401
