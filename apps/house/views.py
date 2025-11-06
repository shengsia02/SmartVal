from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy, reverse
from django.views.generic import View
from django.template.loader import render_to_string 
from .models import House, HouseDetail, Agent, Buyer
from .forms import HouseForm, HouseDetailForm, AgentForm, BuyerForm
# 【!! 修改 !!】 匯入 Choice 選項
from .forms import city_districts, HOUSE_TYPE_CHOICES, AGENT_CITY_CHOICES

import pandas as pd
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator

# 【!! 新增 !!】 匯入 Q 物件，用於 "icontains" (包含) 查詢
from django.db.models import Q

# ==========================================
# 房屋 (House) 相關 Views
# ==========================================
class HouseListView(View):
    def get(self, request):
        # 【!! 修改 !!】 1. 獲取 GET 參數
        query = request.GET.get('q', '')
        house_type_filter = request.GET.get('house_type', '')

        # 【!! 修改 !!】 2. 修正排序並開始過濾
        all_houses = House.objects.all().order_by('-created_at', '-id') 
        
        if query:
            # 搜尋地址 (icontains = 包含, 不分大小寫)
            all_houses = all_houses.filter(address__icontains=query)
        
        if house_type_filter:
            # 篩選房屋類型
            all_houses = all_houses.filter(house_type=house_type_filter)

        # 【!! 修改 !!】 3. Paginator 使用 "過濾後" 的結果
        paginator = Paginator(all_houses, 10) 
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        house_form = HouseForm()
        detail_form = HouseDetailForm()
        context = {
            'houses': page_obj, 
            'total_count': all_houses.count(),
            'create_form': house_form,
            'create_detail_form': detail_form,
            # 【!! 新增 !!】 傳回篩選器選項和目前的值
            'house_type_choices': HOUSE_TYPE_CHOICES[1:], # 移除 ("_,"請選擇...")
            'current_q': query,
            'current_house_type': house_type_filter,
        }
        return render(request, 'house/house_list.html', context) 

    def post(self, request):
        house_id = request.POST.get('house_id')
        house = get_object_or_404(House, pk=house_id)
        house.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponse(status=200) 
        return redirect('house:house_list')

# ... (HouseDetailView 保持不變) ...
class HouseDetailView(View):
    def get(self, request, house_id):
        house = get_object_or_404(House, id=house_id)
        context = {
            'house': house,
            'page_title': "房屋資訊", 
        }
        return render(request, 'house/house_detail.html', context)

# --- (Create / Update View 的 AJAX 成功回傳已修改為 success:True) ---
class HouseCreateView(View):
    template_name = 'house/house_form.html' 
    success_url = reverse_lazy('house:house_list')

    def get(self, request):
        return redirect(self.success_url)

    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        house_form = HouseForm(request.POST)
        detail_form = HouseDetailForm(request.POST, request.FILES) 
        
        if house_form.is_valid() and detail_form.is_valid():
            house = house_form.save(commit=False)
            house.agent = house_form.cleaned_data['agent']
            house.buyers = house_form.cleaned_data['buyers']
            house.save()
            house_form.save_m2m() 
            detail = detail_form.save(commit=False)
            detail.house = house
            detail.save()
            
            if is_ajax:
                return JsonResponse({'success': True})
            else:
                return redirect(self.success_url)
        else:
            if is_ajax:
                context = {
                    'form': house_form,
                    'detail_form': detail_form
                }
                form_html = render_to_string(
                    'house/_house_form_fields.html', 
                    context, 
                    request=request
                )
                return JsonResponse({'success': False, 'html': form_html})
            else:
                context = {
                    'page_title': '新增房屋',
                    'form': house_form,
                    'detail_form': detail_form,
                }
                return render(request, self.template_name, context)

