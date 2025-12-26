# apps/core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # 前台主頁 (輸入表單)
    path('', views.HomeView.as_view(), name='home'),

    # [新增] 任務狀態查詢
    path('task-status/<str:task_id>/', views.TaskStatusView.as_view(), name='task_status'),
    
    # 【新增】估價結果頁
    path('result/', views.ValuationResultView.as_view(), name='valuation_result'),
    
    # 【新增】加入收藏 (AJAX)
    path('favorite/add/', views.AddFavoriteView.as_view(), name='add_favorite'),
    
    # 後台首頁
    path('dashboard/', views.DashboardHomeView.as_view(), name='dashboard_home'),

    # 【新增】獨立的匯入頁面路徑
    path('dashboard/import/', views.DataImportView.as_view(), name='import_data'),
    
    # AJAX 行政區連動
    path('ajax/get_towns/', views.get_towns_ajax, name='get_towns_ajax'),

    # 【新增】收藏列表
    path('favorites/', views.FavoriteListView.as_view(), name='favorite_list'),
    
    # 【新增】收藏詳情 (查看快照)
    path('favorites/<int:pk>/', views.FavoriteDetailView.as_view(), name='favorite_detail'),
    
    path('favorites/remove/<int:pk>/', views.RemoveFavoriteView.as_view(), name='remove_favorite'),

    # 新增這行路由
    path("coming-soon/", views.coming_soon, name="coming_soon"),
]