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
    // Part 2: Celery 非同步提交與 懸浮卡片邏輯 (大幅修改)
    // ==========================================
    const form = document.getElementById('estimation-form');
    
    // [新] 取得懸浮卡片相關元素
    const floatingCard = document.getElementById('floating-status-card');
    const statusProcessing = document.getElementById('status-processing');
    const statusCompleted = document.getElementById('status-completed');
    
    // [舊] 錯誤視窗 (保持不變)
    const errorModal = document.getElementById('error-modal');

    // [新] 定義跳轉函式 (讓 HTML onclick 呼叫)
    window.resultRedirectUrl = null;
    window.goToResult = function() {
        if (window.resultRedirectUrl) {
            window.location.href = window.resultRedirectUrl;
        }
    };

    if (form) {
        form.setAttribute('novalidate', true);

        form.addEventListener('submit', function(e) {
            e.preventDefault(); // 1. 阻止預設提交
            clearErrors();

            // 2. 前端基礎驗證
            let isValid = true;
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (input.type === 'hidden') return;
                if (!input.checkValidity()) {
                    isValid = false;
                    showError(input, getCustomMessage(input));
                }
            });

            if (!isValid) return;

            // 3. [新] 顯示懸浮卡片 (Processing 狀態)
            if (floatingCard) {
                // 重置狀態：顯示「處理中」，隱藏「完成」
                statusProcessing.classList.remove('hidden');
                statusCompleted.classList.add('hidden');
                
                // 移除 hidden 並加入動畫 class
                floatingCard.classList.remove('hidden');
                // 使用 setTimeout 讓 transition 效果生效 (滑入)
                setTimeout(() => {
                    floatingCard.classList.remove('translate-y-20', 'opacity-0');
                }, 10);
            }

            // 4. [新] 按鈕變更 (但不要 disable 整個頁面)
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerText = '後台運算中...';
                // 讓按鈕變灰，暗示使用者「已經送出了，請看右下角」
                submitBtn.classList.add('bg-slate-400', 'cursor-not-allowed');
                submitBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            }

            // 5. 使用 AJAX 發送表單
            const formData = new FormData(form);
            
            fetch(form.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest', // 告訴後端這是 AJAX
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'validation_error') {
                    // 表單驗證失敗 (後端回傳)
                    hideFloatingCard();
                    resetBtn();
                    alert("輸入資料有誤，請檢查後重試。"); 
                    console.log(data.errors);
                } 
                else if (data.status === 'redirect') {
                    // 需要登入
                    window.location.href = data.url;
                }
                else if (data.task_id) {
                    // 6. 成功取得 task_id，開始輪詢
                    pollTaskStatus(data.task_id);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                hideFloatingCard();
                resetBtn();
                alert("連線發生錯誤，請稍後再試");
            });
        });

        // 輪詢函式
        function pollTaskStatus(taskId) {
            const pollInterval = setInterval(() => {
                fetch(`/task-status/${taskId}/`) // 注意 URL 前綴
                    .then(r => r.json())
                    .then(data => {
                        console.log("Task Status:", data.state);
                        
                        if (data.status === 'completed' && data.redirect_url) {
                            // === 成功 ===
                            clearInterval(pollInterval);
                            
                            // [新] 任務完成！不自動跳轉，而是變更卡片狀態
                            window.resultRedirectUrl = data.redirect_url;
                            
                            // 切換卡片內容：隱藏轉圈圈，顯示綠色勾勾
                            if (statusProcessing && statusCompleted) {
                                statusProcessing.classList.add('hidden');
                                statusCompleted.classList.remove('hidden');
                                // 加個彈跳特效吸引注意
                                statusCompleted.classList.add('animate-bounce-in'); 
                            }
                            
                            // 恢復表單按鈕 (讓使用者可以再填一次)
                            resetBtn();
                            
                        } 
                        else if (data.state === 'FAILURE' || (data.data && data.data.error)) {
                            // === 失敗 (例如定位不到) ===
                            clearInterval(pollInterval);
                            hideFloatingCard();
                            resetBtn();
                            
                            // 顯示原本的紅色錯誤彈窗
                            if (errorModal) {
                                const msgContainer = errorModal.querySelector('.text-slate-600');
                                const errorMsg = data.error || "無法定位該地址，請檢查輸入是否正確。";
                                if (msgContainer) msgContainer.innerHTML = `<p class="font-medium text-red-700">${errorMsg}</p>`;
                                
                                errorModal.classList.remove('hidden');
                            } else {
                                alert(data.error);
                            }
                        }
                    })
                    .catch(err => {
                        console.error("Polling error:", err);
                    });
            }, 1500); // 每 1.5 秒問一次
        }

        // 隱藏懸浮卡片的輔助函式
        function hideFloatingCard() {
            if (floatingCard) {
                // 先做滑出動畫
                floatingCard.classList.add('translate-y-20', 'opacity-0');
                // 等動畫結束再 hidden
                setTimeout(() => floatingCard.classList.add('hidden'), 300);
            }
        }

        // 重置按鈕狀態的輔助函式
        function resetBtn() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerText = '開始估價';
                submitBtn.classList.remove('bg-slate-400', 'cursor-not-allowed');
                submitBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
            }
        }
    }
    
    // 點擊任意處關閉泡泡 (保持不變)
    document.addEventListener('click', function(e) {
        if (!e.target.closest('button[type="submit"]')) {
            clearErrors();
        }
    });
});

