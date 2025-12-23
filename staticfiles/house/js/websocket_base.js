// static/house/js/websocket_base.js

/**
 * 設定一個標記，告訴 WebSocket 接下來的幾秒鐘內「忽略」通知
 * (請在表單送出時呼叫此函式)
 */
function markAsMyUpdate() {
    // 設定一個標記，有效期為當下時間
    localStorage.setItem('ws_my_update_timestamp', Date.now());
}

/**
 * 初始化 WebSocket 連線與通知
 * @param {string} endpointPath - WebSocket 的路徑
 * @param {string} targetType - 要監聽的事件類型
 * @param {string} labelName - 顯示在通知上的名稱
 */
function setupWebSocket(endpointPath, targetType, labelName) {
    
    if (!document.getElementById('ws-toast-container')) {
        const container = document.createElement('div');
        container.id = 'ws-toast-container';
        document.body.appendChild(container);
    }

    const ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    const ws_url = `${ws_scheme}://${window.location.host}/ws/${endpointPath}/`;

    console.log(`[WebSocket] 正在連線至: ${ws_url}`);
    const socket = new WebSocket(ws_url);

    socket.onopen = function(e) {
        console.log(`[WebSocket] ${labelName}頻道已連線`);
    };

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        
        if (data.type === targetType) {
            // 【關鍵修改】檢查是否為「我自己」觸發的更新
            if (shouldIgnoreUpdate()) {
                console.log(`[WebSocket] 偵測到這是本機觸發的更新，已忽略通知。`);
                return; // 直接結束，不顯示通知
            }

            console.log(`[WebSocket] 收到更新:`, data.message);
            showToast(data.message);
        }
    };

    socket.onclose = function(e) {
        console.warn(`[WebSocket] ${labelName}連線已中斷`);
    };

    // --- 內部小工具：判斷是否忽略通知 ---
    function shouldIgnoreUpdate() {
        const timestamp = localStorage.getItem('ws_my_update_timestamp');
        if (timestamp) {
            // 取出後立刻清除，避免影響下一次
            localStorage.removeItem('ws_my_update_timestamp');
            
            // 檢查標記是否在 5 秒內建立的 (避免舊標記殘留)
            if (Date.now() - parseInt(timestamp) < 5000) {
                return true;
            }
        }
        return false;
    }

    // --- 內部小工具：顯示 Toast 通知 ---
    function showToast(message) {
        const container = document.getElementById('ws-toast-container');
        
        const toast = document.createElement('div');
        toast.className = 'ws-toast';
        toast.innerHTML = `
            <div class="ws-toast-content">
                <span style="font-weight:bold;">【${labelName}系統通知】</span><br/>
                ${message}
            </div>
            <button class="ws-toast-btn" onclick="window.location.reload()">
                點擊更新
            </button>
        `;

        container.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // 【修改】5秒後自動消失並刷新頁面
        setTimeout(() => {
            if (container.contains(toast)) {
                // 淡出
                toast.style.opacity = '0';

                // 等待淡出動畫結束後
                setTimeout(() => {
                    if (container.contains(toast)) {
                        container.removeChild(toast);
                    }
                    // 【新增】如果使用者沒點，時間到自動刷新
                    console.log('[WebSocket] 通知逾時，自動刷新頁面');
                    window.location.reload();
                }, 500); 
            }
        }, 5000); // 這裡設定顯示 5 秒
    }
}