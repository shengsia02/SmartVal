from django.contrib import admin
from .models import House, Agent, Buyer

@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('address', 'house_type', 'total_price', 'city', 'town', 'agent', 'created_at',)
    list_filter = ('house_type', 'city',)
    search_fields = ('address', 'city', 'town', 'house_type',)
    ordering = ('-created_at', '-total_price',)

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'company', 'branch', 'city', 'town',)
    list_filter = ('city', 'town', 'company',)
    search_fields = ('name', 'company', 'branch', 'city', 'town',)

@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email',)
    search_fields = ('name', 'phone', 'email',)