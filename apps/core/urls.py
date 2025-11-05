from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # 前台主頁 ( / )
    path('', views.HomeView.as_view(), name='home'),
    
    # 後台首頁 ( /dashboard/ )
    path('dashboard/', views.DashboardHomeView.as_view(), name='dashboard_home'),
]