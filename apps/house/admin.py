from django.contrib import admin
from .models import House, HouseDetail, Agent, Buyer

@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('address', 'house_type', 'total_price', 'agent', 'created_at')  # 列表顯示欄位
    list_filter = ('house_type', 'agent', 'buyers',)  # 篩選器
    search_fields = ('house_type', 'agent', 'buyers',)  # 搜尋欄位
    ordering = ('-total_price',)  # 預設排序

@admin.register(HouseDetail)
class HouseDetailAdmin(admin.ModelAdmin):
    list_display = ('city', 'town', 'house_age', 'floor_area', 'land_area', 'unit_price', 'sold_time')  # 列表顯示欄位
    list_filter = ('city', 'town',)  # 篩選器
    search_fields = ('city', 'town',)  # 搜尋欄位

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'town',)  # 列表顯示欄位
    list_filter = ('city', 'town',)  # 篩選器
    search_fields = ('city', 'town',)  # 搜尋欄位

@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ('name', 'occup', 'birth_date', 'nationality',)  # 列表顯示欄位
    list_filter = ('name', 'occup',)  # 篩選器
    search_fields = ('name', 'occup',)  # 搜尋欄位