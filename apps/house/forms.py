from django import forms
from .models import House, HouseDetail, Agent, Buyer
from django.core.exceptions import ValidationError
import re

# --- 1. 台灣縣市行政區資料 (單一資料來源) ---
# ... (city_districts 字典 ... 保持不變) ...
city_districts = {
    '臺北市': [
        '中正區', '大同區', '中山區', '萬華區', '信義區', '松山區', '大安區', '南港區', '北投區', '內湖區', '士林區', '文山區'
    ],
    '新北市': [
        '板橋區', '新莊區', '泰山區', '林口區', '淡水區', '金山區', '八里區', '萬里區', '石門區', '三芝區', '瑞芳區', '汐止區', '平溪區', '貢寮區', '雙溪區', '深坑區', '石碇區', '新店區', '坪林區', '烏來區', '中和區', '永和區', '土城區', '三峽區', '樹林區', '鶯歌區', '三重區', '蘆洲區', '五股區'
    ],
    '基隆市': [
        '仁愛區', '中正區', '信義區', '中山區', '安樂區', '暖暖區', '七堵區'
    ],
    '桃園市': [
        '桃園區', '中壢區', '平鎮區', '八德區', '楊梅區', '蘆竹區', '龜山區', '龍潭區', '大溪區', '大園區', '觀音區', '新屋區', '復興區'
    ],
    '新竹縣': [
        '竹北市', '竹東鎮', '新埔鎮', '關西鎮', '峨眉鄉', '寶山鄉', '北埔鄉', '橫山鄉', '芎林鄉', '湖口鄉', '新豐鄉', '尖石鄉', '五峰鄉'
    ],
    '新竹市': [
        '東區', '北區', '香山區'
    ],
    '苗栗縣': [
        '苗栗市', '通霄鎮', '苑裡鎮', '竹南鎮', '頭份鎮', '後龍鎮', '卓蘭鎮', '西湖鄉', '頭屋鄉', '公館鄉', '銅鑼鄉', '三義鄉', '造橋鄉', '三灣鄉', '南庄鄉', '大湖鄉', '獅潭鄉', '泰安鄉'
    ],
    '臺中市': [
        '中區', '東區', '南區', '西區', '北區', '北屯區', '西屯區', '南屯區', '太平區', '大里區', '霧峰區', '烏日區', '豐原區', '后里區', '東勢區', '石岡區', '新社區', '和平區', '神岡區', '潭子區', '大雅區', '大肚區', '龍井區', '沙鹿區', '梧棲區', '清水區', '大甲區', '外埔區', '大安區'
    ],
    '南投縣': [
        '南投市', '埔里鎮', '草屯鎮', '竹山鎮', '集集鎮', '名間鄉', '鹿谷鄉', '中寮鄉', '魚池鄉', '國姓鄉', '水里鄉', '信義鄉', '仁愛鄉'
    ],
    '彰化縣': [
        '彰化市', '員林鎮', '和美鎮', '鹿港鎮', '溪湖鎮', '二林鎮', '田中鎮', '北斗鎮', '花壇鄉', '芬園鄉', '大村鄉', '永靖鄉', '伸港鄉', '線西鄉', '福興鄉', '秀水鄉', '埔心鄉', '埔鹽鄉', '大城鄉', '芳苑鄉', '竹塘鄉', '社頭鄉', '二水鄉', '田尾鄉', '埤頭鄉', '溪州鄉'
    ],
    '雲林縣': [
        '斗六市', '斗南鎮', '虎尾鎮', '西螺鎮', '土庫鎮', '北港鎮', '莿桐鄉', '林內鄉', '古坑鄉', '大埤鄉', '崙背鄉', '二崙鄉', '麥寮鄉', '臺西鄉', '東勢鄉', '褒忠鄉', '四湖鄉', '口湖鄉', '水林鄉', '元長鄉'
    ],
    '嘉義縣': [
        '太保市', '朴子市', '布袋鎮', '大林鎮', '民雄鄉', '溪口鄉', '新港鄉', '六腳鄉', '東石鄉', '義竹鄉', '鹿草鄉', '水上鄉', '中埔鄉', '竹崎鄉', '梅山鄉', '番路鄉', '大埔鄉', '阿里山鄉'
    ],
    '嘉義市': [
        '東區', '西區'
    ],
    '臺南市': [
        '中西區', '東區', '南區', '北區', '安平區', '安南區', '永康區', '歸仁區', '新化區', '左鎮區', '玉井區', '楠西區', '南化區', '仁德區', '關廟區', '龍崎區', '官田區', '麻豆區', '佳里區', '西港區', '七股區', '將軍區', '學甲區', '北門區', '新營區', '後壁區', '白河區', '東山區', '六甲區', '下營區', '柳營區', '鹽水區', '善化區', '大內區', '山上區', '新市區', '安定區'
    ],
    '高雄市': [
        '楠梓區', '左營區', '鼓山區', '三民區', '鹽埕區', '前金區', '新興區', '苓雅區', '前鎮區', '小港區', '旗津區', '鳳山區', '大寮區', '鳥松區', '林園區', '仁武區', '大樹區', '大社區', '岡山區', '路竹區', '橋頭區', '梓官區', '彌陀區', '永安區', '燕巢區', '田寮區', '阿蓮區', '茄萣區', '湖內區', '旗山區', '美濃區', '內門區', '杉林區', '甲仙區', '六龜區', '茂林區', '桃源區', '那瑪夏區'
    ],
    '屏東縣': [
        '屏東市', '潮州鎮', '東港鎮', '恆春鎮', '萬丹鄉', '長治鄉', '麟洛鄉', '九如鄉', '里港鄉', '鹽埔鄉', '高樹鄉', '萬巒鄉', '內埔鄉', '竹田鄉', '新埤鄉', '枋寮鄉', '新園鄉', '崁頂鄉', '林邊鄉', '南州鄉', '佳冬鄉', '琉球鄉', '車城鄉', '滿州鄉', '枋山鄉', '霧台鄉', '瑪家鄉', '泰武鄉', '來義鄉', '春日鄉', '獅子鄉', '牡丹鄉', '三地門鄉'
    ],
    '宜蘭縣': [
        '宜蘭市', '羅東鎮', '蘇澳鎮', '頭城鎮', '礁溪鄉', '壯圍鄉', '員山鄉', '冬山鄉', '五結鄉', '三星鄉', '大同鄉', '南澳鄉'
    ],
    '花蓮縣': [
        '花蓮市', '鳳林鎮', '玉里鎮', '新城鄉', '吉安鄉', '壽豐鄉', '秀林鄉', '光復鄉', '豐濱鄉', '瑞穗鄉', '萬榮鄉', '富里鄉', '卓溪鄉'
    ],
    '臺東縣': [
        '臺東市', '成功鎮', '關山鎮', '長濱鄉', '海端鄉', '池上鄉', '東河鄉', '鹿野鄉', '延平鄉', '卑南鄉', '金峰鄉', '大武鄉', '達仁鄉', '綠島鄉', '蘭嶼鄉', '太麻里鄉'
    ],
    '澎湖縣': [
        '馬公市', '湖西鄉', '白沙鄉', '西嶼鄉', '望安鄉', '七美鄉'
    ],
    '金門縣': [
        '金城鎮', '金湖鎮', '金沙鎮', '金寧鄉', '烈嶼鄉', '烏坵鄉'
    ],
    '連江縣': [
        '南竿鄉', '北竿鄉', '莒光鄉', '東引鄉'
    ]
}

