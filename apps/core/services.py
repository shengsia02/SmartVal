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
        將地址轉換為經緯度 (嚴格模式)
        """
        geolocator = cls._get_geolocator()
        
        # 1. 處理地址字串
        # 我們只去掉「樓層」相關資訊，保留「路名」與「門牌號碼」
        # 例如: "大德路151號12樓" -> "大德路151號"
        clean_street = re.sub(r'\d+[樓Ff].*', '', street) 
        
        # 組合完整地址
        full_address = f"{city}{town}{clean_street}"

        # 定義驗證函式：檢查回傳的地址是否包含目標縣市
        def is_city_match(location, target_city):
            if not location:
                return False
            # 處理「台」與「臺」的通用問題 (Nominatim 通常用 '臺')
            target_city_std = target_city.replace('台', '臺')
            result_address_std = location.address.replace('台', '臺')
            
            # 檢查縣市名稱是否在回傳的地址中
            if target_city_std in result_address_std:
                return True
            
            # 特殊情況：有時候 Nominatim 只有 "Keelung", "Taipei" 等英文或簡寫
            # 這裡做一個簡單的 Log 警告，方便除錯
            print(f"⚠️ [定位縣市不符] 目標: {target_city}, 找到: {location.address}")
            return False
        
        # --- 嘗試 1：精確搜尋 (包含門牌號碼) ---
        try:
            # timeout 設為 3 秒
            location = geolocator.geocode(f"{full_address}, Taiwan", timeout=3)
            if location:
                # 找到了！回傳座標，並標記 is_exact = True
                return location.longitude, location.latitude, True 
        except Exception:
            pass # 失敗就繼續往下試

        # --- 嘗試 2：退一步搜尋路名 (去除號碼) ---
        # 邏輯：去掉 "數字+號" 及其後面的所有內容
        # 例如 "大德路157號" -> "大德路"
        road_only = re.sub(r'\d+號.*', '', clean_street)
        road_address = f"{city}{town}{road_only}"
        
        # 避免 regex 刪過頭變空字串 (防呆)
        if road_only and road_only != clean_street:
            try:
                print(f"⚠️ 精確定位失敗，嘗試路名定位: {road_address}")
                location = geolocator.geocode(f"{road_address}, Taiwan", timeout=3)
                if location and is_city_match(location, city):
                    return location.longitude, location.latitude, False
            except Exception:
                pass

        # --- 3. 真的全部失敗 ---
        print(f"⚠️ 全部 Geocode 失敗: {full_address}")
        return None, None, False
    
    # 【修改】擴充參數，接收所有篩選條件
    @classmethod
    def find_nearby_houses(cls, target_lat, target_lon, criteria, limit=10):
        """
        找出符合條件且距離最近的房屋
        
        Args:
            target_lat (float): 目標緯度
            target_lon (float): 目標經度
            criteria (dict): 篩選條件字典 (包含 city, house_type, age 等)
            limit (int): 回傳筆數
        """
        try:
            city = criteria.get('city')
            
            # 【調試】印出搜尋條件
            print(f"🔍 [DEBUG] 搜尋條件: {criteria}")
            
            # 1. 執行篩選 (Database Filtering)
            # 使用 Django ORM 的 range 查詢，這是在資料庫層級做的，效能最好
            
            # 【修正】確保範圍值不會是負數
            room_count = float(criteria.get('room_count', 0))
            house_age = float(criteria.get('house_age', 0))
            total_floors = float(criteria.get('total_floors', 0))
            floor_number = float(criteria.get('floor_number', 0))
            floor_area = float(criteria.get('floor_area', 0))
            land_area = float(criteria.get('land_area', 0))
            
            candidates = House.objects.filter(
                city=city, # 基本條件：同縣市
                
                # 條件 1: 房屋類型一樣
                house_type=criteria.get('house_type'),
                
                # 條件 7: 房間數一樣
                room_count=criteria.get('room_count'),
                
                # 條件 2: 屋齡 ±5 年
                house_age__range=(
                    max(0, house_age - 5), 
                    house_age + 5
                ),
                
                # 條件 3: 總樓層 ±5 層
                total_floors__range=(
                    max(1, total_floors - 5), 
                    total_floors + 5
                ),
                
                # 條件 4: 所在樓層 ±5 層
                floor_number__range=(
                    max(1, floor_number - 5), 
                    floor_number + 5
                ),
                
                # 條件 5: 建坪 ±20 坪
                floor_area__range=(
                    max(0, floor_area - 10), 
                    floor_area + 10
                ),
                
                # 條件 6: 地坪 ±10 坪
                land_area__range=(
                    max(0, land_area - 5), 
                    land_area + 5
                )
            ).exclude(
                # 排除經緯度為 NULL 的資料
                latitude__isnull=True
            ).exclude(
                longitude__isnull=True
            ).values(
                'id', 'address', 'total_price', 'house_type', 
                'house_age', 'floor_area', 'latitude', 'longitude'
            )
            
            print(f"🔍 [find_nearby_houses] 嚴格篩選後，找到 {candidates.count()} 筆房屋")
            
            # 【調試】印出前3筆資料看看
            for i, house in enumerate(list(candidates)[:3]):
                print(f"  房屋 {i+1}: {house['address']}, 經緯度: ({house['latitude']}, {house['longitude']})")

            # --- 退路機制 (Fallback) ---
            # 如果嚴格篩選找不到足夠資料 (例如少於 5 筆)，自動放寬條件
            # 這是為了避免地圖上空空如也，讓使用者體驗變差
            if candidates.count() < 5:
                print("⚠️ 符合條件的房屋過少，改為寬鬆模式 (僅看類型與屋齡範圍)")
                candidates = House.objects.filter(
                    city=city,
                    house_type=criteria.get('house_type'),
                    # 屋齡放寬到 ±10 年
                    house_age__range=(
                        max(0, house_age - 10), 
                        house_age + 10
                    )
                    # 移除其他嚴格限制
                ).exclude(
                    latitude__isnull=True
                ).exclude(
                    longitude__isnull=True
                ).values(
                    'id', 'address', 'total_price', 'house_type', 
                    'house_age', 'floor_area', 'latitude', 'longitude'
                )
                print(f"🔍 [find_nearby_houses] 寬鬆模式後，找到 {candidates.count()} 筆房屋")


            # 2. 計算距離並排序 (與原本邏輯相同)
            nearby_list = []
            target_point = (target_lat, target_lon)

            for house in candidates:
                if not house['latitude'] or not house['longitude']:
                    print(f"⚠️ 跳過無經緯度的房屋: {house['address']}")
                    continue
                
                house_point = (house['latitude'], house['longitude'])
                dist = geodesic(target_point, house_point).km
                
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
            
            print(f"✅ [find_nearby_houses] 最終回傳 {len(result)} 筆房屋資料")
            if result:
                print(f"   第一筆: {result[0]['address']} (距離: {result[0]['distance_km']} km)")
            
            return result

        except Exception as e:
            import traceback
            print(f"❌ 尋找周邊房屋失敗: {e}")
            print(traceback.format_exc())
            # 如果出錯，回傳空列表，不要讓整個預測掛掉
            return []

    @classmethod
    def predict(cls, input_data: dict):
        """
        接收前端傳來的 cleaned_data，進行特徵工程並預測
        """
        model = cls._get_model()
        if model is None:
            return {'error': '系統模型載入失敗，請聯繫管理員'}

        try:
            # --- 1. 準備基礎資料 ---
            # 假設 input_data 包含: city, town, street, floor_number, total_floors, 
            # building_type, land_area, floor_area, age, room_count
            
            # 先把變數提取出來
            city = str(input_data.get('city', ''))
            town = str(input_data.get('town', ''))
            street = str(input_data.get('street', ''))

            # 【修正】傳入三個參數 (city, town, street)
            longitude, latitude, is_exact = cls._get_lat_lon(city, town, street)

            # 【修改處 2】檢查經緯度是否為 None
            if longitude is None or latitude is None:
                # 回傳地址錯誤，讓 View 層處理
                return {
                    'error': f'無法定位該地址：「{city}{town}{street}」。請確認地址是否正確，或嘗試輸入更完整的路名。'
                }

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
            # 【修改】準備篩選條件字典 (criteria)
            # 這裡把表單輸入的資料整理成好讀的格式傳給 find_nearby_houses
            criteria = {
                'city': city,
                'house_type': str(input_data.get('house_type')),
                'house_age': float(input_data.get('house_age', 0)),
                'total_floors': float(input_data.get('total_floors', 0)),
                'floor_number': float(input_data.get('floor_number', 0)),
                'floor_area': float(input_data.get('floor_area', 0)),
                'land_area': float(input_data.get('land_area', 0)),
                'room_count': float(input_data.get('room_count', 0)),
            }
            # 【修改】呼叫新的搜尋方法
            nearby_houses = cls.find_nearby_houses(latitude, longitude, criteria)

            # 【修改】回傳值多加一個 'nearby_houses' 與 'target_coords'
            result = {
                'success': True, # 標記成功
                'price': predicted_price,
                'nearby_houses': nearby_houses,
                'target_coords': {'lat': latitude, 'lng': longitude}
            }

            # [新增] 如果是模糊定位 (is_exact = False)，加入警告訊息
            if not is_exact:
                clean_road = re.sub(r'\d+號.*', '', street)
                result['warning'] = f"注意：系統無法精確定位至門牌，目前估價結果是基於「{city}{town}{clean_road}」的平均區段行情，僅供參考。"

            return result

        except Exception as e:
            import traceback
            print(f"預測錯誤: {e}")
            print(traceback.format_exc())
            return {'error': '系統發生預期外的錯誤，請稍後再試'}