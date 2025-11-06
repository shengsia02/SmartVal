from django.shortcuts import render
from django.views.generic import TemplateView # 【新增】

# 【前台】訪客的 AI 估價頁面 ( / )
class HomeView(TemplateView):
    template_name = 'core/home.html'

# 【後台】管理員的 Dashboard ( /dashboard/ )
class DashboardHomeView(TemplateView):
    template_name = 'core/dashboard_home.html'