# --- 2. 動態產生 Choices ---
HOUSE_TYPE_CHOICES = [
    ("", "請選擇房屋類型"),
    ("大樓", "大樓"),
    ("公寓", "公寓"),
    ("透天", "透天"),
]

HOUSE_CITY_CHOICES = [("", "請選擇房屋所在縣市")] + [(city, city) for city in city_districts.keys()]
AGENT_CITY_CHOICES = [("", "請選擇分行所在縣市")] + [(city, city) for city in city_districts.keys()]


# --- 3. 通用的 CSS 樣式 (保持不變) ---
default_attrs = {'class': 'mt-2 p-2 w-full border rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500'}
select_attrs = {
    'class': 'mt-2 p-2 w-full border rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 text-gray-500 valid:text-black'
}
# 【!! 修改 !!】 移除 'disabled': True，因為我們改用 Django 的 field.disabled
disabled_style_attrs = {
    'class': 'mt-2 p-2 w-full border rounded-lg shadow-sm bg-slate-100 text-slate-500 cursor-not-allowed'
}

# --- 4. HouseForm (修改 __init__) ---
class HouseForm(forms.ModelForm):
    house_type = forms.ChoiceField(
        choices=HOUSE_TYPE_CHOICES,
        required=True,
        error_messages={'required': '請選擇房屋類型'},
        widget=forms.Select(attrs=select_attrs)
    )
    total_price = forms.IntegerField(
        required=True,
        error_messages={
            'required': '請輸入房屋總價',
            'invalid': '房屋總價必須是數字'
        },
        widget=forms.NumberInput(attrs={
            **default_attrs,
            'placeholder': '請輸入房屋總價',
        })
    )
    class Meta:
        model = House
        fields = ['address', 'house_type', 'total_price', 'agent', 'buyers']
        widgets = {
            'address': forms.TextInput(attrs={**default_attrs, 'placeholder': '請輸入地址'}),
            'agent':  forms.Select(attrs=select_attrs),
            'buyers': forms.Select(attrs=select_attrs),
        }
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
    def __init__(self, *args, **kwargs):
        is_update = kwargs.pop('is_update', False)
        super().__init__(*args, **kwargs)
        self.fields['agent'].required = True
        self.fields['buyers'].required = True
        if not self.instance.pk or not self.instance.agent:
            self.fields['agent'].empty_label = "請選擇房屋仲介"
        if not self.instance.pk or not self.instance.buyers:
            self.fields['buyers'].empty_label = "請選擇買家"
            
        if is_update:
            fields_to_disable = ['address', 'house_type', 'agent', 'buyers']
            for name in fields_to_disable:
                if name in self.fields:
                    # 【!! 關鍵修正 !!】
                    # 使用 Django 的欄位屬性 .disabled，而不是修改 widget.attrs
                    self.fields[name].disabled = True
                    self.fields[name].widget.attrs.update(disabled_style_attrs)


