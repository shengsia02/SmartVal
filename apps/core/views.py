# apps/core/views.py
from decimal import Decimal  # <--- 1. 記得在檔案最上方加入這個 import
from django.shortcuts import render, redirect
from django.views.generic import FormView, TemplateView, View, ListView, DetailView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.http import Http404
from django.contrib import messages # 用來顯示 "請先登入" 的訊息

# 引入你的 Form, Service 和 Model
from .forms import EstimationForm, city_districts
from .services import HousePriceService
from .models import ValuationRecord

# ==========================================
# Helper Function: 遞迴將所有 Decimal 轉為 float
# ==========================================
def convert_decimal_to_float(data):
    """
    遞迴遍歷字典或列表，將所有的 Decimal 物件轉換為 float。
    這能一勞永逸解決 JSON serializable 錯誤。
    """
    if isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, dict):
        return {k: convert_decimal_to_float(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_decimal_to_float(item) for item in data]
    else:
        return data

# ==========================================
# 1. 首頁 View
# ==========================================
class HomeView(FormView):
    template_name = 'core/home.html'
    form_class = EstimationForm

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "請先登入會員，才能進行房屋估價。")
            return redirect(f"{reverse('account_login')}?next={request.path}")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        
        try:
            # 2. 呼叫 Service 進行預測
            raw_result = HousePriceService.predict(cleaned_data)
            
            if raw_result:
                # ==========================================
                # [FIX - 終極版] 使用遞迴函式清洗所有資料
                # ==========================================
                # 不再手動指定欄位，直接把整個字典丟進去洗
                result = convert_decimal_to_float(raw_result)

                # A. 準備輸入條件 (這裡手動轉也行，或是一樣用 convert_decimal_to_float)
                input_data = {
                    'city': cleaned_data.get('city'),
                    'town': cleaned_data.get('town'),
                    'street': cleaned_data.get('street'),
                    'house_type': str(cleaned_data.get('house_type')),
                    'house_age': float(cleaned_data.get('house_age') or 0),
                    'total_floors': float(cleaned_data.get('total_floors') or 0),
                    'floor_number': float(cleaned_data.get('floor_number') or 0),
                    'floor_area': float(cleaned_data.get('floor_area') or 0),
                    'land_area': float(cleaned_data.get('land_area') or 0),
                    'room_count': int(cleaned_data.get('room_count') or 0),
                }

                # B. 存入 Session
                self.request.session['valuation_result'] = result
                self.request.session['valuation_input'] = input_data
                
                # C. 跳轉到結果頁
                return redirect('core:valuation_result')

            else:
                form.add_error(None, "無法進行估價，請檢查地址是否正確。")
                return self.form_invalid(form)

        except Exception as e:
            # 建議保留 print 以便在 console 看到非預期的錯誤
            print(f"Error in HomeView: {e}")
            import traceback
            traceback.print_exc() 
            form.add_error(None, "系統發生錯誤，請稍後再試。")
            return self.form_invalid(form)

# ==========================================
# 2. 結果頁 View (從 Session 讀取並顯示)
# ==========================================
class ValuationResultView(LoginRequiredMixin, TemplateView):
    template_name = 'core/result.html'  # 我們稍後會建立這個檔案
    login_url = 'account_login' # 設定未登入時跳轉的路由名稱

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. 從 Session 取出資料
        result = self.request.session.get('valuation_result')
        input_data = self.request.session.get('valuation_input')
        
        # 2. 安全機制：如果沒資料 (例如使用者直接貼網址進入)，導回首頁
        if not result or not input_data:
            context['redirect_home'] = True
            return context
            
        context['result'] = result
        context['input_data'] = input_data
        
        # 3. 計算單價 (總價 / 建坪) 顯示用
        try:
            price = float(result.get('price', 0))
            area = float(input_data.get('floor_area', 1))
            context['unit_price'] = round(price / area, 2) if area > 0 else 0
        except:
            context['unit_price'] = 0
            
        return context

