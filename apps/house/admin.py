from django.contrib import admin
from .models import House, HouseDetail, Agent, Buyer

@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('address', 'house_type', 'total_price', 'buyers', 'agent', 'created_at')
    list_filter = ('house_type', 'agent', 'buyers',)
    search_fields = ('house_type', 'agent', 'buyers',)
    ordering = ('-total_price',)

@admin.register(HouseDetail)
class HouseDetailAdmin(admin.ModelAdmin):
    list_display = ('city', 'town', 'house_age', 'floor_area', 'land_area', 'unit_price', 'sold_time')
    list_filter = ('city', 'town',)
    search_fields = ('city', 'town',)

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'company', 'branch', 'city', 'town',)
    list_filter = ('city', 'town', 'company',)
    search_fields = ('name', 'company', 'branch', 'city', 'town',)

@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email',)
    search_fields = ('name', 'phone', 'email',)