class HouseUpdateView(View):
    template_name = 'house/house_form.html' 
    success_url = reverse_lazy('house:house_list')

    def get_object_and_detail(self, pk):
        house = get_object_or_404(House, pk=pk)
        detail, created = HouseDetail.objects.get_or_create(house=house)
        return house, detail

    def get(self, request, pk):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        house, detail = self.get_object_and_detail(pk)
        
        house_form = HouseForm(instance=house, is_update=True)
        detail_form = HouseDetailForm(instance=detail, is_update=True)

        context = {
            'form': house_form,
            'detail_form': detail_form
        }
        
        if is_ajax:
            form_html = render_to_string(
                'house/_house_form_fields.html', 
                context, 
                request=request
            )
            return JsonResponse({'success': True, 'html': form_html})
        else:
            context['page_title'] = f'編輯 {house.address} 的房屋資料'
            return render(request, self.template_name, context)

    def post(self, request, pk):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        house, detail = self.get_object_and_detail(pk)
        
        house_form = HouseForm(request.POST, instance=house, is_update=True)
        detail_form = HouseDetailForm(request.POST, request.FILES, instance=detail, is_update=True)

        if house_form.is_valid() and detail_form.is_valid():
            house_form.save()
            detail_form.save()
            
            if is_ajax:
                return JsonResponse({'success': True})
            else:
                return redirect(self.success_url)
        else:
            if is_ajax:
                context = {
                    'form': house_form,
                    'detail_form': detail_form
                }
                form_html = render_to_string(
                    'house/_house_form_fields.html', 
                    context, 
                    request=request
                )
                return JsonResponse({'success': False, 'html': form_html})
            else:
                context = {
                    'page_title': f'編輯 {house.address} 的房屋資料',
                    'form': house_form,
                    'detail_form': detail_form,
                }
                return render(request, self.template_name, context)

def load_towns(request):
    city = request.GET.get('city')
    towns = city_districts.get(city, [])
    return JsonResponse({'towns': towns})

# ==========================================
# 仲介 (Agent) 相關 Views
# ==========================================
class AgentListView(View):
    def get(self, request):
        # 【!! 修改 !!】 1. 獲取 GET 參數
        query = request.GET.get('q', '')
        city_filter = request.GET.get('city', '')

        # 【!! 修改 !!】 2. 開始過濾
        all_agents = Agent.objects.all()
        
        if query:
            # 搜尋姓名
            all_agents = all_agents.filter(name__icontains=query)
        
        if city_filter:
            # 篩選縣市
            all_agents = all_agents.filter(city=city_filter)

        all_agents = all_agents.order_by('name') # 最後才排序

        # 【!! 修改 !!】 3. Paginator 使用 "過濾後" 的結果
        paginator = Paginator(all_agents, 10) 
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        form = AgentForm() 
        context = {
            'agents': page_obj, 
            'total_count': all_agents.count(),
            'create_form': form,
            # 【!! 新增 !!】 傳回篩選器選項和目前的值
            'agent_city_choices': AGENT_CITY_CHOICES[1:], # 移除 ("_,"請選擇...")
            'current_q': query,
            'current_city': city_filter,
        }
        return render(request, 'house/agent_list.html', context)
    
    def post(self, request):
        agent_id = request.POST.get('agent_id')
        agent = get_object_or_404(Agent, pk=agent_id)
        agent.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponse(status=200)
        return redirect('house:agent_list')

# ... (AgentCreateView, AgentDetailView, AgentUpdateView 保持不變) ...
class AgentCreateView(View):
    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            return redirect('house:agent_list')
        
        form = AgentForm(request.POST) 
        
        if form.is_valid():
            agent = form.save()
            if is_ajax:
                return JsonResponse({'success': True})
        else:
            if is_ajax:
                context = {'form': form}
                form_html = render_to_string(
                    'house/_agent_form_fields.html', 
                    context, 
                    request=request
                )
                return JsonResponse({'success': False, 'html': form_html})
        
        return redirect('house:agent_list') 

class AgentDetailView(View):
    def get(self, request, pk):
        agent = get_object_or_404(Agent, pk=pk)
        context = {
            'agent': agent,
            'page_title': "仲介資訊", 
        }
        return render(request, 'house/agent_detail.html', context)

class AgentUpdateView(View):
    def get(self, request, pk):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            return redirect('house:agent_list')
        
        agent = get_object_or_404(Agent, pk=pk)
        form = AgentForm(instance=agent)
        
        context = {'form': form}
        form_html = render_to_string(
            'house/_agent_form_fields.html', 
            context, 
            request=request
        )
        return JsonResponse({'success': True, 'html': form_html})

    def post(self, request, pk):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            return redirect('house:agent_list')

        agent = get_object_or_404(Agent, pk=pk)
        form = AgentForm(request.POST, instance=agent)

        if form.is_valid():
            agent = form.save()
            if is_ajax:
                return JsonResponse({'success': True})
        else:
            if is_ajax:
                context = {'form': form}
                form_html = render_to_string(
                    'house/_agent_form_fields.html', 
                    context, 
                    request=request
                )
                return JsonResponse({'success': False, 'html': form_html})
        
        return redirect('house:agent_list') 

