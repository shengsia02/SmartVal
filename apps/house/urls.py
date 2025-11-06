from django.urls import path
from . import views

app_name = 'house'

urlpatterns = [
    # 房屋
    path('list/', views.HouseListView.as_view(), name='house_list'),
    path('detail/<int:house_id>/', views.HouseDetailView.as_view(), name='house_detail'),
    path('create/', views.HouseCreateView.as_view(), name='house_create'),
    path('<int:pk>/edit/', views.HouseUpdateView.as_view(), name='house_edit'),
    
    # AJAX
    path('ajax/load-towns/', views.load_towns, name='ajax_load_towns'),
    
    # 仲介
    path('agents/', views.AgentListView.as_view(), name='agent_list'),
    path('agents/create/', views.AgentCreateView.as_view(), name='agent_create'),
    path('agents/<int:pk>/', views.AgentDetailView.as_view(), name='agent_detail'),
    path('agents/<int:pk>/edit/', views.AgentUpdateView.as_view(), name='agent_edit'),
    
    # 買家
    path('buyers/', views.BuyerListView.as_view(), name='buyer_list'),
    path('buyers/create/', views.BuyerCreateView.as_view(), name='buyer_create'),
    path('buyers/<int:pk>/', views.BuyerDetailView.as_view(), name='buyer_detail'),
    path('buyers/<int:pk>/edit/', views.BuyerUpdateView.as_view(), name='buyer_edit'),

    # 【!! 重大新增 !!】 Excel 批次匯入
    path('upload-excel/', views.ExcelUploadView.as_view(), name='upload_excel'),
]