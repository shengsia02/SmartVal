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

      const birthDateInput = formElement.querySelector('#id_birth_date');
      if (birthDateInput) {
        flatpickr(birthDateInput, {
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
    
    openCreateBtn.addEventListener('click', switchToCreateMode);
    
    closeButtons.forEach(btn => btn.addEventListener('click', hideModal));
    
    // --- 4. 綁定 AJAX "編輯" 按鈕 (事件委派) ---
    
    tableBody.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.open-edit-modal-btn');
        if (editBtn) {
            const url = editBtn.dataset.url;
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
            // 【儲存成功】
            if (currentMode === 'CREATE') {
                tableBody.insertAdjacentHTML('afterbegin', data.html);
            } else {
                const pk_form_field = config.pk_form_field || 'id'; 
                const row_id_prefix = config.row_id_prefix || 'row-';
                
                // 【!! 修正 !!】
                // 從 instance.pk 獲取 pk (因為 disabled 欄位不在 formData 中)
                let pk = formData.get(pk_form_field);
                
                if (!pk) {
                    // 如果 formData 中沒有 (例如 house_id)，
                    // 嘗試從表單內的隱藏欄位 DOM 獲取
                    const hiddenInput = form.querySelector(`input[name="${pk_form_field}"]`);
                    if (hiddenInput) {
                        pk = hiddenInput.value;
                    }
                }
                
                if (pk) {
                    const rowId = `#${row_id_prefix}${pk}`;
                    const oldRow = tableBody.querySelector(rowId);
                    if (oldRow) {
                        oldRow.outerHTML = data.html; // 替換整列
                    } else {
                        console.warn(`[ListPageHandler] 找不到舊資料列: ${rowId}。 已改為插入到頂部。`);
                        tableBody.insertAdjacentHTML('afterbegin', data.html);
                    }
                } else {
                    console.error(`[ListPageHandler] 找不到 PK 欄位 '${pk_form_field}'。 已改為插入到頂部。`);
                    tableBody.insertAdjacentHTML('afterbegin', data.html);
                }
            }
            updateTableIndexes(tableBody); // 更新序號
            hideModal();
          } else {
            // 【驗證失敗】: 後端回傳了 "帶有錯誤的" 表單 HTML
            formContentContainer.innerHTML = data.html;
            setupFormFeatures(form, config.commonFeatures);
            const firstError = formContentContainer.querySelector('.text-red-600');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
          }
      } catch (error) {
          console.error('[ListPageHandler] 表單儲存失敗:', error);
          showErrors(errorContainer, errorList, {'__all__': ['處理請求時發生未預期的錯誤。']});
      } finally {
          // 【!! 關鍵修改 !!】
          // 無論成功或失敗，都要恢復按鈕
          submitBtn.disabled = false;
          submitBtn.textContent = '儲存';
      }
    });
  
    // --- 6. 綁定 AJAX "刪除" 事件 (與之前相同) ---
    
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
                    if (row) row.remove();
                    updateTableIndexes(tableBody);
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

    console.log(`[ListPageHandler] ${config.tableBodyId} 已成功初始化。`);
  }
  
  // 將工廠函式綁定到全域
  window.initializeListPageHandler = initializeListPageHandler;

})();