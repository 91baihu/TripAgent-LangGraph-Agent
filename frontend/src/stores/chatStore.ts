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

  // 现有 actions
  addMessage: (role: "user" | "assistant", content: string) => void;
  setStreaming: (v: boolean) => void;
  addToolStep: (step: ToolStep) => void;
  updateToolResult: (stepNum: number, result: string) => void;
  clearSteps: () => void;

  // 🆕 actions
  addGeoRoute: (route: GeoRouteData) => void;
  addRestaurantRanking: (items: RankingItem[]) => void;
  addHotelRanking: (items: HotelRankingItem[]) => void;
  clearVisualData: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  toolSteps: [],
  geoRoutes: [],
  restaurantRankings: [],
  hotelRankings: [],

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
      geoRoutes: [],
      restaurantRankings: [],
      hotelRankings: [],
    }),

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
    }),
}));
