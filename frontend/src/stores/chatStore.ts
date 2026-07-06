/** 对话状态管理 — Zustand */

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

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  toolSteps: ToolStep[];

  addMessage: (role: "user" | "assistant", content: string) => void;
  setStreaming: (v: boolean) => void;
  addToolStep: (step: ToolStep) => void;
  updateToolResult: (stepNum: number, result: string) => void;
  clearSteps: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  toolSteps: [],

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

  clearSteps: () => set({ toolSteps: [] }),
}));
