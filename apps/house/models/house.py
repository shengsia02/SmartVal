from django.db import models
from datetime import date
from .agent import Agent
from .buyer import Buyer

class House(models.Model):
    address = models.CharField(
        max_length=200, 
        verbose_name='地址'
    )
    house_type = models.CharField(max_length=100, 
        verbose_name='房屋類型'
    )
    total_price = models.IntegerField(
        verbose_name='總價（萬/坪）'
    )
    buyers = models.ForeignKey(
        Buyer, 
        on_delete=models.CASCADE,
        related_name='buyers', 
        verbose_name='買家', 
        null=True, blank=True
    )
    agent = models.ForeignKey(
        Agent, 
        on_delete=models.CASCADE, 
        related_name='agent', 
        verbose_name='房屋中介', 
        null=True, blank=True
    )
    created_at = models.DateField(
        default=date.today, 
        verbose_name='建立檔案時間'
    )

    class Meta:
        verbose_name = '房屋資訊'
        verbose_name_plural = '房屋資訊'

    def __str__(self):
        return f"{self.address}_{self.house_type}"

