from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy, reverse
from django.template.loader import render_to_string 
from .models import House, Agent, Buyer
from .forms import HouseForm, AgentForm, BuyerForm
from .forms import city_districts, HOUSE_TYPE_CHOICES, AGENT_CITY_CHOICES
from django.contrib import messages

import pandas as pd
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.db.models import Q

# 【新增】引入權限控制 Mixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# ==========================================
# 房屋 (House) 相關 Views
# ==========================================

# 【修改】HouseListView 加入權限控制
class HouseListView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        query = request.GET.get('q', '')
        house_type_filter = request.GET.get('house_type', '')

        all_houses = House.objects.all().order_by('-created_at', '-id') 
        
        if query:
            all_houses = all_houses.filter(address__icontains=query)
        
        if house_type_filter:
            all_houses = all_houses.filter(house_type=house_type_filter)

        paginator = Paginator(all_houses, 10) 
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        house_form = HouseForm()
        context = {
            'houses': page_obj, 
            'total_count': all_houses.count(),
            'create_form': house_form,
            'house_type_choices': HOUSE_TYPE_CHOICES[1:], 
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

# 【修改】HouseDetailView 加入權限控制
class HouseDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, house_id):
        house = get_object_or_404(House, id=house_id)
        context = {
            'house': house,
            'page_title': "房屋資訊", 
        }
        return render(request, 'house/house_detail.html', context)

# 【修改】HouseCreateView 加入權限控制
class HouseCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'house/house_form.html' 
    success_url = reverse_lazy('house:house_list')
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        return redirect(self.success_url)

    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        form = HouseForm(request.POST, request.FILES)
        
        if form.is_valid():
            house = form.save()
            if is_ajax:
                return JsonResponse({'success': True})
            else:
                messages.success(request, '房屋新增成功！')
                return redirect(self.success_url)
        else:
            if is_ajax:
                form_html = render_to_string(
                    'house/_house_form_fields.html', 
                    {'form': form}, 
                    request=request
                )
                return JsonResponse({'success': False, 'html': form_html})
            else:
                context = {
                    'page_title': '新增房屋',
                    'form': form,
                }
                return render(request, self.template_name, context)

# 【修改】HouseUpdateView 加入權限控制
class HouseUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'house/house_form.html' 
    success_url = reverse_lazy('house:house_list')
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, pk):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        house = get_object_or_404(House, pk=pk)
        form = HouseForm(instance=house)

        if is_ajax:
            form_html = render_to_string(
                'house/_house_form_fields.html', 
                {'form': form}, 
                request=request
            )
            return JsonResponse({'success': True, 'html': form_html})
        else:
            context = {
                'page_title': f'編輯 {house.address} 的房屋資料',
                'form': form
            }
            return render(request, self.template_name, context)

    def post(self, request, pk):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        house = get_object_or_404(House, pk=pk)
        form = HouseForm(request.POST, request.FILES, instance=house)
        
        if form.is_valid():
            form.save()
            if is_ajax:
                return JsonResponse({'success': True})
            else:
                messages.success(request, '房屋更新成功！')
                return redirect(self.success_url)
        else:
            if is_ajax:
                form_html = render_to_string(
                    'house/_house_form_fields.html', 
                    {'form': form}, 
                    request=request
                )
                return JsonResponse({'success': False, 'html': form_html})
            else:
                context = {
                    'page_title': f'編輯 {house.address} 的房屋資料',
                    'form': form,
                }
                return render(request, self.template_name, context)

def load_towns(request):
    city = request.GET.get('city')
    towns = city_districts.get(city, [])
    return JsonResponse({'towns': towns})

# ==========================================
# 仲介 (Agent) 相關 Views
# ==========================================

# 【修改】AgentListView 加入權限控制
class AgentListView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        query = request.GET.get('q', '')
        city_filter = request.GET.get('city', '')

        all_agents = Agent.objects.all()
        
        if query:
            all_agents = all_agents.filter(name__icontains=query)
        
        if city_filter:
            all_agents = all_agents.filter(city=city_filter)

        all_agents = all_agents.order_by('-id', 'name') 

        paginator = Paginator(all_agents, 10) 
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        form = AgentForm() 
        context = {
            'agents': page_obj, 
            'total_count': all_agents.count(),
            'create_form': form,
            'agent_city_choices': AGENT_CITY_CHOICES[1:], 
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

# 【修改】AgentCreateView 加入權限控制
class AgentCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

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

# 【修改】AgentDetailView 加入權限控制
class AgentDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, pk):
        agent = get_object_or_404(Agent, pk=pk)
        context = {
            'agent': agent,
            'page_title': "仲介資訊", 
        }
        return render(request, 'house/agent_detail.html', context)

# 【修改】AgentUpdateView 加入權限控制
class AgentUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

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

