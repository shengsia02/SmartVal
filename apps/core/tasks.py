from celery import shared_task
from .services import HousePriceService

@shared_task
def predict_house_price(input_data):
    """
    非同步執行的估價任務
    """
    try:
        # 呼叫原本的 Service 邏輯
        result = HousePriceService.predict(input_data)
        
        # 為了讓結果能存入 Session (JSON 序列化)，需要確保回傳的都是基本型別
        # Service 目前回傳的已經是 dict，但如果有 Decimal 需要注意
        # 這裡我們回傳一個標準結構
        return {
            'status': 'success' if 'error' not in result else 'error',
            'data': result,
            'input_data': input_data
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'data': {'error': '系統發生未預期的錯誤，請稍後再試。'}
        }