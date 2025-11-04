from .base import *
import os
from dotenv import load_dotenv
import dj_database_url

# 載入 .env 檔案
load_dotenv()

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

# 使用 DATABASE_URL 設定資料庫
DATABASES = {
    'default': dj_database_url.parse(
        os.getenv('DATABASE_URL'),
        conn_max_age=600  # 連線池:連線最多保持 600 秒(10分鐘)
    )
}

# 生產環境安全設定
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
