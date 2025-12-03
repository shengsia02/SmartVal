# apps/core/views.py

from django.shortcuts import render
from django.views.generic import FormView, TemplateView # 引入 FormView
from django.http import JsonResponse
from .forms import EstimationForm, city_districts
# 【新增】引入權限控制 Mixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .services import HousePriceService  # 引入剛剛寫的 Service


# 【前台】訪客的 AI 估價頁面 ( / )
# 前台頁面不需要限制權限，維持原樣
class HomeView(FormView):
    template_name = 'core/home.html'
    form_class = EstimationForm
    success_url = '/'

    def form_valid(self, form):
        # 判斷是否為 AJAX 請求
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            
            try:
                # 取得表單清洗後的資料
                data = form.cleaned_data
                
                print(f"📥 收到估價請求: {data}")
                
                # 【直接呼叫 Service 進行預測】
                result = HousePriceService.predict(data) # 變數名稱改叫 result 比較合適
                
                if result is not None:
                    print(f"✅ 預測成功: 價格={result['price']}萬, 周邊房屋={len(result.get('nearby_houses', []))}筆")
                    
                    return JsonResponse({
                        'success': True,
                        'price': result['price'],               # 從 dict 取出價格
                        'nearby_houses': result.get('nearby_houses', []), # 取出周邊房屋
                        'target_coords': result.get('target_coords', {}), # 取出目標座標
                        'message': '估價完成'
                    })
                else:
                    print("❌ Service 回傳 None")
                    return JsonResponse({
                        'success': False, 
                        'error': '系統維護中，無法進行估價'
                    }, status=500)
                    
            except Exception as e:
                import traceback
                print(f"❌ 估價過程發生錯誤: {e}")
                print(traceback.format_exc())
                
                return JsonResponse({
                    'success': False,
                    'error': f'系統錯誤: {str(e)}'
                }, status=500)
        
        return super().form_valid(form)
    

# 【後台】管理員的 Dashboard ( /dashboard/ )
# 【修改】加入權限控制：必須登入 + 必須是工作人員 (is_staff)
class DashboardHomeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/dashboard_home.html'
    
    # 未登入時導向的 URL 名稱 (對應 urls.py 中的 name)
    login_url = 'account_login' 

    # 檢查使用者是否為工作人員
    def test_func(self):
        return self.request.user.is_staff

# 【新增】AJAX 接口：根據縣市獲取行政區
def get_towns_ajax(request):
    """
    接收 AJAX 請求，根據縣市名稱返回對應的行政區列表 (JSON)
    """
    city_name = request.GET.get('city')

    # 檢查 city_name 是否有效，並從 city_districts 中獲取行政區列表
    if city_name and city_name in city_districts:
        towns = city_districts[city_name]
        # 回傳 JSON 格式的行政區列表
        return JsonResponse({'towns': towns}, status=200)
    
    # 如果找不到縣市或請求無效，回傳空列表
    return JsonResponse({'towns': []}, status=200)