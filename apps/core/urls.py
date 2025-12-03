from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # 前台主頁 ( / )
    path('', views.HomeView.as_view(), name='home'),
    
    # 後台首頁 ( /dashboard/ )
    path('dashboard/', views.DashboardHomeView.as_view(), name='dashboard_home'),
    
    # 【新增】AJAX 接口：獲取行政區列表
    path('ajax/get_towns/', views.get_towns_ajax, name='get_towns_ajax'),
]