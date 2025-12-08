// apps/core/static/core/js/utils.js

/**
 * 通用的 AJAX 請求函數
 * 封裝 fetch API，自動處理 CSRF Token、錯誤處理等
 */
async function sendRequest({
    url,
    method = "GET",
    params = null,
    data = null,
    onSuccess = () => {},
    onError = null,
    onComplete = null,
    showLoadingOverlay = false,
  }) {
    if (!url) {
      console.error("URL is required");
      return;
    }
  
    method = method.toUpperCase();
  
    // 處理 query string 參數
    if (params && typeof params === "object") {
      const query = new URLSearchParams(params).toString();
      url += url.includes("?") ? `&${query}` : `?${query}`;
    }
  
    let headers = {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",  // 標識這是 AJAX 請求
    };
  
    let body = null;
  
    // CSRF Token（Django 安全機制）
    const csrfToken = document.querySelector(
      'input[name="csrfmiddlewaretoken"]'
    )?.value;

    // 對於 POST/PUT/PATCH/DELETE 等需要 CSRF 保護的方法，加入 CSRF token
    if (csrfToken && method !== "GET" && method !== "HEAD" && method !== "OPTIONS") {
      headers["X-CSRFToken"] = csrfToken;
    }

    // 決定資料格式
    if (data && method !== "GET") {
      const isFormData = data instanceof FormData;

      if (isFormData) {
        // 如果是 FormData，不設定 Content-Type（瀏覽器會自動設定）
        if (csrfToken && !data.has("csrfmiddlewaretoken")) {
          data.append("csrfmiddlewaretoken", csrfToken);
        }
        body = data;
      } else {
        // 如果是普通物件，轉為 JSON
        headers["Content-Type"] = "application/json";
        body = JSON.stringify(data);
      }
    }
  
    try {
      // if (showLoadingOverlay) showLoading();
  
      const response = await fetch(url, {
        method,
        headers,
        body,
      });
  
      if (!response.ok) {
        const contentType = response.headers.get("Content-Type");
        const errorData =
          contentType && contentType.includes("application/json")
            ? await response.json()
            : await response.text();
        throw typeof errorData === "string" ? { message: errorData } : errorData;
      }
  
      const contentType = response.headers.get("Content-Type");
      const responseData =
        contentType && contentType.includes("application/json")
          ? await response.json()
          : await response.text();
  
      onSuccess(responseData);
    } catch (error) {
      console.error("Request failed:", error);
      // 優先使用 error.error，然後是 error.message，最後是預設訊息
      const errorMessage = error.error || error.message || "請求失敗";
      if (typeof showNotification === "function") {
        showNotification(errorMessage, "error");
      }
      if (typeof onError === "function") onError(error);
    } finally {
      if (showLoadingOverlay) hideLoading();
      if (typeof onComplete === "function") onComplete();
    }
  }
