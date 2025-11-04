from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy, reverse
from django.views.generic import View
# 【新增】用於在 View 中渲染模板片段
from django.template.loader import render_to_string 
from .models import House, HouseDetail
from .forms import HouseForm, HouseDetailForm
from .forms import city_districts

# Create your views here.
class IntroductionView(View):
    def get(self, request):
        context = {
            'page_title': 'AI 房屋估價系統'
        }
        return render(request, 'house/introduction.html', context)

class HouseListView(View):
    # 【修改】GET 方法
    def get(self, request):
        houses = House.objects.all().order_by('-created_at') # 讓最新的在最上面
        
        # 【新增】為 Modal 提供空的表單
        house_form = HouseForm()
        detail_form = HouseDetailForm()
        
        context = {
            'houses': houses,
            'total_count': houses.count(),
            'form': house_form,         # 傳遞空表單
            'detail_form': detail_form, # 傳遞空表單
        }
        return render(request, 'house/house_list.html', context) #

    # ... (POST 用於刪除，保持不變) ...
    def post(self, request):
        house_id = request.POST.get('house_id')
        house = get_object_or_404(House, pk=house_id)
        house.delete()
        return redirect('house:house_list')

class HouseDetailView(View):
    # ... (保持不變) ...
    def get(self, request, house_id):
        houses = House.objects.get(id=house_id)
        context = {
            'house': houses,
            'page_title': f"{houses.address} 的房屋詳細資訊",
        }
        return render(request, './house/house_detail.html', context)

class HouseCreateView(View):
    # 【修改】 template_name 不再是主要回傳方式
    template_name = 'house/house_form.html' #
    success_url = reverse_lazy('house:house_list')

    # 【修改】GET 請求現在會直接導向列表頁（因為表單在列表頁的 Modal 中）
    def get(self, request):
        # return render(request, self.template_name, context)
        # 【修改】直接導向列表頁，Modal 會在那裡被渲染
        return redirect(self.success_url)

    # 【重大修改】POST 方法
    def post(self, request):
        # 檢查是否為 AJAX 請求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        house_form = HouseForm(request.POST)
        detail_form = HouseDetailForm(request.POST, request.FILES) 

        if house_form.is_valid() and detail_form.is_valid():
            house = house_form.save()
            detail = detail_form.save(commit=False)
            detail.house = house
            detail.save()
            house_form.save_m2m() 
            
            if is_ajax:
                # 【AJAX 成功】
                # 1. 渲染新的表格橫列 (<tr>...</tr>)
                new_row_html = render_to_string(
                    'house/_house_table_row.html',
                    {'house': house},
                    request=request
                )
                # 2. 回傳 JSON
                return JsonResponse({'success': True, 'house_html': new_row_html})
            else:
                # 【非 AJAX 成功】（舊的備用行為）
                return redirect(self.success_url)
        else:
            # 【表單驗證失敗】
            if is_ajax:
                # 合併兩個表單的錯誤
                errors = {**house_form.errors, **detail_form.errors}
                return JsonResponse({'success': False, 'errors': errors})
            else:
                # 【非 AJAX 失敗】（舊的備用行為）
                # 重新渲染帶有錯誤的頁面
                context = {
                    'page_title': '新增房屋',
                    'form': house_form,
                    'detail_form': detail_form,
                }
                # 注意：我們必須返回 'house_form.html' 而不是 'house_list.html'
                # 因為 'house_list.html' 的 POST 是用於刪除
                return render(request, self.template_name, context)


class HouseUpdateView(View):
    # ... (保持不變，UpdateView 仍然使用 house_form.html 頁面) ...
    template_name = 'house/house_form.html' #
    success_url = reverse_lazy('house:house_list')

    def get_object_and_detail(self, pk):
        house = get_object_or_404(House, pk=pk)
        default_values = {
            'house_age': 0, 'floor_area': 0.01, 'land_area': 0.01, 'unit_price': 0.01
        }
        detail, created = HouseDetail.objects.get_or_create(
            house=house, 
            defaults=default_values
        )
        return house, detail

    def get(self, request, pk):
        house, detail = self.get_object_and_detail(pk)
        
        house_form = HouseForm(instance=house, is_update=True)
        detail_form = HouseDetailForm(instance=detail, is_update=True)

        context = {
            'page_title': f'編輯 {house.address} 的房屋資料',
            'form': house_form,
            'detail_form': detail_form,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        house, detail = self.get_object_and_detail(pk)
        
        house_form = HouseForm(request.POST, instance=house, is_update=True)
        detail_form = HouseDetailForm(request.POST, request.FILES, instance=detail, is_update=True)

        if house_form.is_valid() and detail_form.is_valid():
            house_form.save()
            detail_form.save()
            return redirect(self.success_url)
        else:
            context = {
                'page_title': f'編輯 {house.address} 的房屋資料',
                'form': house_form,
                'detail_form': detail_form,
            }
            return render(request, self.template_name, context)


def load_towns(request):
    # ... (保持不變) ...
    city = request.GET.get('city')
    towns = city_districts.get(city, [])
    return JsonResponse({'towns': towns})