// ==========================================
// [修改] 輔助函式：顯示錯誤訊息泡泡
// ==========================================
function showError(input, message) {
    // 1. 標記輸入框紅色外框
    input.classList.add('input-error');

    // 2. 創建錯誤訊息泡泡 div
    const errorBubble = document.createElement('div');
    // [修改] 使用新的 class 名稱
    errorBubble.className = 'validation-bubble';
    // 加入警告圖示和訊息
    errorBubble.innerHTML = `<i class="fas fa-exclamation-circle mr-1"></i>${message}`;

    // 3. 插入到欄位的父容器中
    const parent = input.parentNode;
    if (parent) {
        // [關鍵新增] 確保父容器具有 relative 定位，這樣泡泡才能相對於它定位
        const parentStyle = window.getComputedStyle(parent);
        if (parentStyle.position === 'static') {
            parent.style.position = 'relative';
        }
        parent.appendChild(errorBubble);
    }
    
    // 監聽：當使用者開始打字修改時，移除錯誤樣式和泡泡
    input.addEventListener('input', function() {
        input.classList.remove('input-error');
        if (errorBubble) errorBubble.remove();
        // 如果我們手動加了 relative，可以考慮移除，但保留也無妨
    }, { once: true });
}

// ==========================================
// [修改] 輔助函式：清除所有錯誤
// ==========================================
function clearErrors() {
    // 移除所有紅色框
    document.querySelectorAll('.input-error').forEach(el => el.classList.remove('input-error'));
    // [修改] 移除所有錯誤泡泡 (使用新的 class 名稱)
    document.querySelectorAll('.validation-bubble').forEach(el => el.remove());
}

// ==========================================
// 輔助函式：獲取客製化訊息 (保持不變)
// ==========================================
function getCustomMessage(input) {
    // 針對不同錯誤類型回傳中文訊息
    const v = input.validity;
    
    if (v.valueMissing) return "此欄位為必填";
    if (v.typeMismatch) return "格式不正確";
    if (v.rangeUnderflow) return `數值不能小於 ${input.min}`; // 針對負數
    if (v.rangeOverflow) return `數值不能大於 ${input.max}`;
    if (v.stepMismatch) return "數值間隔不符";
    if (v.tooShort) return `內容太短 (最少 ${input.minLength} 字)`;
    if (v.tooLong) return `內容太長 (最多 ${input.maxLength} 字)`;
    
    return input.validationMessage; // 瀏覽器預設訊息 (fallback)
}

// ==========================================
// [修改] 頁面顯示時 (包含上一頁回來) 的重置邏輯
// ==========================================
window.addEventListener('pageshow', function(event) {
    const form = document.getElementById('estimation-form');
    // 注意：這裡改成隱藏懸浮卡片
    const floatingCard = document.getElementById('floating-status-card');
    
    if (floatingCard) {
        floatingCard.classList.add('hidden');
        floatingCard.classList.add('translate-y-20', 'opacity-0');
    }

    if (form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerText = '開始估價'; 
            submitBtn.classList.remove('bg-slate-400', 'cursor-not-allowed');
            submitBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
        }
    }
});