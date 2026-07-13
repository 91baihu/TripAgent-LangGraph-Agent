/** 额度状态管理 — Zustand */

import { create } from "zustand";
import { api } from "../services/api";
import { endpoints } from "../services/endpoints";

export interface QuotaStatus {
  is_guest: boolean;
  quota_type: "device" | "account";
  remaining: number;
  total: number;
  percent: number;
  status: "normal" | "warning" | "exhausted";
  plan_name: string;
  message: string;
  is_admin?: boolean;
  unlimited?: boolean;
}

interface QuotaState {
  quota: QuotaStatus | null;
  loading: boolean;
  fetchQuota: () => Promise<void>;
}

export const useQuotaStore = create<QuotaState>((set) => ({
  quota: null,
  loading: false,

  fetchQuota: async () => {
    set({ loading: true });
    try {
      const data = await api.get<QuotaStatus>(endpoints.credits.status);
      set({ quota: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));