# ==========================================
# 買家 (Buyer) 相關 Views
# ==========================================
class BuyerListView(View):
    def get(self, request):
        # 【!! 修改 !!】 1. 獲取 GET 參數
        query = request.GET.get('q', '')

        # 【!! 修改 !!】 2. 開始過濾
        all_buyers = Buyer.objects.all()

        if query:
            # 搜尋姓名
            all_buyers = all_buyers.filter(name__icontains=query)

        all_buyers = all_buyers.order_by('name') # 最後才排序

        # 【!! 修改 !!】 3. Paginator 使用 "過濾後" 的結果
        paginator = Paginator(all_buyers, 10) 
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        form = BuyerForm() 
        context = {
            'buyers': page_obj, 
            'total_count': all_buyers.count(),
            'create_form': form,
            # 【!! 新增 !!】 傳回目前的值
            'current_q': query,
        }
        return render(request, 'house/buyer_list.html', context)
    
    def post(self, request):
        buyer_id = request.POST.get('buyer_id')
        buyer = get_object_or_404(Buyer, pk=buyer_id)
        buyer.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponse(status=200)
        return redirect('house:buyer_list')

# ... (BuyerCreateView, BuyerDetailView, BuyerUpdateView 保持不變) ...
class BuyerCreateView(View):
    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            return redirect('house:buyer_list')
        
        form = BuyerForm(request.POST) 
        
        if form.is_valid():
            buyer = form.save()
            if is_ajax:
                return JsonResponse({'success': True})
        else:
            if is_ajax:
                context = {'form': form}
                form_html = render_to_string(
                    'house/_buyer_form_fields.html', 
                    context, 
                    request=request
                )
                return JsonResponse({'success': False, 'html': form_html})
        
        return redirect('house:buyer_list') 

class BuyerDetailView(View):
    def get(self, request, pk):
        buyer = get_object_or_404(Buyer, pk=pk)
        context = {
            'buyer': buyer,
            'page_title': "買家資訊", 
        }
        return render(request, 'house/buyer_detail.html', context)

class BuyerUpdateView(View):
    def get(self, request, pk):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            return redirect('house:buyer_list')
        
        buyer = get_object_or_404(Buyer, pk=pk)
        form = BuyerForm(instance=buyer)
        
        context = {'form': form}
        form_html = render_to_string(
            'house/_buyer_form_fields.html', 
            context, 
            request=request
        )
        return JsonResponse({'success': True, 'html': form_html})

    def post(self, request, pk):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            return redirect('house:buyer_list')

        buyer = get_object_or_404(Buyer, pk=pk)
        form = BuyerForm(request.POST, instance=buyer)

        if form.is_valid():
            buyer = form.save()
            if is_ajax:
                return JsonResponse({'success': True})
        else:
            if is_ajax:
                context = {'form': form}
                form_html = render_to_string(
                    'house/_buyer_form_fields.html', 
                    context, 
                    request=request
                )
                return JsonResponse({'success': False, 'html': form_html})
        
        return redirect('house:buyer_list') 


