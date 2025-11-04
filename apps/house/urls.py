from django.urls import path
from . import views

app_name = 'house'

urlpatterns = [
    path('', views.IntroductionView.as_view(), name='intro'),
    path('house_list/', views.HouseListView.as_view(), name='house_list'),
    path('house_detail/<int:house_id>/', views.HouseDetailView.as_view(), name='house_detail'),
    path('house_list/create/', views.HouseCreateView.as_view(), name='house_create'),
    path('house_list/<int:pk>/edit/', views.HouseUpdateView.as_view(), name='house_edit'),
    
    # 【新增】用於連動選單的 AJAX URL
    path('ajax/load-towns/', views.load_towns, name='ajax_load_towns'),
]