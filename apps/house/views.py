from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy, reverse
from django.views.generic import View  # 只需要 View
from .models import House, HouseDetail
from .forms import HouseForm, HouseDetailForm

# Create your views here.
class IntroductionView(View):
    def get(self, request):
        context = {
            'page_title': 'AI 房屋估價系統'
        }
        return render(request, 'house/introduction.html', context)

class HouseListView(View):
    """房屋列表"""
    def get(self, request):
        houses = House.objects.all()
        context = {
            'houses': houses,
            'total_count': houses.count(),
        }
        return render(request, 'house/house_list.html', context)

    def post(self, request):
        house_id = request.POST.get('house_id')
        house = get_object_or_404(House, pk=house_id)
        house.delete()
        return redirect('house:house_list')

class HouseDetailView(View):
    """房屋詳細資訊"""
    def get(self, request, house_id):
        houses = House.objects.get(id=house_id)
        context = {
            'house': houses,
            'page_title': f"{houses.address} 的房屋詳細資訊",
        }
        return render(request, './house/house_detail.html', context)

class HouseCreateView(View):
    template_name = 'house/house_form.html'
    success_url = reverse_lazy('house:house_list')

    def get(self, request):
        # 新增模式: is_update=False (預設)
        house_form = HouseForm()
        detail_form = HouseDetailForm()
        context = {
            'page_title': '新增房屋',
            'form': house_form,
            'detail_form': detail_form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        # 新增模式: is_update=False (預設)
        house_form = HouseForm(request.POST)
        detail_form = HouseDetailForm(request.POST, request.FILES)

        if house_form.is_valid() and detail_form.is_valid():
            house = house_form.save()
            detail = detail_form.save(commit=False)
            detail.house = house
            detail.save()
            house_form.save_m2m() 
            return redirect(self.success_url)
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
        # ... (這部分程式碼不變) ...
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
        
        # 【修改】傳入 is_update=True
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
        
        # 【修改】傳入 is_update=True
        # 
        # **重要**: 
        # 因為 'disabled' 欄位不會被 POST，我們需要從 instance 重新載入它們。
        # Django 的 ModelForm 會自動處理這個問題：
        # 它會從 instance 取得 'disabled' 欄位的值，並與 POST 的資料合併。
        # 所以 'is_update=True' 在 POST 時也是必要的，
        # 這樣 Form 才知道哪些欄位是 'disabled' 且應該從 'instance' 讀取。
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