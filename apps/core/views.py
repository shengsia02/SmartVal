# apps/core/views.py
from decimal import Decimal  # <--- 1. 記得在檔案最上方加入這個 import
from django.shortcuts import render, redirect
from django.views.generic import FormView, TemplateView, View, ListView, DetailView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.http import Http404
from django.contrib import messages # 用來顯示 "請先登入" 的訊息

# 引入 Celery 相關
from celery.result import AsyncResult
from .tasks import predict_house_price

# 引入你的 Form, Service 和 Model
from .forms import EstimationForm, city_districts
from .services import HousePriceService
from .models import ValuationRecord

from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import json

from apps.house.models import House, Agent, Buyer

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
# 1. 首頁 View (修改為非同步派發)
# ==========================================
class HomeView(FormView):
    template_name = 'core/home.html'
    form_class = EstimationForm

    def post(self, request, *args, **kwargs):
        # 1. 權限檢查
        if not request.user.is_authenticated:
            # 如果是 AJAX 請求 (Fetch)，回傳 401 JSON 讓前端導向
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                login_url = f"{reverse('account_login')}?next={request.path}"
                return JsonResponse({'status': 'redirect', 'url': login_url}, status=401)
            
            messages.warning(request, "請先登入會員，才能進行房屋估價。")
            return redirect(f"{reverse('account_login')}?next={request.path}")
            
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # 2. 準備資料
        cleaned_data = form.cleaned_data
        
        # 為了避免 Celery JSON 序列化錯誤，先將 Decimal 轉為 float/str
        serializable_data = convert_decimal_to_float(cleaned_data)
        
        # 手動確保特定欄位格式 (與原本邏輯一致)
        input_data = {
            'city': serializable_data.get('city'),
            'town': serializable_data.get('town'),
            'street': serializable_data.get('street'),
            'house_type': str(serializable_data.get('house_type')),
            'house_age': float(serializable_data.get('house_age') or 0),
            'total_floors': float(serializable_data.get('total_floors') or 0),
            'floor_number': float(serializable_data.get('floor_number') or 0),
            'floor_area': float(serializable_data.get('floor_area') or 0),
            'land_area': float(serializable_data.get('land_area') or 0),
            'room_count': int(serializable_data.get('room_count') or 0),
        }

        # 3. [關鍵修改] 派發 Celery 任務
        task = predict_house_price.delay(input_data)

        # 4. 回傳 task_id 給前端
        return JsonResponse({
            'task_id': task.id,
            'status': 'processing',
            'msg': '估價計算中...'
        })

    def form_invalid(self, form):
        # 如果表單驗證失敗，且是 AJAX 請求，回傳 JSON 錯誤
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'validation_error',
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)
    
# 新增這個簡單的 view
def coming_soon(request):
    """顯示「功能建置中」的幽默頁面"""
    return render(request, "core/coming_soon.html")


# ==========================================
# [新增] 任務狀態查詢 View
# ==========================================
class TaskStatusView(LoginRequiredMixin, View):
    def get(self, request, task_id):
        result = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'state': result.state,
        }

        if result.state == 'SUCCESS':
            task_result = result.result # tasks.py 回傳的字典
            
            # 【通用化修改】檢查這是哪種任務的回傳
            
            # A. 估價任務 (有 'input_data' 欄位)
            if isinstance(task_result, dict) and 'input_data' in task_result:
                if task_result.get('status') == 'success':
                    # ... (原本的 session 處理邏輯) ...
                    safe_result = convert_decimal_to_float(task_result['data'])
                    safe_input = convert_decimal_to_float(task_result['input_data'])
                    request.session['valuation_result'] = safe_result
                    request.session['valuation_input'] = safe_input
                    
                    response_data['status'] = 'completed'
                    response_data['redirect_url'] = reverse('core:valuation_result')
                else:
                    response_data['state'] = 'FAILURE'
                    response_data['error'] = task_result['data'].get('error', '未知錯誤')

            # B. Excel 匯入任務 (有 'message' 欄位，沒有 input_data)
            elif isinstance(task_result, dict) and 'message' in task_result:
                if task_result.get('status') == 'success':
                    response_data['status'] = 'completed'
                    response_data['message'] = task_result.get('message')
                else:
                    response_data['state'] = 'FAILURE'
                    response_data['error'] = task_result.get('error')
            
            # C. 其他未知任務
            else:
                response_data['data'] = task_result # 直接回傳原本結果

        elif result.state == 'FAILURE':
            response_data['error'] = str(result.result)
        
        return JsonResponse(response_data)

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
# [修改] 儀表板首頁 View (增加數據統計)
# ==========================================
class DashboardHomeView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/dashboard_home.html'
    login_url = 'account_login' 
    
    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- 1. KPI 核心指標 ---
        # 統計各個 Model 的總數量
        context['total_houses'] = House.objects.count()
        context['total_agents'] = Agent.objects.count()
        context['total_buyers'] = Buyer.objects.count()
        
        # 統計「本月估價次數」 (反映系統活躍度)
        # 使用 ValuationRecord 來代表使用者的估價行為
        now = timezone.now()
        context['estimates_this_month'] = ValuationRecord.objects.filter(
            created_at__year=now.year, 
            created_at__month=now.month
        ).count()

        # --- 2. 圖表資料：近 7 天估價流量趨勢 (Line Chart) ---
        dates = []
        traffic_data = []
        today = now.date()
        
        # 倒推 7 天
        for i in range(6, -1, -1):
            date_cursor = today - timedelta(days=i)
            dates.append(date_cursor.strftime('%m/%d')) # 格式化日期為 "12/17"
            
            # 查詢當天的估價紀錄數量
            count = ValuationRecord.objects.filter(
                created_at__date=date_cursor
            ).count()
            traffic_data.append(count)
            
        # 轉為 JSON 字串傳給前端 JS
        context['chart_dates'] = json.dumps(dates)
        context['chart_traffic'] = json.dumps(traffic_data)

        # --- 3. 圖表資料：房屋物件區域分佈 Top 5 (Doughnut Chart) ---
        top_cities = House.objects.values('city').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        area_labels = [item['city'] for item in top_cities]
        area_data = [item['count'] for item in top_cities]
        
        context['area_labels'] = json.dumps(area_labels)
        context['area_data'] = json.dumps(area_data)

        return context

# ==========================================
# 6. 其他既有功能 (Dashboard, Ajax) - 保留原樣
# ==========================================
def get_towns_ajax(request):
    city_name = request.GET.get('city')
    if city_name and city_name in city_districts:
        return JsonResponse({'towns': city_districts[city_name]}, status=200)
    return JsonResponse({'towns': []}, status=200)

class DataImportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'core/import_data.html' # 我們等下建立這個檔案
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff