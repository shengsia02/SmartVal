from django import forms
from .models import House, HouseDetail
from django.core.exceptions import ValidationError
import re

# --- 1. 定義選項 (Choices) ---
# (你沒有貼上列表，我先用範例代替)
HOUSE_TYPE_CHOICES = [
    ("", "請選擇房屋類型"), # 這是你的 placeholder
    ("大樓", "大樓"),
    ("公寓", "公寓"),
    ("透天", "透天"),
]

# (這只是範例，你需要貼上你的完整列表)
CITY_CHOICES = [
    ("", "請選擇房屋所在縣市"),
    ("台北市", "台北市"),
    ("新北市", "新北市"),
]

# (這只是範例，未來需要用 JavaScript 動態載入)
TOWN_CHOICES = [
    ("", "請選擇房屋所在行政區"),
    ("大安區", "大安區 (台北市)"),
    ("信義區", "信義區 (台北市)"),
    ("板橋區", "板橋區 (新北市)"),
    ("三峽區", "三峽區 (新北市)"),
]

# --- 2. 通用的 CSS 樣式 ---
default_attrs = {'class': 'mt-2 p-2 w-full border rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500'}

# 【新增】這是下拉選單專用的樣式
select_attrs = {
    'class': 'mt-2 p-2 w-full border rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-500 valid:text-black'
}
# 說明:
# text-gray-500: 預設文字為灰色
# valid:text-black: 當選中一個有效值 (非空值) 時，文字變為黑色

readonly_attrs = {
    'class': 'mt-2 p-2 w-full border rounded-lg shadow-sm bg-slate-100 text-slate-500 cursor-not-allowed',
    'readonly': True
}

# --- 3. 更新 HouseForm ---

class HouseForm(forms.ModelForm):
    # 房屋類型: 套用 select_attrs
    house_type = forms.ChoiceField(
        choices=HOUSE_TYPE_CHOICES,
        required=True,
        error_messages={'required': '請選擇房屋類型'},
        widget=forms.Select(attrs=select_attrs) # 【修改】
    )

    # 3. 總價: 改成 IntegerField，並加入 placeholder 和錯誤訊息
    total_price = forms.IntegerField(
        required=True,
        error_messages={
            'required': '請輸入房屋總價',
            'invalid': '房屋總價必須是數字' # 'invalid' 會捕捉所有非數字輸入
        },
        widget=forms.NumberInput(attrs={
            **default_attrs, # 合併 default_attrs
            'placeholder': '請輸入房屋總價',
        })
    )

    class Meta:
        model = House
        fields = ['address', 'house_type', 'total_price', 'agent', 'buyers']
        
        widgets = {
            'address': forms.TextInput(attrs={
                **default_attrs,
                'placeholder': '請輸入地址'
            }),
            
            # 房屋中介: 套用 select_attrs
            'agent': forms.Select(attrs=select_attrs), # 【修改】
            
            # 買家: 【修改】改成 forms.Select 並套用 select_attrs
            'buyers': forms.Select(attrs=select_attrs), 
        }
        
        # 綁定欄位和錯誤訊息
        error_messages = {
            'address': {
                'required': '請輸入地址',
            },
            'agent': {
                'required': '請選擇房屋仲介',
            },
            'buyers': {
                'required': '請選擇買家',
            },
        }

    # 處理「編輯模式」和「placeholder」
    def __init__(self, *args, **kwargs):
        is_update = kwargs.pop('is_update', False) 
        super().__init__(*args, **kwargs)
        
        # 為 agent 和 buyers 加入 "請選擇..." 的 placeholder
        if not self.instance.pk or not self.instance.agent:
             self.fields['agent'].empty_label = "請選擇房屋仲介"
        
        # 【新增】為 buyers 加入 empty_label
        if not self.instance.pk or not self.instance.buyers:
             self.fields['buyers'].empty_label = "請選擇買家"

        if is_update:
            # ... (唯讀設定保持不變) ...
            fields_to_disable = ['address', 'house_type', 'agent', 'buyers'] # 【修改】
            for field_name in fields_to_disable:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs.update(readonly_attrs)
                    self.fields[field_name].widget.attrs['disabled'] = True


# --- 4. 更新 HouseDetailForm ---

class HouseDetailForm(forms.ModelForm):
    # 縣市: 套用 select_attrs
    city = forms.ChoiceField(
        choices=CITY_CHOICES,
        required=True,
        error_messages={'required': '請選擇房屋所在縣市'},
        widget=forms.Select(attrs=select_attrs) # 【修改】
    )

    # 行政區: 套用 select_attrs
    town = forms.ChoiceField(
        choices=TOWN_CHOICES, 
        required=True,
        error_messages={'required': '請選擇房屋所在行政區'},
        widget=forms.Select(attrs=select_attrs) # 【修改】
    )

    # 8. 數字欄位 (小數)
    house_age = forms.DecimalField(
        required=True, max_digits=10, decimal_places=2,
        error_messages={'required': '請輸入屋齡', 'invalid': '屋齡必須是數字'},
        widget=forms.NumberInput(attrs={
            **default_attrs, 
            'placeholder': '請輸入屋齡', 
            'step': '0.01'
        })
    )
    floor_area = forms.DecimalField(
        required=True, max_digits=10, decimal_places=2,
        error_messages={'required': '請輸入建坪', 'invalid': '建坪必須是數字'},
        widget=forms.NumberInput(attrs={
            **default_attrs, 
            'placeholder': '請輸入建坪', 
            'step': '0.01'
        })
    )
    land_area = forms.DecimalField(
        required=True, max_digits=10, decimal_places=2,
        error_messages={'required': '請輸入地坪', 'invalid': '地坪必須是數字'},
        widget=forms.NumberInput(attrs={
            **default_attrs, 
            'placeholder': '請輸入地坪', 
            'step': '0.01'
        })
    )
    unit_price = forms.DecimalField(
        required=True, max_digits=10, decimal_places=2,
        error_messages={'required': '請輸入單價', 'invalid': '單價必須是數字'},
        widget=forms.NumberInput(attrs={
            **default_attrs, 
            'placeholder': '請輸入單價 (萬/坪)', 
            'step': '0.01'
        })
    )

    class Meta:
        model = HouseDetail
        fields = [
            'city', 'town', 'house_age', 'floor_area', 'land_area', 
            'unit_price', 'sold_time', 'description', 'house_image'
        ]
        widgets = {
            # 9. 出售日期
            'sold_time': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    **default_attrs,
                    'type': 'date',
                    'placeholder': '請選擇出售日期' # 注意: type='date' 的 placeholder 效果不一
                }
            ),
            # 10. 房屋簡介
            'description': forms.Textarea(
                attrs={
                    **default_attrs,
                    'rows': 4,
                    # w-1/2 會在 n*2 排版時自動實現
                }
            ),
            'house_image': forms.ClearableFileInput(
                attrs={'class': 'mt-2 p-2 w-full border rounded-lg'}
            ),
        }
        # 9. 出售日期
        error_messages = {
            'sold_time': {
                'required': '請選擇出售日期',
                'invalid': '請輸入有效的日期格式 (YYYY-MM-DD)'
            }
        }

    # 6. 處理「編輯模式 (唯讀)」
    def __init__(self, *args, **kwargs):
        is_update = kwargs.pop('is_update', False)
        super().__init__(*args, **kwargs)

        if is_update:
            # 6. & 7. 縣市/行政區 設定為唯讀
            fields_to_disable = ['city', 'town']
            for field_name in fields_to_disable:
                if field_name in self.fields:
                    self.fields[field_name].widget.attrs.update(readonly_attrs)
                    self.fields[field_name].widget.attrs['disabled'] = True