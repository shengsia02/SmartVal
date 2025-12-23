// APPS/core/static/core/js/estimation_handler.js

document.addEventListener('DOMContentLoaded', function() {
    // 獲取表單元素
    const citySelect = document.getElementById('id_city');
    const townSelect = document.getElementById('id_town');
    
    // 【!! 獲取隱藏的 URL 容器元素 !!】
    const urlContainer = document.getElementById('ajax-url-container');
    
    // 檢查元素是否存在，確保代碼只在 HomeView 運行
    if (!citySelect || !townSelect || !urlContainer) {
        return;
    }

    // 【!! 修改 !!】從 DOM 元素的 data 屬性讀取 AJAX URL
    const ajaxUrl = urlContainer.dataset.townsUrl; 
    
    if (!ajaxUrl) {
        // 現在這個錯誤只會在 Django 沒有成功解析 {% url %} 時發生
        townSelect.innerHTML = '<option value="">載入失敗 (URL錯誤)</option>';
        console.error("AJAX URL not found. Django URL tag did not render correctly.");
        return;
    }

    /**
     * 根據選定的縣市，發送 AJAX 請求並更新行政區下拉選單
     */
    function updateTowns() {
        // ... (updateTowns 函數內部邏輯保持不變) ...
        const selectedCity = citySelect.value;
        
        // 1. 重設行政區選單
        townSelect.innerHTML = '<option value="">請選擇行政區</option>';
        townSelect.disabled = true; 

        if (!selectedCity) {
            return;
        }

        // 2. 發送 AJAX 請求
        fetch(`${ajaxUrl}?city=${selectedCity}`, { // 使用從 DOM 讀取的 ajaxUrl
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.towns && data.towns.length > 0) {
                // 3. 填充新的選項
                data.towns.forEach(town => {
                    const option = document.createElement('option');
                    option.value = town;
                    option.textContent = town;
                    townSelect.appendChild(option);
                });
                townSelect.disabled = false;
            } else {
                 const option = document.createElement('option');
                 option.value = "";
                 option.textContent = "無可選行政區";
                 townSelect.appendChild(option);
            }
        })
        .catch(error => {
            console.error('Error fetching towns:', error);
            townSelect.innerHTML = '<option value="">載入失敗</option>'; 
        });
    }

    // 4. 綁定事件監聽器
    citySelect.addEventListener('change', updateTowns);

    // 5. 確保頁面載入時，如果縣市有預設值，也載入行政區
    if (citySelect.value) {
        updateTowns();
    }
});