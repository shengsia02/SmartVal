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

    // ==========================================
    // Part 2: 估價表單提交與結果顯示 (【新增】)
    // ==========================================
    const form = document.getElementById('estimation-form');
    const resultSection = document.getElementById('result-section');
    const loadingSection = document.getElementById('loading-section');
    const priceDisplay = document.getElementById('predicted-price');

    // 只有在表單存在時才執行 (確保不會在其他頁面報錯)
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault(); // 1. 阻止表單預設的頁面跳轉行為

            // 2. 切換 UI 狀態：顯示 Loading，隱藏舊結果
            if (resultSection) resultSection.classList.add('hidden');
            if (loadingSection) loadingSection.classList.remove('hidden');
            
            // 【!! 新增 !!】 點擊後立刻平滑捲動到下方的白色結果區塊 (result-container)
            // 這樣使用者就會看到「正在進行 AI 運算中...」的轉圈圈
            const resultContainer = document.getElementById('result-container');
            if (resultContainer) {
                resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

            // 3. 收集表單資料
            const formData = new FormData(form);

            // 4. 發送 POST 請求給後端
            // window.location.href 代表 POST 到當前頁面的 URL (即 HomeView)
            sendRequest({
                url: window.location.href,
                method: 'POST',
                data: formData,
                onSuccess: (data) => {
                    // 隱藏 Loading 動畫
                    if (loadingSection) loadingSection.classList.add('hidden');

                    console.log('📥 後端回傳資料:', data); // Debug: 查看完整回傳資料

                    if (data.success) {
                        // 1. 顯示價格
                        if (priceDisplay) priceDisplay.textContent = data.price;
                        if (resultSection) {
                            resultSection.classList.remove('hidden');
                            // 平滑捲動視窗到結果區塊，提升體驗
                            resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        }
                        
                        // 2. 【新增】繪製地圖 - 加入資料驗證
                        if (data.target_coords && data.nearby_houses) {
                            console.log('🗺️ 準備初始化地圖...');
                            console.log('目標座標:', data.target_coords);
                            console.log('周邊房屋數量:', data.nearby_houses.length);
                            
                            // 確保 Leaflet 已載入
                            if (typeof L === 'undefined') {
                                console.error('❌ Leaflet 庫未載入！');
                                alert('地圖功能載入失敗，請重新整理頁面');
                            } else {
                                initMap(data.target_coords, data.nearby_houses);
                            }
                        } else {
                            console.warn('⚠️ 缺少地圖資料，無法顯示地圖');
                        }
                    } else {
                        // --- 失敗：顯示錯誤 ---
                        // 如果後端回傳的是表單驗證錯誤 (data.errors)，可以在這裡處理顯示在欄位旁
                        // 這裡先簡單用 alert 顯示
                        let errorMsg = data.error || '輸入資料有誤，請檢查欄位。';
                        
                        // 如果是表單欄位錯誤 (data.errors 是個物件)
                        if (data.errors) {
                            // 簡單將錯誤訊息串接起來
                            errorMsg += '\n' + JSON.stringify(data.errors);
                        }
                        
                        alert('估價失敗：' + errorMsg);
                        console.error('Validation errors:', data.errors);
                    }
                },
                onError: (error) => {
                    if (loadingSection) loadingSection.classList.add('hidden');
                    alert('系統發生連線錯誤，請稍後再試。');
                    console.error('Fetch error:', error);
                }
            });
        });

        // 【新增】監聽表單的 "reset" 事件 (當使用者點擊「清除重填」時觸發)
        form.addEventListener('reset', function() {
            // 1. 隱藏結果區塊
            if (resultSection) {
                resultSection.classList.add('hidden');
            }
            
            // 2. (選用) 清空顯示的價格數字，歸零
            if (priceDisplay) {
                priceDisplay.textContent = '0';
            }

            // 3. 確保 Loading 也被隱藏 (以防萬一)
            if (loadingSection) {
                loadingSection.classList.add('hidden');
            }
            
            // 注意：這裡不需要 e.preventDefault()，因為我們希望表單欄位被清空
        });    
    }
});


/**
 * 初始化並繪製 Leaflet 地圖
 * @param {Object} target - 目標房屋座標 {lat, lng}
 * @param {Array} nearby - 周邊房屋列表
 */