# 【修改】BuyerListView 加入權限控制
class BuyerListView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        query = request.GET.get('q', '')

        all_buyers = Buyer.objects.all()

        if query:
            all_buyers = all_buyers.filter(name__icontains=query)

        all_buyers = all_buyers.order_by('-id', 'name') 

        paginator = Paginator(all_buyers, 10) 
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        form = BuyerForm() 
        context = {
            'buyers': page_obj, 
            'total_count': all_buyers.count(),
            'create_form': form,
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

# 【修改】BuyerCreateView 加入權限控制
class BuyerCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

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

# 【修改】BuyerDetailView 加入權限控制
class BuyerDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, pk):
        buyer = get_object_or_404(Buyer, pk=pk)
        context = {
            'buyer': buyer,
            'page_title': "買家資訊", 
        }
        return render(request, 'house/buyer_detail.html', context)

# 【修改】BuyerUpdateView 加入權限控制
class BuyerUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff

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
# Excel 匯入
# ==========================================

# 【修改】ExcelUploadView 加入權限控制
class ExcelUploadView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff
    
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
        '縣市': 'city',
        '行政區': 'town',
        '房屋類型': 'house_type',
        '地址': 'address',
        '所在層數': 'floor_number',
        '地坪': 'land_area',
        '地上總層數': 'total_floors',
        '建坪': 'floor_area',
        '房間數': 'room_count',
        '總價格（萬元）': 'total_price',
        '建坪單價(萬元/坪)': 'unit_price',
        '經度': 'longitude',
        '緯度': 'latitude',
        '屋齡（年）': 'house_age',
        '出售日期': 'sold_time',
        '仲介': 'agent_name', 
        '買家': 'buyer_name',
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

        BATCH_SIZE = 1000

        try:
            # ===== 1. 處理仲介 (同原程式碼) =====
            sheet_name = '仲介'
            df_agent = xls[sheet_name].astype(str)
            df_agent = df_agent.rename(columns=self.AGENT_COLUMN_MAP)
            
            for batch_start in range(0, len(df_agent), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(df_agent))
                batch_df = df_agent.iloc[batch_start:batch_end]
                
                with transaction.atomic():
                    agents_to_create = []
                    agents_to_update = []
                    existing_agents = {a.name: a for a in Agent.objects.filter(name__in=batch_df['name'].tolist())}
                    
                    for index, row in batch_df.iterrows():
                        data = row.to_dict()
                        data = {k: (None if pd.isna(v) or v == 'nan' else v) for k, v in data.items()}
                        
                        if not data.get('name'):
                            raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行: 姓名為必填')
                        
                        if data['name'] in existing_agents:
                            agent = existing_agents[data['name']]
                            for key, value in data.items():
                                setattr(agent, key, value)
                            agents_to_update.append(agent)
                        else:
                            agents_to_create.append(Agent(**data))
                    
                    if agents_to_create:
                        Agent.objects.bulk_create(agents_to_create, ignore_conflicts=True)
                    if agents_to_update:
                        Agent.objects.bulk_update(agents_to_update, ['phone', 'email', 'company', 'branch', 'city', 'town'])

            # ===== 2. 處理買家 (同原程式碼) =====
            sheet_name = '買家'
            df_buyer = xls[sheet_name].astype(str)
            df_buyer = df_buyer.rename(columns=self.BUYER_COLUMN_MAP)
            
            for batch_start in range(0, len(df_buyer), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(df_buyer))
                batch_df = df_buyer.iloc[batch_start:batch_end]
                
                with transaction.atomic():
                    buyers_to_create = []
                    buyers_to_update = []
                    existing_buyers = {b.name: b for b in Buyer.objects.filter(name__in=batch_df['name'].tolist())}
                    
                    for index, row in batch_df.iterrows():
                        data = row.to_dict()
                        data = {k: (None if pd.isna(v) or v == 'nan' else v) for k, v in data.items()}
                        
                        if not data.get('name'):
                            raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行: 姓名為必填')
                        
                        if data['name'] in existing_buyers:
                            buyer = existing_buyers[data['name']]
                            for key, value in data.items():
                                setattr(buyer, key, value)
                            buyers_to_update.append(buyer)
                        else:
                            buyers_to_create.append(Buyer(**data))
                    
                    if buyers_to_create:
                        Buyer.objects.bulk_create(buyers_to_create, ignore_conflicts=True)
                    if buyers_to_update:
                        Buyer.objects.bulk_update(buyers_to_update, ['phone', 'email'])

            # ===== 3. 處理房屋 (已修正為單一模型邏輯) =====
            sheet_name = '房屋'
            df_house = xls[sheet_name].astype(str)
            df_house = df_house.rename(columns=self.HOUSE_COLUMN_MAP)
            
            # 準備關聯資料
            agent_names = df_house['agent_name'].dropna().unique().tolist()
            buyer_names = df_house['buyer_name'].dropna().unique().tolist()
            
            agents_dict = {a.name: a for a in Agent.objects.filter(name__in=agent_names)}
            buyers_dict = {b.name: b for b in Buyer.objects.filter(name__in=buyer_names)}
            
            # 定義數值格式欄位
            DECIMAL_2DP_FIELDS = {'house_age', 'floor_area', 'land_area', 'unit_price'}
            DECIMAL_12DP_FIELDS = {'longitude', 'latitude'}
            INTEGER_FIELDS = {'floor_number', 'total_floors', 'room_count', 'total_price'}
            
            total_rows = len(df_house)
            for batch_start in range(0, total_rows, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, total_rows)
                batch_df = df_house.iloc[batch_start:batch_end]
                
                with transaction.atomic():
                    houses_to_create = []
                    houses_to_update = []
                    
                    # 判斷是否為現有房屋 (依據地址)
                    batch_addresses = batch_df['address'].dropna().tolist()
                    # 【修改】不再需要 select_related('detail')
                    existing_houses = {h.address: h for h in House.objects.filter(address__in=batch_addresses)}
                    existing_addresses = set(existing_houses.keys())
                    
                    for idx_in_batch, (index, row) in enumerate(batch_df.iterrows()):
                        data = row.to_dict()
                        data = {k: (None if pd.isna(v) or v == 'nan' else v) for k, v in data.items()}
                        
                        # 1. 關聯欄位驗證
                        agent_name = data.pop('agent_name', None)
                        buyer_name = data.pop('buyer_name', None)
                        
                        if not agent_name or agent_name not in agents_dict:
                            raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行: 找不到仲介 "{agent_name}"。')
                        if not buyer_name or buyer_name not in buyers_dict:
                            raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行: 找不到買家 "{buyer_name}"。')
                        
                        agent_obj = agents_dict[agent_name]
                        buyer_obj = buyers_dict[buyer_name]
                        
                        # 2. 資料清洗與賦值
                        house_params = {}
                        
                        # 必填檢查
                        if not data.get('address'):
                            raise ValidationError(f'工作表 "{sheet_name}", 第 {index + 2} 行: 地址為必填')

                        # 遍歷所有欄位進行處理
                        # 定義所有屬於 House 的欄位 (除了 agent, buyers 以外)
                        ALL_HOUSE_FIELDS = [
                            'city', 'town', 'house_type', 'address', 
                            'floor_number', 'land_area', 'total_floors', 
                            'floor_area', 'room_count', 'total_price', 
                            'unit_price', 'longitude', 'latitude', 
                            'house_age', 'sold_time'
                        ]

                        for field in ALL_HOUSE_FIELDS:
                            if field not in data:
                                continue
                            
                            value = data[field]
                            
                            if value in (None, '', 'nan'):
                                house_params[field] = None
                                continue

                            # 格式轉換
                            if field == 'sold_time':
                                house_params[field] = str(value).split(' ')[0] # 簡單處理日期
                            
                            elif field in DECIMAL_2DP_FIELDS:
                                try:
                                    house_params[field] = Decimal(value).quantize(Decimal('0.01'))
                                except InvalidOperation:
                                    raise ValidationError(f'第 {index + 2} 行: {field} 格式錯誤: {value}')
                            
                            elif field in DECIMAL_12DP_FIELDS:
                                try:
                                    house_params[field] = Decimal(value).quantize(Decimal('0.000000000001'))
                                except InvalidOperation:
                                    raise ValidationError(f'第 {index + 2} 行: {field} 格式錯誤: {value}')
                            
                            elif field in INTEGER_FIELDS:
                                try:
                                    house_params[field] = int(Decimal(value))
                                except (InvalidOperation, ValueError):
                                    raise ValidationError(f'第 {index + 2} 行: {field} 必須是整數: {value}')
                            
                            else:
                                house_params[field] = value

                        # 放入關聯物件
                        house_params['agent'] = agent_obj
                        house_params['buyers'] = buyer_obj # 注意：這裏假設你的 Model Field 叫 buyers
                        
                        # 3. 建立或更新物件
                        address = house_params['address']
                        
                        if address in existing_addresses:
                            # 更新
                            house = existing_houses[address]
                            for key, val in house_params.items():
                                setattr(house, key, val)
                            houses_to_update.append(house)
                        else:
                            # 新增
                            house = House(**house_params)
                            houses_to_create.append(house)
                    
                    # 4. 批量操作 (Bulk Operations)
                    # 定義所有要更新的欄位 (Foreign Keys 用欄位名即可)
                    UPDATE_FIELDS = [
                        'city', 'town', 'house_type', 
                        'floor_number', 'land_area', 'total_floors', 
                        'floor_area', 'room_count', 'total_price', 
                        'unit_price', 'longitude', 'latitude', 
                        'house_age', 'sold_time', 'agent', 'buyers'
                    ]

                    if houses_to_update:
                        House.objects.bulk_update(houses_to_update, UPDATE_FIELDS)
                    
                    if houses_to_create:
                        House.objects.bulk_create(houses_to_create)

            return JsonResponse({'success': True, 'message': 'Excel 資料已成功匯入！'})

        except ValidationError as e:
            return JsonResponse({'success': False, 'error': f'資料驗證失敗: {e.message}'}, status=400)
        except Exception as e:
            import traceback
            print(traceback.format_exc()) # 印出詳細錯誤以便除錯
            return JsonResponse({'success': False, 'error': f'匯入過程中發生未預期的錯誤: {e}'}, status=500)