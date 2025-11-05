from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy, reverse
from django.views.generic import View
from django.template.loader import render_to_string 
from .models import House, HouseDetail, Agent, Buyer
from .forms import HouseForm, HouseDetailForm, AgentForm, BuyerForm
from .forms import city_districts

# ==========================================
# 房屋 (House) 相關 Views
# ==========================================
# ... (HouseListView, HouseDetailView, HouseCreateView, HouseUpdateView 保持不變) ...
class HouseListView(View):
    def get(self, request):
        houses = House.objects.all().order_by('-created_at') 
        house_form = HouseForm()
        detail_form = HouseDetailForm()
        context = {
            'houses': houses,
            'total_count': houses.count(),
            'create_form': house_form,
            'create_detail_form': detail_form, 
        }
        return render(request, 'house/house_list.html', context) 

    def post(self, request):
        house_id = request.POST.get('house_id')
        house = get_object_or_404(House, pk=house_id)
        house.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponse(status=200) 
        return redirect('house:house_list')

class HouseDetailView(View):
    def get(self, request, house_id):
        house = get_object_or_404(House, id=house_id)
        context = {
            'house': house,
            'page_title': "房屋資訊", 
        }
        return render(request, 'house/house_detail.html', context)

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
                new_row_html = render_to_string(
                    'house/_house_table_row.html',
                    {'house': house},
                    request=request
                )
                return JsonResponse({'success': True, 'html': new_row_html})
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
                updated_row_html = render_to_string(
                    'house/_house_table_row.html',
                    {'house': house},
                    request=request
                )
                return JsonResponse({'success': True, 'html': updated_row_html})
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
# ... (AgentListView, AgentCreateView, AgentDetailView, AgentUpdateView 保持不變) ...
# (你提供的 views.py 中 Agent 相關的 View 已經是升級後的，保持不變即可)
class AgentListView(View):
    def get(self, request):
        agents = Agent.objects.all().order_by('name')
        form = AgentForm() 
        context = {
            'agents': agents,
            'total_count': agents.count(),
            'create_form': form, 
        }
        return render(request, 'house/agent_list.html', context)
    
    def post(self, request):
        agent_id = request.POST.get('agent_id')
        agent = get_object_or_404(Agent, pk=agent_id)
        agent.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponse(status=200)
        return redirect('house:agent_list')

class AgentCreateView(View):
    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            return redirect('house:agent_list')
        
        form = AgentForm(request.POST) 
        
        if form.is_valid():
            agent = form.save()
            new_row_html = render_to_string(
                'house/_agent_table_row.html',
                {'agent': agent},
                request=request
            )
            return JsonResponse({'success': True, 'html': new_row_html})
        else:
            context = {'form': form}
            form_html = render_to_string(
                'house/_agent_form_fields.html', 
                context, 
                request=request
            )
            return JsonResponse({'success': False, 'html': form_html})

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
            updated_row_html = render_to_string(
                'house/_agent_table_row.html',
                {'agent': agent},
                request=request
            )
            return JsonResponse({'success': True, 'html': updated_row_html})
        else:
            context = {'form': form}
            form_html = render_to_string(
                'house/_agent_form_fields.html', 
                context, 
                request=request
            )
            return JsonResponse({'success': False, 'html': form_html})

# ==========================================
# 買家 (Buyer) 相關 Views
# ==========================================

# --- 【!! 重大修改 !!】 (BuyerListView) ---
class BuyerListView(View):
    def get(self, request):
        buyers = Buyer.objects.all().order_by('name')
        # 【!! 修改 !!】 傳遞 'create_form' 供模板首次渲染
        form = BuyerForm() 
        context = {
            'buyers': buyers,
            'total_count': buyers.count(),
            'create_form': form, # <-- 傳遞空表單
        }
        return render(request, 'house/buyer_list.html', context)
    
    # ... (POST 刪除邏輯保持不變) ...
    def post(self, request):
        buyer_id = request.POST.get('buyer_id')
        buyer = get_object_or_404(Buyer, pk=buyer_id)
        buyer.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return HttpResponse(status=200)
        return redirect('house:buyer_list')

# --- 【!! 重大修改 !!】 (BuyerCreateView) ---
class BuyerCreateView(View):
    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            return redirect('house:buyer_list')
        
        form = BuyerForm(request.POST) 
        
        if form.is_valid():
            buyer = form.save()
            new_row_html = render_to_string(
                'house/_buyer_table_row.html',
                {'buyer': buyer},
                request=request
            )
            return JsonResponse({'success': True, 'html': new_row_html})
        else:
            # 【!! 修改 !!】
            # 驗證失敗，回傳 "帶有錯誤" 的表單 HTML
            # (模仿 AgentCreateView)
            context = {'form': form}
            form_html = render_to_string(
                'house/_buyer_form_fields.html', 
                context, 
                request=request
            )
            return JsonResponse({'success': False, 'html': form_html})

# ... (BuyerDetailView 保持不變) ...
class BuyerDetailView(View):
    def get(self, request, pk):
        buyer = get_object_or_404(Buyer, pk=pk)
        context = {
            'buyer': buyer,
            'page_title': "買家資訊", 
        }
        return render(request, 'house/buyer_detail.html', context)

# --- 【!! 重大新增 !!】 (BuyerUpdateView) ---
class BuyerUpdateView(View):
    """
    處理 AJAX 的買家 "編輯" 功能
    (模仿 AgentUpdateView)
    """
    def get(self, request, pk):
        # AJAX GET: 回傳 "已填入資料" 的表單 HTML
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
        # AJAX POST: 儲存 "編輯"
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if not is_ajax:
            return redirect('house:buyer_list')

        buyer = get_object_or_404(Buyer, pk=pk)
        form = BuyerForm(request.POST, instance=buyer)

        if form.is_valid():
            buyer = form.save()
            # 成功: 回傳 "更新後的" 該列 <tr> HTML
            updated_row_html = render_to_string(
                'house/_buyer_table_row.html',
                {'buyer': buyer},
                request=request
            )
            return JsonResponse({'success': True, 'html': updated_row_html})
        else:
            # 失敗: 回傳 "帶有錯誤" 的表單 HTML
            context = {'form': form}
            form_html = render_to_string(
                'house/_buyer_form_fields.html', 
                context, 
                request=request
            )
            return JsonResponse({'success': False, 'html': form_html})