# ==========================================
# 3. 加入收藏 View (AJAX 請求)
# ==========================================
class AddFavoriteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            # 從 Session 拿資料 (比從前端傳安全)
            result = request.session.get('valuation_result')
            input_data = request.session.get('valuation_input')
            
            if not result or not input_data:
                return JsonResponse({'success': False, 'msg': '無估價資料，請重新搜尋'})
            
            # 建立資料庫紀錄 (Snapshot)
            record = ValuationRecord.objects.create(
                user=request.user,
                
                # 輸入條件
                city=input_data['city'],
                town=input_data['town'],
                street=input_data['street'],
                house_type=input_data['house_type'],
                house_age=input_data['house_age'],
                total_floors=input_data['total_floors'],
                floor_number=input_data['floor_number'],
                floor_area=input_data['floor_area'],
                land_area=input_data['land_area'],
                room_count=input_data['room_count'],
                
                # 估價結果
                predicted_price=result['price'],
                unit_price=result.get('price') / input_data['floor_area'] if input_data['floor_area'] else 0,
                
                # 視覺化快照
                latitude=result.get('target_coords', {}).get('lat'),
                longitude=result.get('target_coords', {}).get('lng'),
                
                # 【重點】儲存周邊實價資訊列表 (JSON)
                nearby_data=result.get('nearby_houses', []) 
            )
            
            return JsonResponse({'success': True, 'msg': '已加入收藏夾', 'id': record.id})
            
        except Exception as e:
            return JsonResponse({'success': False, 'msg': str(e)})

# ==========================================
# 4. 收藏夾列表 View (需登入)
# ==========================================
class FavoriteListView(LoginRequiredMixin, ListView):
    model = ValuationRecord
    template_name = 'core/favorite_list.html'
    context_object_name = 'records'
    paginate_by = 9  # 一頁顯示 9 張卡片

    def get_queryset(self):
        # 只顯示當前登入使用者的收藏，並按時間倒序排列
        return ValuationRecord.objects.filter(user=self.request.user).order_by('-created_at')

# ==========================================
# 5. 收藏夾詳情 View (需登入，重用 result.html)
# ==========================================
class FavoriteDetailView(LoginRequiredMixin, DetailView):
    model = ValuationRecord
    template_name = 'core/result.html' # <--- 注意：我們直接重用結果頁的模板！
    context_object_name = 'record'

    def get_queryset(self):
        # 確保使用者只能看自己的收藏
        return ValuationRecord.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self.object

        # === 關鍵魔法 ===
        # 我們要把資料庫的 Record 物件，轉換成 result.html 看得懂的 input_data 和 result 字典
        # 這樣就不用重寫一個 HTML 了！
        
        # 1. 重建 input_data
        context['input_data'] = {
            'city': record.city,
            'town': record.town,
            'street': record.street,
            'house_type': record.house_type,
            'house_age': record.house_age,
            'total_floors': record.total_floors,
            'floor_number': record.floor_number,
            'floor_area': record.floor_area,
            'land_area': record.land_area,
            'room_count': record.room_count,
        }

        # 2. 重建 result
        context['result'] = {
            'price': record.predicted_price,
            'nearby_houses': record.nearby_data, # 從 JSONField 取出當年的實價資料
            'target_coords': {
                'lat': record.latitude, 
                'lng': record.longitude
            }
        }
        
        # 3. 單價
        context['unit_price'] = record.unit_price

        # 4. 告訴 Template 這是「快照模式」，請隱藏收藏按鈕
        context['is_snapshot'] = True

        return context

class RemoveFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            # 1. 執行刪除
            record = ValuationRecord.objects.get(pk=pk, user=request.user)
            record.delete()
            
            # 2. 判斷請求類型
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # A. 來自 AJAX (列表頁) -> 回傳 JSON
                return JsonResponse({'success': True, 'msg': '已移除收藏'})
            else:
                # B. 來自 Form 表單 (詳細頁) -> 重導向回列表頁
                messages.success(request, "已成功移除該筆收藏")
                return redirect('core:favorite_list')
                
        except ValuationRecord.DoesNotExist:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'msg': '找不到該紀錄'}, status=404)
            else:
                messages.error(request, "找不到該紀錄")
                return redirect('core:favorite_list')
                
        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'msg': str(e)}, status=500)
            else:
                messages.error(request, "發生錯誤，無法移除")
                return redirect('core:favorite_list')

# ==========================================
# 6. 其他既有功能 (Dashboard, Ajax) - 保留原樣
# ==========================================

class DashboardHomeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/dashboard_home.html'
    login_url = 'account_login' 
    def test_func(self):
        return self.request.user.is_staff

def get_towns_ajax(request):
    city_name = request.GET.get('city')
    if city_name and city_name in city_districts:
        return JsonResponse({'towns': city_districts[city_name]}, status=200)
    return JsonResponse({'towns': []}, status=200)