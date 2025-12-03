/**
 * ===================================================================
 * SmartVal 列表頁通用處理器 (AJAX Create, Read, Update, Delete)
 * ===================================================================
 */

// 使用 IIFE 建立私有作用域
(function () {
  "use strict";

  // --- 私有輔助函式 ---

  function showErrors(errorContainer, errorList, errors) {
    errorList.innerHTML = ''; 
    for (const field in errors) {
      errors[field].forEach(error => {
        const li = document.createElement('li');
        li.textContent = error;
        errorList.appendChild(li);
      });
    }
    errorContainer.classList.remove('hidden');
  }

  function clearErrors(errorContainer, errorList) {
    errorContainer.classList.add('hidden');
    errorList.innerHTML = '';
  }

  function updateTableIndexes(tbody) {
    const rows = tbody.querySelectorAll('tr');
    rows.forEach((row, index) => {
      const indexCell = row.querySelector('.row-index');
      if (indexCell) {
        indexCell.textContent = index + 1;
      }
    });
  }
  
  function setupFormFeatures(formElement, features) {
    // 1. 處理連動選單
    if (features.townsUrl) {
      const citySelect = formElement.querySelector('#id_city');
      const townSelect = formElement.querySelector('#id_town');
      
      if (citySelect && townSelect) {
        const initialTownPlaceholder = townSelect.querySelector('option[value=""]').textContent;

        citySelect.addEventListener('change', function () {
          const selectedCity = this.value;
          townSelect.innerHTML = ''; 

          if (!selectedCity) {
            townSelect.add(new Option(initialTownPlaceholder, ''));
            return;
          }

          townSelect.add(new Option('載入中...', ''));
          
          fetch(`${features.townsUrl}?city=${selectedCity}`)
            .then(response => response.json())
            .then(data => {
              townSelect.innerHTML = '';
              const townPlaceholder = townSelect.dataset.placeholder || '請選擇行政區';
              townSelect.add(new Option(townPlaceholder, ''));
              data.towns.forEach(town => townSelect.add(new Option(town, town)));
            })
            .catch(error => {
              console.error('Error loading towns:', error);
              townSelect.innerHTML = '';
              townSelect.add(new Option('載入失敗', ''));
            });
        });
      }
    }

    // 2. 處理 Flatpickr
    if (features.hasFlatpickr) {
      const soldTimeInput = formElement.querySelector('#id_sold_time');
      if (soldTimeInput) {
        if (!soldTimeInput.value) {
            soldTimeInput.placeholder = 'yyyy-mm-dd';
        }
        flatpickr(soldTimeInput, {
          dateFormat: 'Y-m-d',
          allowInput: true,
          locale: 'zh_tw'
        });
      }
    }
  }

  function resetForm(formElement, originalHtml) {
      formElement.innerHTML = originalHtml;
  }
  
  // --- 工廠函式 (公開) ---

  function initializeListPageHandler(config) {
    
    // --- 1. 獲取所有 DOM 元素 ---
    const modal = document.getElementById(config.modalId);
    const tableBody = document.getElementById(config.tableBodyId);
    const openCreateBtn = document.getElementById('open-create-modal-btn');
    
    if (!modal || !tableBody || !openCreateBtn) {
      console.error("[ListPageHandler] 初始化失敗：找不到 Modal, TableBody 或 OpenCreateBtn。");
      return;
    }
    
    // Modal 內部元素
    const modalTitle = config.modalTitle;
    const modalHeader = config.modalHeader;
    const form = document.getElementById(config.formId);
    const formContentContainer = config.formContentContainer;
    const submitBtn = modal.querySelector('#modal-submit-btn');
    const errorContainer = modal.querySelector('#modal-form-errors');
    const errorList = modal.querySelector('#modal-error-list');
    const closeButtons = [
      modal.querySelector('#close-modal-btn-x'),
      modal.querySelector('#close-modal-btn-cancel')
    ];

    let currentMode = 'CREATE'; 
    let currentEditUrl = ''; 
    
    // --- 2. 定義 Modal 控制函式 ---
    
    const showModal = () => modal.classList.remove('hidden');
    
    const hideModal = () => {
      modal.classList.add('hidden');
      clearErrors(errorContainer, errorList); 
      resetForm(formContentContainer, config.createConfig.formHtml);
      setupFormFeatures(form, config.commonFeatures);
    };

    function switchToCreateMode() {
        currentMode = 'CREATE';
        modalTitle.textContent = config.createConfig.modalTitle;
        form.action = config.createConfig.formAction;
        modalHeader.classList.remove(...config.editConfig.headerClass.split(' '));
        modalHeader.classList.add(...config.createConfig.headerClass.split(' '));
        
        resetForm(formContentContainer, config.createConfig.formHtml);
        setupFormFeatures(form, config.commonFeatures);
        
        showModal();
    }

    async function switchToEditMode(editUrl) {
        currentMode = 'EDIT';
        currentEditUrl = editUrl;
        
        modalTitle.textContent = config.editConfig.modalTitle;
        form.action = editUrl;
        modalHeader.classList.remove(...config.createConfig.headerClass.split(' '));
        modalHeader.classList.add(...config.editConfig.headerClass.split(' '));

        formContentContainer.innerHTML = '<p class="text-center p-8">載入資料中...</p>';
        showModal();
        
        try {
            const response = await fetch(editUrl, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!response.ok) throw new Error('伺服器讀取錯誤');
            
            const data = await response.json();
            
            if (data.success) {
                formContentContainer.innerHTML = data.html;
                setupFormFeatures(form, config.commonFeatures);
            } else {
                throw new Error('無法載入表單');
            }
        } catch (error) {
            console.error('[ListPageHandler] 載入編輯表單失敗:', error);
            hideModal();
            alert('載入編輯資料失敗，請稍後再試。');
        }
    }
    
    // --- 3. 綁定基本事件監聽器 ---
    
    // 【修正】加入調試和錯誤處理
    if (!openCreateBtn) {
      console.error('[ListPageHandler] 找不到 open-create-modal-btn');
    } else {
      console.log('[ListPageHandler] 找到 open-create-modal-btn，準備綁定事件');
      openCreateBtn.addEventListener('click', function(e) {
        console.log('[ListPageHandler] 新增按鈕被點擊');
        switchToCreateMode();
      });
    }
    
    closeButtons.forEach((btn, index) => {
      if (!btn) {
        console.warn(`[ListPageHandler] 找不到關閉按鈕 #${index}`);
      } else {
        btn.addEventListener('click', hideModal);
      }
    });
    
    // --- 4. 綁定 AJAX "編輯" 按鈕 (事件委派) ---
    
    // 【修正】更穩健的事件委派，加入調試
    tableBody.addEventListener('click', function(e) {
        // 檢查是否點擊到編輯按鈕或其子元素
        const editBtn = e.target.closest('.open-edit-modal-btn');
        if (editBtn) {
            console.log('[ListPageHandler] 編輯按鈕被點擊', editBtn);
            const url = editBtn.dataset.url;
            if (!url) {
                console.error('[ListPageHandler] 編輯按鈕缺少 data-url 屬性');
                return;
            }
            console.log('[ListPageHandler] 準備載入編輯表單:', url);
            switchToEditMode(url);
        }
    });

    // --- 5. 綁定 AJAX "儲存" (新增/編輯) 事件 ---
    
    form.addEventListener('submit', async function (e) {
      e.preventDefault(); 
      clearErrors(errorContainer, errorList);
      submitBtn.disabled = true;
      submitBtn.textContent = '儲存中...';

      const formData = new FormData(form);
      const actionUrl = form.action; 
      
      try {
          const response = await fetch(actionUrl, {
            method: 'POST',
            body: formData,
            headers: {
              'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
              'X-Requested-With': 'XMLHttpRequest' 
            }
          });
          
          if (!response.ok) throw new Error(`Server responded with status: ${response.status}`);
          
          const data = await response.json();
          
          if (data.success) {
            // 【!! 重大修改 !!】
            // 為了讓後端分頁重新計算，我們不再動態插入 HTML，
            // 而是直接重新整理頁面。
            hideModal(); // 先關閉 Modal
            location.reload(); // 重新整理頁面
            
            // (舊的動態插入邏輯已被移除)

          } else {
            // 【驗證失敗】: 後端回傳了 "帶有錯誤的" 表單 HTML
            formContentContainer.innerHTML = data.html;
            setupFormFeatures(form, config.commonFeatures);
            const firstError = formContentContainer.querySelector('.text-red-600');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            // 請求未成功，恢復按鈕狀態
            submitBtn.disabled = false;
            submitBtn.textContent = '儲存';
          }
      } catch (error) {
          console.error('[ListPageHandler] 表單儲存失敗:', error);
          showErrors(errorContainer, errorList, {'__all__': ['處理請求時發生未預期的錯誤。']});
          // 請求失敗，恢復按鈕狀態
          submitBtn.disabled = false;
          submitBtn.textContent = '儲存';
      }
      // finally 區塊被移除，因為成功時頁面會 reload，不需要恢復按鈕。
      // 只有在失敗或驗證錯誤時才需要恢復按鈕，已移至 catch 和 else 區塊。
    });
  
    // --- 6. 綁定 AJAX "刪除" 事件 (與之前相同) ---
    // 【!! 修改 !!】 刪除成功後，也改成 location.reload()
    tableBody.addEventListener('submit', function(e) {
        if (e.target && e.target.matches('.delete-form')) {
            e.preventDefault(); 
            
            const deleteForm = e.target;
            const row = deleteForm.closest('tr');
            
            // (確認對話框由 onsubmit 屬性處理)
            
            fetch(deleteForm.action, {
                method: 'POST',
                body: new FormData(deleteForm),
                headers: {
                    'X-CSRFToken': deleteForm.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (response.ok) {
                    // 【!! 修改 !!】
                    location.reload(); // 重新整理以更新分頁
                } else {
                    alert('刪除失敗，請重新整理頁面再試。');
                }
            })
            .catch(error => {
                console.error(`[ListPageHandler] AJAX 刪除失敗:`, error);
                alert('刪除時發生錯誤。');
            });
        }
    });

    // 刪除 updateTableIndexes 的呼叫，因為我們不再動態更新
    // updateTableIndexes(tableBody); 
    console.log(`[ListPageHandler] ${config.tableBodyId} 已成功初始化。`);
  }
  
  window.initializeListPageHandler = initializeListPageHandler;

})();