# --- 5. HouseDetailForm (修改 __init__) ---
class HouseDetailForm(forms.ModelForm):
    city = forms.ChoiceField(
        choices=HOUSE_CITY_CHOICES,
        required=True,
        error_messages={'required': '請選擇房屋所在縣市'},
        widget=forms.Select(attrs=select_attrs)
    )
    town = forms.ChoiceField(
        choices=[("", "請先選擇房屋所在縣市")], 
        required=True,
        error_messages={'required': '請選擇房屋所在行政區'},
        widget=forms.Select(attrs=select_attrs)
    )
    house_age = forms.DecimalField(
        required=True, max_digits=10, decimal_places=2,
        error_messages={'required': '請輸入屋齡', 'invalid': '屋齡必須是數字'},
        widget=forms.NumberInput(attrs={**default_attrs, 'placeholder': '請輸入屋齡', 'step': '0.01'})
    )
    floor_area = forms.DecimalField(
        required=True, max_digits=10, decimal_places=2,
        error_messages={'required': '請輸入建坪', 'invalid': '建坪必須是數字'},
        widget=forms.NumberInput(attrs={**default_attrs, 'placeholder': '請輸入建坪', 'step': '0.01'})
    )
    land_area = forms.DecimalField(
        required=True, max_digits=10, decimal_places=2,
        error_messages={'required': '請輸入地坪', 'invalid': '地坪必須是數字'},
        widget=forms.NumberInput(attrs={**default_attrs, 'placeholder': '請輸入地坪', 'step': '0.01'})
    )
    unit_price = forms.DecimalField(
        required=True, max_digits=10, decimal_places=2,
        error_messages={'required': '請輸入單價', 'invalid': '單價必須是數字'},
        widget=forms.NumberInput(attrs={**default_attrs, 'placeholder': '請輸入單價 (萬/坪)', 'step': '0.01'})
    )
    class Meta:
        model = HouseDetail
        fields = [
            'city', 'town', 'house_age', 'floor_area', 'land_area', 
            'unit_price', 'sold_time', 'house_image'
        ]
        widgets = {
            'sold_time': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    **default_attrs,
                    'type': 'text',
                    'placeholder': '請選擇出售日期'
                }
            ),
            'house_image': forms.ClearableFileInput(
                attrs={'class': 'mt-2 p-2 w-full border rounded-lg'}
            ),
        }
        error_messages = {
            'sold_time': {
                'required': '請選擇出售日期',
                'invalid': '請輸入有效的日期格式 (YYYY-MM-DD)'
            }
        }
    def __init__(self, *args, **kwargs):
        is_update = kwargs.pop('is_update', False)
        super().__init__(*args, **kwargs)
        
        selected_city = None
        if 'city' in self.data:
            try:
                selected_city = self.data.get('city')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.city:
            selected_city = self.instance.city
            
        if selected_city:
            town_choices = [(town, town) for town in city_districts.get(selected_city, [])]
            self.fields['town'].choices = [("", "請選擇房屋所在行政區")] + town_choices
        else:
            self.fields['town'].choices = [("", "請先選擇房屋所在縣市")]
            
        if is_update:
            fields_to_disable = ['city', 'town', 'sold_time']
            for field_name in fields_to_disable:
                if field_name in self.fields:
                    # 【!! 關鍵修正 !!】
                    # 使用 Django 的欄位屬性 .disabled，而不是修改 widget.attrs
                    self.fields[field_name].disabled = True
                    self.fields[field_name].widget.attrs.update(disabled_style_attrs)

