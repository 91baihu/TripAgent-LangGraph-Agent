/** API 请求封装 — fetch + JWT 自动注入 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T = unknown>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { skipAuth = false, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };

  // 自动注入 JWT
  if (!skipAuth) {
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    let message = "请求失败";
    try {
      const errorBody = await response.json();
      message = errorBody.detail || errorBody.message || message;
    } catch {}
    throw new ApiError(message, response.status);
  }

  // 204 No Content
  if (response.status === 204) return undefined as T;

  return response.json();
}

// ===== 便捷方法 =====
export const api = {
  get: <T = unknown>(url: string, opts?: RequestOptions) =>
    request<T>(url, { ...opts, method: "GET" }),

  post: <T = unknown>(url: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(url, { ...opts, method: "POST", body: JSON.stringify(body) }),

  patch: <T = unknown>(url: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(url, { ...opts, method: "PATCH", body: JSON.stringify(body) }),

  delete: <T = unknown>(url: string, opts?: RequestOptions) =>
    request<T>(url, { ...opts, method: "DELETE" }),
};

export { ApiError };
