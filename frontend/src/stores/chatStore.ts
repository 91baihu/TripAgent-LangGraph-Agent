/** 对话状态管理 — Zustand（含可视化数据状态） */

import { create } from "zustand";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

interface ToolStep {
  step: number;
  tool: string;
  args: Record<string, unknown>;
  result?: string;
}

// 🌤️ 天气数据
export interface WeatherData {
  city: string;
  condition: string;
  temperature: string;
  humidity: string;
  wind: string;
  details: string;
}

// 🆕 可视化数据类型
export interface GeoRouteData {
  spots: Array<{ name: string; lat: number; lng: number; order: number }>;
  distance_km: number;
  duration_min: number;
  transport: string;
}

export interface RankingItem {
  rank: number;
  name: string;
  rating: number;
  price_per_person: number;
  distance_m: number;
  type: string;
  address: string;
}

export interface HotelRankingItem {
  rank: number;
  name: string;
  rating: number;
  price_per_night: number;
  distance_m: number;
  type: string;
  feature: string;
  address: string;
}

interface ChatState {
  // 现有字段
  messages: ChatMessage[];
  isStreaming: boolean;
  toolSteps: ToolStep[];

  // 🆕 可视化数据
  geoRoutes: GeoRouteData[];
  restaurantRankings: RankingItem[][];
  hotelRankings: HotelRankingItem[][];

  // 🌤️ 天气
  weatherData: WeatherData | null;

  // 💬 流式回复（增量显示）
  streamingReply: string;

  // 🔍 推理面板
  traceExpanded: boolean;

  // 📋 步骤折叠（方案A）
  stepsCollapsed: boolean;

  // 📊 检索进度（方案C）
  progressPhase: string;
  progressPercent: number;

  // 现有 actions
  addMessage: (role: "user" | "assistant", content: string) => void;
  setStreaming: (v: boolean) => void;
  addToolStep: (step: ToolStep) => void;
  updateToolResult: (stepNum: number, result: string) => void;
  clearSteps: () => void;
  collapseSteps: () => void;
  expandSteps: () => void;
  setProgress: (phase: string, percent: number) => void;

  // 🆕 actions
  addGeoRoute: (route: GeoRouteData) => void;
  addRestaurantRanking: (items: RankingItem[]) => void;
  addHotelRanking: (items: HotelRankingItem[]) => void;
  clearVisualData: () => void;

  // 🌤️ actions
  setWeatherData: (data: WeatherData) => void;

  // 💬 流式回复 actions
  setStreamingReply: (content: string) => void;
  finalizeStreamingReply: () => void;

  // 🔍 推理面板 actions
  toggleTrace: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  toolSteps: [],
  geoRoutes: [],
  restaurantRankings: [],
  hotelRankings: [],
  weatherData: null,
  streamingReply: "",
  traceExpanded: false,
  stepsCollapsed: false,
  progressPhase: "",
  progressPercent: 0,

  addMessage: (role, content) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
          role,
          content,
          timestamp: Date.now(),
        },
      ],
    })),

  setStreaming: (v) => set({ isStreaming: v }),

  addToolStep: (step) =>
    set((state) => ({
      toolSteps: [...state.toolSteps, step],
    })),

  updateToolResult: (stepNum, result) =>
    set((state) => ({
      toolSteps: state.toolSteps.map((s) =>
        s.step === stepNum ? { ...s, result } : s
      ),
    })),

  clearSteps: () =>
    set({
      toolSteps: [],
      stepsCollapsed: false,
      progressPhase: "",
      progressPercent: 0,
      // 清空旧可视化数据（新查询时替换）
      geoRoutes: [],
      restaurantRankings: [],
      hotelRankings: [],
      weatherData: null,
    }),

  // 📋 步骤折叠（方案A）
  collapseSteps: () => set({ stepsCollapsed: true }),
  expandSteps: () => set({ stepsCollapsed: false }),

  // 📊 检索进度（方案C）
  setProgress: (phase, percent) =>
    set({ progressPhase: phase, progressPercent: percent }),

  // 🆕 可视化数据 actions
  addGeoRoute: (route) =>
    set((state) => ({
      geoRoutes: [...state.geoRoutes, route],
    })),

  addRestaurantRanking: (items) =>
    set((state) => ({
      restaurantRankings: [...state.restaurantRankings, items],
    })),

  addHotelRanking: (items) =>
    set((state) => ({
      hotelRankings: [...state.hotelRankings, items],
    })),

  clearVisualData: () =>
    set({
      geoRoutes: [],
      restaurantRankings: [],
      hotelRankings: [],
      weatherData: null,
    }),

  // 🌤️ 天气
  setWeatherData: (data) => set({ weatherData: data }),

  // 💬 流式回复
  setStreamingReply: (content) => set({ streamingReply: content }),
  finalizeStreamingReply: () =>
    set((state) => {
      if (!state.streamingReply) return { streamingReply: "" };
      return {
        messages: [
          ...state.messages,
          {
            id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            role: "assistant",
            content: state.streamingReply,
            timestamp: Date.now(),
          },
        ],
        streamingReply: "",
      };
    }),

  // 🔍 推理面板
  toggleTrace: () =>
    set((state) => ({ traceExpanded: !state.traceExpanded })),
}));