# --- 6. AgentForm (遵循選項 B) ---
class AgentForm(forms.ModelForm):
    city = forms.ChoiceField(
        choices=AGENT_CITY_CHOICES,
        required=True,
        error_messages={'required': '請選擇分行所在縣市'},
        widget=forms.Select(attrs=select_attrs)
    )
    town = forms.ChoiceField(
        choices=[("", "請先選擇分行所在縣市")], 
        required=True,
        error_messages={'required': '請選擇分行所在行政區'},
        widget=forms.Select(attrs=select_attrs)
    )
    phone = forms.CharField(
        required=True, 
        error_messages={'required': '請輸入聯絡電話'}, 
        widget=forms.TextInput(attrs={**default_attrs, 'placeholder': '例如：0912-345-678'})
    )
    email = forms.EmailField(
        required=True, 
        error_messages={'required': '請輸入電子郵件'}, 
        widget=forms.EmailInput(attrs={**default_attrs, 'placeholder': '例如：agent@example.com'})
    )
    company = forms.CharField(
        required=True, 
        error_messages={'required': '請輸入隸屬品牌'}, 
        widget=forms.TextInput(attrs={**default_attrs, 'placeholder': '例如：信義房屋'})
    )
    branch = forms.CharField(
        required=True, 
        error_messages={'required': '請輸入分行名稱'}, 
        widget=forms.TextInput(attrs={**default_attrs, 'placeholder': '例如：大安店'})
    )

    class Meta:
        model = Agent
        fields = ['name', 'phone', 'email', 'company', 'branch', 'city', 'town']
        widgets = {
            'name': forms.TextInput(attrs={
                **default_attrs, 
                'placeholder': '請輸入仲介姓名'
            }),
        }
        error_messages = {
            'name': {
                'required': '請輸入仲介姓名',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected_city = None
        if 'city' in self.data:
            try:
                selected_city = self.data.get('city')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.city:
            selected_city = self.instance.city
        if selected_city:
            town_choices = [(town, town) for town in city_districts.get(selected_city, [])]
            self.fields['town'].choices = [("", "請選擇分行所在行政區")] + town_choices
        else:
            self.fields['town'].choices = [("", "請先選擇分行所在縣市")]

# --- 7. BuyerForm (遵循選項 B) ---
class BuyerForm(forms.ModelForm):
    phone = forms.CharField(
        required=True, 
        error_messages={'required': '請輸入聯絡電話'}, 
        widget=forms.TextInput(attrs={**default_attrs, 'placeholder': '例如：0988-123-456'})
    )
    email = forms.EmailField(
        required=True, 
        error_messages={'required': '請輸入電子郵件'}, 
        widget=forms.EmailInput(attrs={**default_attrs, 'placeholder': '例如：buyer@example.com'})
    )

    class Meta:
        model = Buyer
        fields = ['name', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                **default_attrs, 
                'placeholder': '請輸入買家姓名'
            }),
        }
        error_messages = {
            'name': {
                'required': '請輸入買家姓名',
            },
        }