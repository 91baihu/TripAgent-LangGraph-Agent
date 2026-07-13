/** 认证状态管理 — Zustand */

import { create } from "zustand";
import { api } from "../services/api";
import { endpoints } from "../services/endpoints";

interface User {
  id: string;
  email: string;
  nickname: string;
  role: string;
  phone?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (email: string, password: string) => Promise<void>;
  loginWithPhone: (phone: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    nickname?: string,
    code?: string,
    phone?: string
  ) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem("access_token"),
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const data = await api.post<{
        access_token: string;
        refresh_token: string;
      }>(endpoints.auth.login, {
        email,
        password,
        login_type: "email",
      }, { skipAuth: true });

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      set({ isAuthenticated: true });

      // 获取用户信息
      const user = await api.get<User>(endpoints.auth.me);
      set({ user });
    } finally {
      set({ isLoading: false });
    }
  },

  loginWithPhone: async (phone, password) => {
    set({ isLoading: true });
    try {
      const data = await api.post<{
        access_token: string;
        refresh_token: string;
      }>(endpoints.auth.login, {
        phone,
        password,
        login_type: "phone",
      }, { skipAuth: true });

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      set({ isAuthenticated: true });

      const user = await api.get<User>(endpoints.auth.me);
      set({ user });
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (email, password, nickname, code, phone) => {
    set({ isLoading: true });
    try {
      const data = await api.post<{
        access_token: string;
        refresh_token: string;
      }>(endpoints.auth.register, {
        email,
        password,
        nickname,
        code,
        phone,
      }, { skipAuth: true });

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      set({ isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false });
  },

  fetchMe: async () => {
    try {
      const user = await api.get<User>(endpoints.auth.me);
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    }
  },
}));
