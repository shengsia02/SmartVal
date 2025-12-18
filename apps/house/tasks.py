# apps/house/tasks.py
import os
import pandas as pd
from decimal import Decimal
from celery import shared_task
from django.db import transaction
from django.core.exceptions import ValidationError
from channels.layers import get_channel_layer # 新增
from asgiref.sync import async_to_sync # 新增
from .models import House, Agent, Buyer

@shared_task
def import_excel_task(file_path, user_id):
    """
    背景執行 Excel 匯入任務，並透過 WebSocket 通知特定使用者
    """
    # 準備 WebSocket 推播工具
    channel_layer = get_channel_layer()
    group_name = f"user_{user_id}"

    def send_notification(status, message):
        """輔助函式：發送 WebSocket 訊息"""
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'task_message', # 對應 Consumer 的 task_message 方法
                'status': status,
                'message': message
            }
        )

    try:
        # 1. 讀取 Excel (從路徑)
        try:
            xls = pd.read_excel(file_path, sheet_name=None)
        except Exception as e:
            return {'status': 'error', 'error': f'無法讀取 Excel 檔案: {str(e)}'}

        # 2. 檢查工作表
        required_sheets = ['仲介', '買家', '房屋']
        for sheet_name in required_sheets:
            if sheet_name not in xls:
                return {'status': 'error', 'error': f'缺少 "{sheet_name}" 工作表。'}

        # 定義欄位對照 (與原本 View 相同)
        AGENT_COLUMN_MAP = {
            '姓名': 'name', '聯絡電話': 'phone', '電子郵件': 'email',
            '隸屬公司': 'company', '分行名稱': 'branch', '分行縣市': 'city', '分行行政區': 'town',
        }
        BUYER_COLUMN_MAP = {
            '姓名': 'name', '聯絡電話': 'phone', '電子郵件': 'email',
        }
        HOUSE_COLUMN_MAP = {
            '縣市': 'city', '行政區': 'town', '房屋類型': 'house_type', '地址': 'address',
            '所在層數': 'floor_number', '地坪': 'land_area', '地上總層數': 'total_floors',
            '建坪': 'floor_area', '房間數': 'room_count', '總價格（萬元）': 'total_price',
            '建坪單價(萬元/坪)': 'unit_price', '經度': 'longitude', '緯度': 'latitude',
            '屋齡（年）': 'house_age', '出售日期': 'sold_time',
            '仲介': 'agent_name', '買家': 'buyer_name',
        }

        BATCH_SIZE = 1000

        # ===== 執行匯入邏輯 (與原本 View 邏輯一致，僅移除 request 相關) =====
        
        # (A) 處理仲介
        sheet_name = '仲介'
        if sheet_name in xls:
            df_agent = xls[sheet_name].rename(columns=AGENT_COLUMN_MAP)
            df_agent = df_agent.where(pd.notnull(df_agent), None)
            agent_records = df_agent.to_dict('records')
            
            for i in range(0, len(agent_records), BATCH_SIZE):
                batch_data = agent_records[i:i+BATCH_SIZE]
                with transaction.atomic():
                    agents_to_create = []
                    agents_to_update = []
                    batch_names = [d['name'] for d in batch_data if d.get('name')]
                    existing_agents = {a.name: a for a in Agent.objects.filter(name__in=batch_names)}
                    
                    for row in batch_data:
                        name = row.get('name')
                        if not name: continue
                        clean_data = {k: (str(v).strip() if v is not None else None) for k, v in row.items()}
                        if name in existing_agents:
                            agent = existing_agents[name]
                            for key, value in clean_data.items():
                                setattr(agent, key, value)
                            agents_to_update.append(agent)
                        else:
                            agents_to_create.append(Agent(**clean_data))
                    
                    if agents_to_create:
                        Agent.objects.bulk_create(agents_to_create, ignore_conflicts=True)
                    if agents_to_update:
                        Agent.objects.bulk_update(agents_to_update, ['phone', 'email', 'company', 'branch', 'city', 'town'])

        # (B) 處理買家
        sheet_name = '買家'
        if sheet_name in xls:
            df_buyer = xls[sheet_name].rename(columns=BUYER_COLUMN_MAP)
            df_buyer = df_buyer.where(pd.notnull(df_buyer), None)
            buyer_records = df_buyer.to_dict('records')
            
            for i in range(0, len(buyer_records), BATCH_SIZE):
                batch_data = buyer_records[i:i+BATCH_SIZE]
                with transaction.atomic():
                    buyers_to_create = []
                    buyers_to_update = []
                    batch_names = [d['name'] for d in batch_data if d.get('name')]
                    existing_buyers = {b.name: b for b in Buyer.objects.filter(name__in=batch_names)}
                    
                    for row in batch_data:
                        name = row.get('name')
                        if not name: continue
                        clean_data = {k: (str(v).strip() if v is not None else None) for k, v in row.items()}
                        if name in existing_buyers:
                            buyer = existing_buyers[name]
                            for key, value in clean_data.items():
                                setattr(buyer, key, value)
                            buyers_to_update.append(buyer)
                        else:
                            buyers_to_create.append(Buyer(**clean_data))
                    
                    if buyers_to_create:
                        Buyer.objects.bulk_create(buyers_to_create, ignore_conflicts=True)
                    if buyers_to_update:
                        Buyer.objects.bulk_update(buyers_to_update, ['phone', 'email'])

        # (C) 處理房屋
        sheet_name = '房屋'
        if sheet_name in xls:
            df_house = xls[sheet_name].rename(columns=HOUSE_COLUMN_MAP)
            df_house = df_house.where(pd.notnull(df_house), None)
            
            all_agent_names = df_house['agent_name'].dropna().unique().tolist()
            all_buyer_names = df_house['buyer_name'].dropna().unique().tolist()
            agents_dict = {a.name: a for a in Agent.objects.filter(name__in=all_agent_names)}
            buyers_dict = {b.name: b for b in Buyer.objects.filter(name__in=all_buyer_names)}

            house_records = df_house.to_dict('records')
            DECIMAL_2DP_FIELDS = {'house_age', 'floor_area', 'land_area', 'unit_price'}
            DECIMAL_12DP_FIELDS = {'longitude', 'latitude'}
            INTEGER_FIELDS = {'floor_number', 'total_floors', 'room_count', 'total_price'}
            
            for i in range(0, len(house_records), BATCH_SIZE):
                batch_data = house_records[i:i+BATCH_SIZE]
                with transaction.atomic():
                    houses_to_create = []
                    houses_to_update = []
                    batch_addresses = [d['address'] for d in batch_data if d.get('address')]
                    existing_houses = {h.address: h for h in House.objects.filter(address__in=batch_addresses)}
                    
                    for idx, row in enumerate(batch_data):
                        excel_row_num = i + idx + 2 
                        
                        agent_name = row.get('agent_name')
                        buyer_name = row.get('buyer_name')
                        if not agent_name or agent_name not in agents_dict:
                            raise ValidationError(f'第 {excel_row_num} 行: 找不到仲介 "{agent_name}"')
                        if not buyer_name or buyer_name not in buyers_dict:
                            raise ValidationError(f'第 {excel_row_num} 行: 找不到買家 "{buyer_name}"')
                        
                        house_params = {}
                        if not row.get('address'):
                             raise ValidationError(f'第 {excel_row_num} 行: 地址為必填')

                        ALL_HOUSE_FIELDS = [
                            'city', 'town', 'house_type', 'address', 
                            'floor_number', 'land_area', 'total_floors', 
                            'floor_area', 'room_count', 'total_price', 
                            'unit_price', 'longitude', 'latitude', 
                            'house_age', 'sold_time'
                        ]

                        for field in ALL_HOUSE_FIELDS:
                            value = row.get(field)
                            if value is None:
                                house_params[field] = None
                                continue
                            try:
                                if field == 'sold_time':
                                    house_params[field] = str(value).split(' ')[0]
                                elif field in DECIMAL_2DP_FIELDS:
                                    house_params[field] = Decimal(str(value)).quantize(Decimal('0.01'))
                                elif field in DECIMAL_12DP_FIELDS:
                                    house_params[field] = Decimal(str(value)).quantize(Decimal('0.000000000001'))
                                elif field in INTEGER_FIELDS:
                                    house_params[field] = int(float(value))
                                else:
                                    house_params[field] = str(value)
                            except Exception as e:
                                raise ValidationError(f'第 {excel_row_num} 行: 欄位 {field} 格式錯誤 ({value})')

                        house_params['agent'] = agents_dict[agent_name]
                        house_params['buyers'] = buyers_dict[buyer_name]
                        
                        address = house_params['address']
                        if address in existing_houses:
                            house = existing_houses[address]
                            for key, val in house_params.items():
                                setattr(house, key, val)
                            houses_to_update.append(house)
                        else:
                            houses_to_create.append(House(**house_params))
                    
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

        # [修改] 成功時發送通知
        send_notification('success', 'Excel 資料匯入成功！您可以前往列表查看。')

        return {'status': 'success', 'message': 'Excel 資料匯入成功！'}

    except ValidationError as e:
        # [修改] 失敗時發送通知
        send_notification('error', f'匯入失敗：{e.message}')
        return {'status': 'error', 'error': e.message}
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        error_msg = f'系統發生預期外的錯誤: {str(e)}'
        # [修改] 失敗時發送通知
        send_notification('error', error_msg)
        return {'status': 'error', 'error': error_msg}
    
    finally:
        # [重要] 任務結束後，刪除暫存檔案以釋放空間
        if os.path.exists(file_path):
            os.remove(file_path)