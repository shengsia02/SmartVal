# apps/core/models.py
from django.db import models
from django.conf import settings  # 為了引用 User 模型

class ValuationRecord(models.Model):
    """
    使用者估價收藏紀錄 (Snapshot 快照)
    記錄當下估價的所有輸入條件與輸出結果
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='valuations')
    
    # =====================================================
    # 1. 輸入條件 (Input Data) - 讓使用者知道是哪間房
    # =====================================================
    city = models.CharField("縣市", max_length=10)
    town = models.CharField("行政區", max_length=10)
    street = models.CharField("街道/路名", max_length=100)
    house_type = models.CharField("房屋類型", max_length=50)
    
    # 數值資料
    house_age = models.FloatField("屋齡", default=0)
    total_floors = models.FloatField("總樓層", default=0)
    floor_number = models.FloatField("所在樓層", default=0)
    floor_area = models.FloatField("建坪", default=0)
    land_area = models.FloatField("地坪", default=0)
    room_count = models.IntegerField("房間數", default=0)
    
    # =====================================================
    # 2. 估價結果 (Prediction Result)
    # =====================================================
    predicted_price = models.DecimalField("預估總價(萬)", max_digits=12, decimal_places=2)
    unit_price = models.DecimalField("預估單價(萬/坪)", max_digits=10, decimal_places=2, null=True, blank=True)
    
    # =====================================================
    # 3. 視覺化快照 (Snapshot Data) - 關鍵修改
    # =====================================================
    
    # 儲存目標房屋的經緯度 (為了畫地圖中心的紅色標記)
    latitude = models.FloatField("緯度", null=True, blank=True)
    longitude = models.FloatField("經度", null=True, blank=True)

    # 【重點新增】儲存「周邊實價資訊」的完整列表
    # 這會存入一個 List，裡面包含那 10 筆房屋的：地址、價格、屋齡、經緯度等
    # 透過這個欄位，我們就能重現「周邊實價資訊表格」和「地圖上的藍色點」
    nearby_data = models.JSONField("周邊實價資訊快照", default=list, blank=True)

    # 【預留】如果有「鄰近設施資訊」(如學校、公園)，未來也可以存這裡
    # 目前你的 Service 主要是回傳成交行情，若日後有接 Google Places API，可再開一個欄位
    # facility_data = models.JSONField("鄰近設施快照", default=list, blank=True)

    # =====================================================
    # 4. 系統欄位
    # =====================================================
    created_at = models.DateTimeField("建立時間", auto_now_add=True)
    is_favorite = models.BooleanField("是否收藏", default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "估價收藏紀錄"
        verbose_name_plural = "估價收藏紀錄"

    def __str__(self):
        return f"{self.user} - {self.city}{self.town} ({self.predicted_price}萬)"