# ==========================================
# Excel 匯入 (保持不變)
# ==========================================
class ExcelUploadView(View):
    
    AGENT_COLUMN_MAP = {
        '姓名': 'name',
        '聯絡電話': 'phone',
        '電子郵件': 'email',
        '隸屬公司': 'company',
        '分行名稱': 'branch',
        '分行縣市': 'city',
        '分行行政區': 'town',
    }
    
    BUYER_COLUMN_MAP = {
        '姓名': 'name',
        '聯絡電話': 'phone',
        '電子郵件': 'email',
    }
    
    HOUSE_COLUMN_MAP = {
        '地址': 'address',
        '房屋類型': 'house_type',
        '總價格（萬）': 'total_price',
        '仲介': 'agent_name', 
        '買家': 'buyer_name', 
        '縣市': 'city',
        '行政區': 'town',
        '屋齡': 'house_age',
        '建坪': 'floor_area',
        '地坪': 'land_area',
        '單價（萬/坪）': 'unit_price',
        '出售日期': 'sold_time',
    }

    def post(self, request):
        if not request.FILES.get('file'):
            return JsonResponse({'success': False, 'error': '沒有上傳檔案。'}, status=400)

        excel_file = request.FILES['file']
        
        try:
            xls = pd.read_excel(excel_file, sheet_name=None)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'無法讀取 Excel 檔案，請確認格式正確。錯誤: {e}'}, status=400)

        required_sheets = ['仲介', '買家', '房屋']
        for sheet_name in required_sheets:
            if sheet_name not in xls:
                return JsonResponse({'success': False, 'error': f'Excel 檔案中缺少 "{sheet_name}" 工作表。'}, status=400)

        try:
            with transaction.atomic():
                # ... (匯入仲介和買家的邏輯保持不變) ...
                sheet_name = '仲介'
                df_agent = xls[sheet_name].astype(str) 
                df_agent = df_agent.rename(columns=self.AGENT_COLUMN_MAP)
                for index, row in df_agent.iterrows():
                    data = row.to_dict()
                    data = {k: (None if pd.isna(v) or v == 'nan' else v) for k, v in data.items()}
                    form = AgentForm(data)
                    if not form.is_valid():
                        errors = "; ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
                        raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行: {errors}')
                    Agent.objects.update_or_create(name=data['name'], defaults=data)

                sheet_name = '買家'
                df_buyer = xls[sheet_name].astype(str)
                df_buyer = df_buyer.rename(columns=self.BUYER_COLUMN_MAP)
                for index, row in df_buyer.iterrows():
                    data = row.to_dict()
                    data = {k: (None if pd.isna(v) or v == 'nan' else v) for k, v in data.items()}
                    form = BuyerForm(data)
                    if not form.is_valid():
                        errors = "; ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
                        raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行: {errors}')
                    Buyer.objects.update_or_create(name=data['name'], defaults=data)

                # ... (匯入房屋的邏輯保持不變) ...
                sheet_name = '房屋'
                df_house = xls[sheet_name].astype(str)
                df_house = df_house.rename(columns=self.HOUSE_COLUMN_MAP)
                for index, row in df_house.iterrows():
                    data = row.to_dict()
                    data = {k: (None if pd.isna(v) or v == 'nan' else v) for k, v in data.items()}

                    try:
                        agent_name = data.pop('agent_name') 
                        agent_obj = Agent.objects.get(name=agent_name)
                    except Agent.DoesNotExist:
                        raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行: 找不到仲介 "{agent_name}"。請先在 "仲介" 工作表建立。')
                    
                    try:
                        buyer_name = data.pop('buyer_name') 
                        buyer_obj = Buyer.objects.get(name=buyer_name)
                    except Buyer.DoesNotExist:
                        raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行: 找不到買家 "{buyer_name}"。請先在 "買家" 工作表建立。')

                    house_data = {}
                    detail_data = {}
                    for field in ['address', 'house_type', 'total_price']:
                        if field in data: house_data[field] = data[field]
                    for field in ['city', 'town', 'house_age', 'floor_area', 'land_area', 'unit_price', 'sold_time']:
                        if field in data:
                            if field == 'sold_time' and data[field]: detail_data[field] = data[field].split(' ')[0]
                            else: detail_data[field] = data[field]
                    
                    house_data['agent'] = agent_obj
                    house_data['buyers'] = buyer_obj

                    house_form = HouseForm(house_data)
                    detail_form = HouseDetailForm(detail_data)

                    if not house_form.is_valid():
                        errors = "; ".join([f"{k}: {v[0]}" for k, v in house_form.errors.items()])
                        raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行 (房屋資料): {errors}')
                    if not detail_form.is_valid():
                        errors = "; ".join([f"{k}: {v[0]}" for k, v in detail_form.errors.items()])
                        raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行 (詳細資料): {errors}')

                    house_data['agent_id'] = agent_obj.id
                    house_data['buyers_id'] = buyer_obj.id
                    house_data.pop('agent') 
                    house_data.pop('buyers') 

                    house_obj, created = House.objects.update_or_create(address=house_data['address'], defaults=house_data)
                    HouseDetail.objects.update_or_create(house=house_obj, defaults=detail_data)

            return JsonResponse({'success': True, 'message': 'Excel 資料已成功匯入！'})

        except ValidationError as e:
            return JsonResponse({'success': False, 'error': f'資料驗證失敗: {e.message}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'匯入過程中發生未預期的錯誤: {e}'}, status=500)