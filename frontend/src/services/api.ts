/** API 请求封装 — fetch + JWT 自动注入 + Token 自动刷新 */

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

// ===== Token 管理 =====
let isRefreshing = false;
let pendingRequests: Array<{
  resolve: (token: string) => void;
  reject: (err: Error) => void;
}> = [];

function getAccessToken(): string | null {
  return localStorage.getItem("access_token");
}

function getRefreshToken(): string | null {
  return localStorage.getItem("refresh_token");
}

function setTokens(access: string, refresh: string): void {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

function clearTokens(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error("无刷新令牌");
  }

  const response = await fetch(`${BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    clearTokens();
    throw new Error("令牌刷新失败");
  }

  const data = await response.json();
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

async function handleTokenRefresh(): Promise<string> {
  // 如果已在刷新中，等待结果
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      pendingRequests.push({ resolve, reject });
    });
  }

  isRefreshing = true;
  try {
    const newToken = await refreshAccessToken();
    // 通知所有等待中的请求
    pendingRequests.forEach(({ resolve }) => resolve(newToken));
    pendingRequests = [];
    return newToken;
  } catch (err) {
    pendingRequests.forEach(({ reject }) => reject(err as Error));
    pendingRequests = [];
    throw err;
  } finally {
    isRefreshing = false;
  }
}

// ===== 核心请求 =====
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
    const token = getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  let response = await fetch(`${BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  // Token 过期 → 尝试刷新
  if (response.status === 401 && !skipAuth && getRefreshToken()) {
    try {
      const newToken = await handleTokenRefresh();
      // 用新 token 重试原请求
      headers["Authorization"] = `Bearer ${newToken}`;
      response = await fetch(`${BASE_URL}${endpoint}`, {
        ...fetchOptions,
        headers,
      });
    } catch {
      // 刷新失败 → 跳转登录页
      clearTokens();
      window.location.href = "/login";
      throw new ApiError("登录已过期，请重新登录", 401);
    }
  }

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
