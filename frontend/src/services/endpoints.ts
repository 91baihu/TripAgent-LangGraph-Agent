/** API 端点定义 */

export const endpoints = {
  // 对话
  chat: {
    stream: "/chat/stream",
    sync: "/chat",
    health: "/chat/health",
  },

  // 行程
  trips: {
    list: "/trips",
    create: "/trips",
    get: (id: string) => `/trips/${id}`,
    update: (id: string) => `/trips/${id}`,
    delete: (id: string) => `/trips/${id}`,
    share: (id: string) => `/trips/${id}/share`,
  },

  // 工具调试
  tools: {
    list: "/tools",
    searchAttractions: "/tools/search_attractions",
    getWeather: "/tools/get_weather",
    planRoute: "/tools/plan_route",
    searchRestaurants: "/tools/search_restaurants",
    searchHotels: "/tools/search_hotels",
  },

  // 认证
  auth: {
    register: "/auth/register",
    login: "/auth/login",
    refresh: "/auth/refresh",
    me: "/auth/me",
    sendCode: "/auth/send-code",
  },

  // 额度
  credits: {
    status: "/credits/status",
  },

  // 套餐
  plans: {
    list: "/plans",
  },

  // 会话
  sessions: {
    list: "/sessions",
    get: (id: string) => `/sessions/${id}`,
    messages: (id: string) => `/sessions/${id}/messages`,
    update: (id: string) => `/sessions/${id}`,
    delete: (id: string) => `/sessions/${id}`,
  },

  // 导出
  export: {
    download: (tripId: string, format: string) => `/trips/${tripId}/export?format=${format}`,
    text: (tripId: string) => `/trips/${tripId}/export/text`,
    preview: (tripId: string, format: string = "html") => `/trips/${tripId}/export/preview?format=${format}`,
  },
} as const;
