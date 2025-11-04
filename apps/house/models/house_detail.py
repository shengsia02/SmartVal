from django.db import models
from datetime import date
from .house import House

class HouseDetail(models.Model):
    """書籍詳細資訊（將不常用的資訊分離到另一個表格）"""
    # OneToOneField 建立一對一關聯
    house = models.OneToOneField(
        House,
        on_delete=models.CASCADE,
        related_name='detail',
        verbose_name='房屋'
    )
    city = models.CharField(max_length=200, verbose_name='縣市', null=True, blank=True)
    town = models.CharField(max_length=200, verbose_name='行政區', null=True, blank=True)
    house_age = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='屋齡（年）')
    floor_area = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='建坪')
    land_area = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='地坪')
    unit_price = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='單價（萬/坪）')
    sold_time = models.DateField(verbose_name='出售日期')
    
    # 【已移除】下面這行 description 欄位已被刪除
    # description = models.TextField(blank=True, verbose_name='房屋簡介')
    
    house_image = models.ImageField(upload_to='house_images/', null=True, blank=True, verbose_name='房屋圖片')

    class Meta:
        verbose_name = '房屋詳細資料'
        verbose_name_plural = '房屋詳細資料'

    def __str__(self):
        return f"{self.house.house_type}_{self.house.address} 的詳細資料"