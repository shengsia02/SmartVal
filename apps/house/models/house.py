from django.db import models
from datetime import date
from .agent import Agent
from .buyer import Buyer

class House(models.Model):
    """整合後的房屋完整資訊"""
    
    # ===== 基本資訊 =====
    address = models.CharField(
        max_length=200, 
        verbose_name='地址'
    )
    house_type = models.CharField(
        max_length=100, 
        verbose_name='房屋類型'
    )
    total_price = models.IntegerField(
        verbose_name='總價格（萬元）'
    )
    
    # ===== 關聯資訊 =====
    buyers = models.ForeignKey(
        Buyer, 
        on_delete=models.CASCADE,
        related_name='houses_bought', 
        verbose_name='買家', 
        null=True, blank=True
    )
    agent = models.ForeignKey(
        Agent, 
        on_delete=models.CASCADE, 
        related_name='houses_sold', 
        verbose_name='仲介', 
        null=True, blank=True
    )
    
    # ===== 位置資訊（原 HouseDetail）=====
    city = models.CharField(
        max_length=200, 
        verbose_name='縣市',
        null=True, blank=True
    )
    town = models.CharField(
        max_length=200, 
        verbose_name='行政區',
        null=True, blank=True
    )
    
    # ===== 房屋詳細資訊（原 HouseDetail）=====
    house_age = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='屋齡（年）',
        null=True, blank=True
    )
    floor_area = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='建坪',
        null=True, blank=True
    )
    land_area = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='地坪',
        null=True, blank=True
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='建坪單價（萬元/坪）',
        null=True, blank=True
    )
    floor_number = models.IntegerField(
        verbose_name='所在層數',
        null=True, blank=True
    )
    total_floors = models.IntegerField(
        verbose_name='地上總層數',
        null=True, blank=True
    )
    room_count = models.IntegerField(
        verbose_name='房間數',
        null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=20, 
        decimal_places=12, 
        verbose_name='經度',
        null=True, blank=True
    )
    latitude = models.DecimalField(
        max_digits=20, 
        decimal_places=12, 
        verbose_name='緯度',
        null=True, blank=True
    )
    sold_time = models.DateField(
        verbose_name='出售日期',
        null=True, blank=True
    )
    house_image = models.ImageField(
        upload_to='house_images/', 
        null=True, 
        blank=True, 
        verbose_name='圖片'
    )
    
    # ===== 時間戳記 =====
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='建立時間'
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name='更新時間'
    )

    class Meta:
        db_table = 'house_house'
        verbose_name = '房屋資訊'
        verbose_name_plural = '房屋資訊'
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f"{self.address} - {self.house_type}"