function initMap(target, nearby) {
    console.log('🗺️ initMap 被調用');
    console.log('target:', target);
    console.log('nearby:', nearby);
    
    // 驗證參數
    if (!target || !target.lat || !target.lng) {
        console.error('❌ 目標座標資料不完整:', target);
        return;
    }
    
    // 驗證地圖容器存在
    const mapContainer = document.getElementById('map');
    if (!mapContainer) {
        console.error('❌ 找不到地圖容器 #map');
        return;
    }
    
    try {
        // 如果地圖已經存在，先移除 (這是 Leaflet 的規定，不能重複 init)
        if (mapInstance) {
            console.log('移除舊地圖實例...');
            mapInstance.remove();
            mapInstance = null; 
        }

        // 1. 初始化地圖，中心點設為目標房屋
        console.log(`初始化地圖中心點: [${target.lat}, ${target.lng}]`);
        mapInstance = L.map('map').setView([target.lat, target.lng], 15);
        
        console.log('地圖實例已創建:', mapInstance);

        // 2. 載入 OpenStreetMap 圖資
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(mapInstance);
        
        console.log('圖資已載入');
        
        // 重要：延遲調用 invalidateSize 以確保地圖尺寸正確
        setTimeout(() => {
            mapInstance.invalidateSize();
            console.log('地圖尺寸已重新計算');
        }, 100);

        // 3. 加入「目標房屋」標記 - 使用自訂紅色房屋圖標
        const targetIcon = L.divIcon({
            className: 'custom-target-marker',
            html: `<div style="position: relative; width: 40px; height: 40px;">
                      <div style="position: absolute; top: 0; left: 50%; transform: translateX(-50%); 
                                  background-color: #DC2626; color: white; 
                                  width: 36px; height: 36px; border-radius: 50% 50% 50% 0; 
                                  transform: translateX(-50%) rotate(-45deg); 
                                  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                                  border: 3px solid white;
                                  display: flex; align-items: center; justify-content: center;">
                          <span style="transform: rotate(45deg); font-size: 20px;">🏠</span>
                      </div>
                   </div>`,
            iconSize: [40, 40],
            iconAnchor: [20, 40],
            popupAnchor: [0, -40]
        });
        
        const targetMarker = L.marker([target.lat, target.lng], {
            icon: targetIcon,
            zIndexOffset: 1000  // 確保顯示在最上層
        }).addTo(mapInstance);
        console.log('目標標記已加入');
        
        const priceElement = document.getElementById('predicted-price');
        const priceText = priceElement ? priceElement.textContent : '(未知)';
        
        targetMarker.bindPopup(`
            <div style="text-align: center;">
                <b style="color: red; font-size: 1.1em;">🏠 目標估價房屋</b><br>
                預測價格: <b>${priceText} 萬元</b>
            </div>
        `).openPopup();

        // 4. 加入「周邊房屋」標記 - 使用 MarkerCluster 處理重疊
        if (nearby && Array.isArray(nearby) && nearby.length > 0) {
            console.log(`準備加入 ${nearby.length} 個周邊房屋標記（使用聚合功能）`);
            
            // 創建 MarkerCluster 群組 - 使用自訂紅色圖標
            const markers = L.markerClusterGroup({
                // 當縮放到最大時，即使在同一位置也要展開成蜘蛛腿
                spiderfyOnMaxZoom: true,
                // 點擊聚合標記時展開
                showCoverageOnHover: false,
                // 縮放到展開標記的層級
                zoomToBoundsOnClick: true,
                // 最大聚合半徑（像素）
                maxClusterRadius: 80,
                // 自訂聚合圖標 - 紅色主題
                iconCreateFunction: function(cluster) {
                    const count = cluster.getChildCount();
                    let size = 'small';
                    
                    if (count >= 10) {
                        size = 'large';
                    } else if (count >= 5) {
                        size = 'medium';
                    }
                    
                    return L.divIcon({
                        html: `<div style="background-color: #1e40af; color: white; font-weight: bold; 
                               width: 100%; height: 100%; border-radius: 50%; display: flex; 
                               align-items: center; justify-content: center; font-size: 14px;">
                               ${count}
                               </div>`,
                        className: 'marker-cluster marker-cluster-' + size,
                        iconSize: L.point(40, 40)
                    });
                }
            });
            
            let successCount = 0;
            let failCount = 0;
            
            nearby.forEach((house, index) => {
                if (!house.lat || !house.lng) {
                    console.warn(`❌ 周邊房屋 ${index} 缺少座標`);
                    failCount++;
                    return;
                }
                
                try {
                    // 使用 CircleMarker 而不是普通 Marker
                    const circle = L.circleMarker([house.lat, house.lng], {
                        color: 'rgb(220, 38, 38)', // 藍色邊框
                        fillColor: 'rgb(220, 38, 38)', // 藍色填充
                        fillOpacity: 0.7,
                        radius: 8,
                        weight: 2
                    });

                    // 加入詳細資訊 Popup
                    circle.bindPopup(`
                        <div style="min-width: 200px;">
                            <b style="color: #1e40af;">${house.address || '未知地址'}</b><br>
                            <hr style="margin: 8px 0; border: none; border-top: 1px solid #e5e7eb;">
                            💰 成交價: <b>${house.price || 'N/A'}</b> 萬元<br>
                            📐 坪數: ${house.area || 'N/A'} 坪<br>
                            🏠 類型: ${house.type || 'N/A'}<br>
                            📅 屋齡: ${house.age || 'N/A'} 年<br>
                            <span style="color: #6b7280; font-size: 0.9em;">📍 距離: ${house.distance_km || 'N/A'} km</span>
                        </div>
                    `);
                    
                    // 加入到群組中，而不是直接加到地圖
                    markers.addLayer(circle);
                    successCount++;
                    
                } catch (e) {
                    console.error(`❌ 加入周邊房屋 ${index} 標記失敗:`, e);
                    failCount++;
                }
            });
            
            // 將整個群組加入地圖
            mapInstance.addLayer(markers);
            
            console.log(`✅ 成功加入 ${successCount} 個標記到聚合群組，失敗 ${failCount} 個`);
        } else {
            console.warn('⚠️ 沒有周邊房屋資料');
        }
        
        console.log('✅ 地圖初始化完成');
        
    } catch (error) {
        console.error('❌ 地圖初始化失敗:', error);
        alert('地圖顯示失敗: ' + error.message);
    }
}