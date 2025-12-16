// APPS/core/static/core/js/estimation_handler.js
console.log("✅ estimation_handler.js 已成功載入！");

// ==========================================
// 全域變數：地圖實體 (必須在 DOMContentLoaded 外面)
// ==========================================
let mapInstance = null;

document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // Part 1: 行政區動態連動 (保留原本的邏輯)
    // ==========================================
    const citySelect = document.getElementById('id_city');
    const townSelect = document.getElementById('id_town');
    const urlContainer = document.getElementById('ajax-url-container');
    
    // 只有當相關元素都存在時，才執行行政區連動邏輯
    if (citySelect && townSelect && urlContainer) {
        
        const ajaxUrl = urlContainer.dataset.townsUrl; 
        
        if (!ajaxUrl) {
            townSelect.innerHTML = '<option value="">載入失敗 (URL錯誤)</option>';
            console.error("AJAX URL not found.");
        } else {
            /**
             * 根據選定的縣市，發送 AJAX 請求並更新行政區下拉選單
             */
            function updateTowns() {
                const selectedCity = citySelect.value;
                
                // 重設行政區選單
                townSelect.innerHTML = '<option value="">請選擇行政區</option>';
                // 如果沒有選縣市，就保持 disable
                if (!selectedCity) {
                    townSelect.disabled = true; 
                    return;
                }
                townSelect.disabled = true; // 載入中先 disable

                // 發送 AJAX 請求
                sendRequest({
                    url: ajaxUrl,
                    method: 'GET',
                    params: { city: selectedCity },
                    onSuccess: (data) => {
                        if (data.towns && data.towns.length > 0) {
                            data.towns.forEach(town => {
                                const option = document.createElement('option');
                                option.value = town;
                                option.textContent = town;
                                townSelect.appendChild(option);
                            });
                            townSelect.disabled = false; // 載入完成，啟用
                        } else {
                            const option = document.createElement('option');
                            option.value = "";
                            option.textContent = "無可選行政區";
                            townSelect.appendChild(option);
                        }
                    },
                    onError: (error) => {
                        console.error('Error fetching towns:', error);
                        townSelect.innerHTML = '<option value="">載入失敗</option>';
                    }
                });
            }

            // 綁定事件：當縣市改變時，更新行政區
            citySelect.addEventListener('change', updateTowns);

            // 初始化：如果頁面載入時縣市已有值 (例如驗證失敗返回時)，自動載入行政區
            if (citySelect.value) {
                updateTowns();
            }
        }
    }

});

