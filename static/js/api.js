// لایه ارتباط با REST API.
export const API = (() => {
  const BASE = window.__API_BASE__ || "";   // same-origin

  // تابع برای خواندن کوکی CSRF
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  async function request(path, options = {}) {
    // هدرهای پیش‌فرض
    const headers = {
      "Accept": "application/json",
      ...(options.headers || {}),
    };

    // اگر متد POST یا PUT یا DELETE باشد، توکن CSRF را اضافه کن
    const method = (options.method || "GET").toUpperCase();
    if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
      const csrfToken = getCookie("csrftoken");
      if (csrfToken) {
        headers["X-CSRFToken"] = csrfToken;
      }
    }

    const res = await fetch(`${BASE}${path}`, {
      headers: headers,
      ...options,
    });

    const contentType = res.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
      ? await res.json()
      : await res.text();

    if (!res.ok) {
      const detail = (data && data.detail) || "خطا در ارتباط با سرور";
      throw Object.assign(new Error(detail), { status: res.status, data });
    }
    return data;
  }

  return {
    base: BASE,
    get: (p) => request(p),
    postJSON: (p, body) => request(p, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
    postForm: (p, formData) => request(p, { method: "POST", body: formData }),
  };
})();