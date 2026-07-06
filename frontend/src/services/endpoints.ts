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
  },
} as const;
