import os, re
import joblib
import pandas as pd
import numpy as np
from django.conf import settings
from geopy.geocoders import Nominatim # 免費的地理編碼服務 (OpenStreetMap)
from geopy.distance import geodesic # 【新增】用於計算距離
from apps.house.models import House # 【新增】引入房屋模型

class HousePriceService:
    _model = None
    _geolocator = None

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            # 讀取您訓練好的最佳模型 (請確認檔名是否一致)
            model_path = os.path.join(settings.BASE_DIR, 'apps/core/ml_models/smartval_model.pkl')
            try:
                cls._model = joblib.load(model_path)
            except Exception as e:
                print(f"❌ 模型載入失敗: {e}")
                return None
        return cls._model

    @classmethod
    def _get_geolocator(cls):
        """初始化地理編碼器"""
        if cls._geolocator is None:
            # user_agent 必須設定，建議用您的專案名稱
            cls._geolocator = Nominatim(user_agent="smartval_app")
        return cls._geolocator

    @classmethod
    def _get_lat_lon(cls, city, town, street):
        """
        將地址轉換為經緯度 (三層式 Fallback 機制)
        """
        geolocator = cls._get_geolocator()
        
        # 組合原始完整地址
        full_address = f"{city}{town}{street}"
        
        # 處理路名：使用 Regex 去除門牌號碼 (例如 "信義路三段147號" -> "信義路三段")
        # 邏輯：抓取 "路"、"街"、"道"、"段" 之後的數字+號，並將其移除
        # 簡單版：直接把數字和 '號' 拿掉，保留路名和段數
        street_only = re.sub(r'\d+號.*', '', street) # 去掉 "123號" 後面的所有東西
        street_only = re.sub(r'\d+樓.*', '', street_only) # 去掉 "5樓" 
        
        # 定義嘗試順序 (由精細到寬鬆)
        search_queries = [
            # 1. 第一層：嘗試完整地址 (雖然 OSM 常失敗，但還是試試)
            f"{city}{town}{street}", 
            
            # 2. 第二層：【關鍵】只查 "路名+段數" (根據你的截圖，這層成功率很高)
            f"{city}{town}{street_only}",
            
            # 3. 第三層：只查 "行政區" (最後手段，雖然不準但比報錯好)
            f"{city}{town}" 
        ]

        for query in search_queries:
            if not query: continue 
            try:
                # 加上 Taiwan 限制範圍
                # timeout 設為 3 秒即可，太久會卡住使用者體驗
                location = geolocator.geocode(f"{query}, Taiwan", timeout=3)
                
                if location:
                    # 為了 Debug 方便，你可以印出來看是哪一層成功的
                    # print(f"📍 Geocode 成功 ({query}): {location.latitude}, {location.longitude}")
                    return location.longitude, location.latitude
                    
            except Exception as e:
                # 這裡不需要 print error，因為失敗我們會試下一個
                continue

        # 真的全部失敗 (連行政區都找不到)，回傳預設值 (台北市中心)
        print(f"⚠️ 全部 Geocode 失敗: {full_address}")
        return 121.5, 25.0
    
    # 【新增】尋找最近的房屋邏輯
    @classmethod
    def find_nearby_houses(cls, target_lat, target_lon, city, limit=10):
        """
        找出同縣市中，距離目標經緯度最近的房屋
        """
        try:
            # 1. 先篩選同縣市 (大幅減少計算量)
            # 使用 select_related 優化查詢 (如果需要 agent 資訊)
            candidates = House.objects.filter(city=city).values(
                'id', 'address', 'total_price', 'house_type', 
                'house_age', 'floor_area', 'latitude', 'longitude'
            )
            
            print(f"🔍 [find_nearby_houses] 搜尋 {city} 的房屋，總共找到 {candidates.count()} 筆")

            # 2. 計算距離並排序
            # 注意：這裡使用 Python 列表推導式計算距離，適合資料量不大(幾千筆)的情況
            # 如果資料量有幾十萬筆，建議改用 PostGIS 資料庫層級搜尋
            
            nearby_list = []
            target_point = (target_lat, target_lon)

            for house in candidates:
                # 略過沒有經緯度的資料
                if not house['latitude'] or not house['longitude']:
                    continue
                
                house_point = (house['latitude'], house['longitude'])
                
                # 計算距離 (單位: 公里)
                dist = geodesic(target_point, house_point).km
                
                # 整理要回傳給前端的資料格式
                house_data = {
                    'address': house['address'],
                    'price': house['total_price'],
                    'type': house['house_type'],
                    'age': house['house_age'],
                    'area': house['floor_area'],
                    'lat': float(house['latitude']),
                    'lng': float(house['longitude']),
                    'distance_km': round(dist, 2)
                }
                nearby_list.append(house_data)

            # 3. 依照距離排序 (由近到遠)，取前 limit 筆
            nearby_list.sort(key=lambda x: x['distance_km'])
            result = nearby_list[:limit]
            
            print(f"✅ [find_nearby_houses] 處理完成: 有效房屋 {len(nearby_list)} 筆，回傳 {len(result)} 筆")
            if len(result) > 0:
                print(f"   最近距離: {result[0]['distance_km']} km, 最遠距離: {result[-1]['distance_km']} km")
            
            return result

        except Exception as e:
            print(f"尋找周邊房屋失敗: {e}")
            return []

    @classmethod
    def predict(cls, input_data: dict):
        """
        接收前端傳來的 cleaned_data，進行特徵工程並預測
        """
        model = cls._get_model()
        if model is None:
            return None

        try:
            # --- 1. 準備基礎資料 ---
            # 假設 input_data 包含: city, town, street, floor_number, total_floors, 
            # building_type, land_area, floor_area, age, room_count
            
            # 先把變數提取出來
            city = str(input_data.get('city', ''))
            town = str(input_data.get('town', ''))
            street = str(input_data.get('street', ''))

            # 【修正】傳入三個參數 (city, town, street)
            longitude, latitude = cls._get_lat_lon(city, town, street)

            # --- 2. 建立 DataFrame (欄位名稱必須與訓練時完全一致) ---
            data_dict = {
                '縣市': [str(input_data.get('city'))],
                '行政區': [str(input_data.get('town'))],
                '建物類型': [str(input_data.get('house_type'))], # 注意前端欄位名稱對應
                '所在層數': [str(input_data.get('floor_number'))], # 訓練時轉為 str，這裡也要轉
                '地上總層數': [str(input_data.get('total_floors'))], # 訓練時轉為 str
                '地坪': [float(input_data.get('land_area', 0))],
                '建坪': [float(input_data.get('floor_area', 0))], # 假設前端叫 building_area
                '屋齡（年）': [float(input_data.get('house_age', 0))],
                '房間數': [float(input_data.get('room_count', 0))], # 您提到的新增欄位
                '經度': [float(longitude)],
                '緯度': [float(latitude)],
                # '樓層比' 會在下面計算，這裡先不用填
            }
            
            df = pd.DataFrame(data_dict)

            # --- 3. 重現特徵工程 (Feature Engineering) ---
            # 這是您問題1的核心：必須在 Service 層重做這些計算
            
            # 計算樓層比
            try:
                current_floor = float(input_data.get('floor_number', 0))
                total_floors = float(input_data.get('total_floors', 1))
                floor_ratio = current_floor / total_floors if total_floors > 0 else 0
                
                # 限制上限為 1.0 (與訓練邏輯一致)
                if floor_ratio > 1.0:
                    floor_ratio = 1.0
            except:
                floor_ratio = 0.0
            
            df['樓層比'] = floor_ratio

            # --- 4. 預測 ---
            # 注意：您的訓練目標變數做了 log1p 轉換 (y_log_train = np.log1p(...))
            # 所以模型預測出來的是 log 價格，必須轉回來
            log_prediction = model.predict(df)
            real_price = np.expm1(log_prediction)[0]
            predicted_price = round(float(real_price), 2)
            
            # 【新增】5. 搜尋周邊實價登錄行情
            nearby_houses = cls.find_nearby_houses(latitude, longitude, city)

            # 【修改】回傳值多加一個 'nearby_houses' 與 'target_coords'
            return {
                'price': predicted_price,
                'nearby_houses': nearby_houses,
                'target_coords': {'lat': latitude, 'lng': longitude}
            }

        except Exception as e:
            import traceback
            print(f"預測錯誤: {e}")
            print(traceback.format_exc())
            return None