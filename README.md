## SmartVal 智能房屋估價系統 (SmartVal Real Estate Valuation System)
Python 全端開發：統計分析與資料視覺化實戰期末專案

運用機器學習與大數據，解決房地產資訊不對稱，實現即時、客觀的房價預測。

專案網址：https://ntpu-smartval.zeabur.app/

## 專案簡介 (Introduction)
SmartVal 是一個基於 Django 開發的全端房屋估價平台。本專案旨在解決傳統房屋交易中「價格不透明」與「估價依賴人工經驗」的問題。透過整合實價登錄大數據，並運用機器學習模型（Machine Learning），系統能根據使用者輸入的房屋特徵（如地點、屋齡、坪數等），即時計算出客觀的估價結果。

此外，系統整合了互動式地圖與後台數據儀表板，為買家、賣家及房仲提供直觀的視覺化分析工具。

## 核心功能 (Key Features)
### AI 智能估價：

整合 Scikit-learn 與 XGBoost 模型，針對房屋特徵進行房價預測。

支援模型序列化 (.pkl)，實現快速推論。

### 互動式地圖查詢：

整合 Leaflet.js 地圖框架，視覺化顯示周邊行情。

支援行政區 (City/Town) 連動選單與地圖定位。

### 非同步任務處理 (Async Processing)：

使用 Celery + Redis 處理耗時的估價運算與資料匯入任務，確保前端使用者體驗流暢，不需等待後端運算卡頓。

透過 Django Channels (WebSocket) 實現任務進度即時推播。

### 數據視覺化儀表板：

後台提供 Chart.js 圖表，分析每日估價流量、熱門區域分佈。

### 會員與權限管理：

完整的註冊、登入、登出機制。

使用者可收藏估價結果，建立個人化的追蹤清單。

### 現代化 UI 設計：

使用 Tailwind CSS 打造響應式（RWD）介面，提供極佳的使用者體驗。

設計有漸進式動畫效果與幽默的「施工中」頁面。

## 技術架構 (Tech Stack)
- Backend (後端)
    - Language: Python 3.10+

    - Framework: Django 4.x

    - Async Task Queue: Celery 5.x

    - Message Broker: Redis

    - WebSockets: Django Channels, Daphne

    - Database: SQLite (Dev) / PostgreSQL (Prod)

- Frontend (前端)
    - Template Engine: Django Templates (DTL)

    - Styling: Tailwind CSS (CDN)

    - Mapping: Leaflet.js, OpenStreetMap

    - Icons: Font Awesome 6

    - Interactivity: JavaScript (ES6+), AJAX

- Data Science & ML (資料科學)
    - Libraries: Pandas, NumPy, Scikit-learn, XGBoost, Joblib
