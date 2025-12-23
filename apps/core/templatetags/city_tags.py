from django import template

register = template.Library()

# 定義縣市對應圖片的字典
CITY_IMAGE_MAP = {
    '臺北市': 'taipei.jpg',
    '台北市': 'taipei.jpg',
    '新北市': 'newtaipei.jpg',
    '桃園市': 'taoyuan.jpg',
    '臺中市': 'taichung.jpg',
    '台中市': 'taichung.jpg',
    '臺南市': 'tainan.jpg',
    '台南市': 'tainan.jpg',
    '高雄市': 'kaohsiung.jpg',
    '基隆市': 'keelung.jpg',
    '新竹市': 'hsinchu_city.jpg',
    '新竹縣': 'hsinchu_county.jpg',
    '苗栗縣': 'miaoli.jpg',
    '彰化縣': 'changhua.jpg',
    '南投縣': 'nantou.jpg',
    '雲林縣': 'yunlin.jpg',
    '嘉義市': 'chiayi_city.jpg',
    '嘉義縣': 'chiayi_county.jpg',
    '屏東縣': 'pingtung.jpg',
    '宜蘭縣': 'yilan.jpg',
    '花蓮縣': 'hualien.jpg',
    '臺東縣': 'taitung.jpg',
    '台東縣': 'taitung.jpg',
    '澎湖縣': 'penghu.jpg',
    '金門縣': 'kinmen.jpg',
}

@register.filter
def get_city_image(city_name):
    """
    根據縣市名稱回傳對應的圖片檔名，如果找不到則回傳預設圖
    """
    # 預設圖片 (請確保有這張圖)
    default_image = 'default.jpg'
    
    if not city_name:
        return default_image
        
    # 去除前後空白並比對字典
    return CITY_IMAGE_MAP.get(city_name.strip(), default_image)