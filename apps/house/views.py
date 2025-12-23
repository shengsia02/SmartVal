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

from django.core.files.storage import default_storage # 新增這個
from django.core.files.base import ContentFile # 新增這個
from .tasks import import_excel_task # 新增這個
import base64

import os
from django.conf import settings

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



class ExcelUploadView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'account_login'

    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request):
        # 1. 檢查檔案
        if not request.FILES.get('file'):
            return JsonResponse({'success': False, 'error': '沒有上傳檔案。'}, status=400)

        excel_file = request.FILES['file']
        
        try:
            # === 修改開始：改用 Base64 傳送內容 ===
            
            # 1. 讀取檔案的二進位內容
            file_content = excel_file.read()
            
            # 2. 轉成 base64 字串 (因為 Redis 只能傳送文字，不能直接傳 binary)
            # decode('utf-8') 是為了把 bytes 轉成 string
            file_content_b64 = base64.b64encode(file_content).decode('utf-8')

            # 3. 呼叫 Celery Task
            # 注意：我們傳送的是「內容字串」，不再是「路徑」
            # 我們也把檔名傳過去，方便 logging 辨識
            task = import_excel_task.delay(file_content_b64, request.user.id, filename=excel_file.name)

            # === 修改結束 ===

            return JsonResponse({
                'success': True, 
                'task_id': task.id,
                'message': '檔案已上傳，正在後台處理中...'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'啟動任務失敗: {str(e)}'}, status=500)