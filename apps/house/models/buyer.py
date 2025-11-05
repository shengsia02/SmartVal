from django.db import models

class Buyer(models.Model):
    """買家 (已成交客戶名冊)"""

    # --- 核心聯絡資訊 ---
    name = models.CharField(max_length=100, verbose_name='買家姓名')
    phone = models.CharField(max_length=20, verbose_name='聯絡電話', blank=True)
    email = models.EmailField(max_length=100, verbose_name='電子郵件', blank=True)
    
    # 【已移除】 occup, birth_date, nationality 欄位

    class Meta:
        verbose_name = '買家'
        verbose_name_plural = '買家'

    def __str__(self):
        return self.name