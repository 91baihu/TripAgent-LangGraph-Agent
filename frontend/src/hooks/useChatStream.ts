/** SSE 流式对话 Hook */

import { useCallback, useRef } from "react";
import { useChatStore } from "../stores/chatStore";
import { endpoints } from "../services/endpoints";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export function useChatStream() {
  const { addMessage, setStreaming, addToolStep, updateToolResult, clearSteps } =
    useChatStore();
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      const { messages } = useChatStore.getState();

      // 添加用户消息
      addMessage("user", content);
      setStreaming(true);
      clearSteps();

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await fetch(`${API_BASE}${endpoints.chat.stream}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
          },
          body: JSON.stringify({
            messages: [
              ...messages.map((m) => ({ role: m.role, content: m.content })),
              { role: "user", content },
            ],
            stream: true,
          }),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("无法读取响应流");

        const decoder = new TextDecoder();
        let buffer = "";
        let fullReply = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data:")) continue;
            const dataStr = line.slice(5).trim();
            if (!dataStr) continue;

            try {
              const event = JSON.parse(dataStr);
              // SSE 事件类型: tool_call | tool_result | reply | error | done
              const eventType = line.includes("event:")
                ? ""
                : "";

              // 尝试从 SSE 格式解析
              if (typeof event === "object") {
                const type = event.event || "unknown";
                const payload = event.data ? JSON.parse(event.data) : event;

                switch (type) {
                  case "tool_call":
                    addToolStep({
                      step: payload.step,
                      tool: payload.tool,
                      args: payload.args,
                    });
                    break;
                  case "tool_result":
                    updateToolResult(payload.step, payload.result);
                    break;
                  case "reply":
                    fullReply += payload.content;
                    break;
                  case "error":
                    fullReply = `❌ ${payload.message}`;
                    break;
                  case "done":
                    if (fullReply) {
                      addMessage("assistant", fullReply);
                    }
                    break;
                }
              }
            } catch {
              // 跳过解析失败的行
            }
          }
        }

        if (fullReply) {
          addMessage("assistant", fullReply);
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name === "AbortError") return;
        const errorMsg = err instanceof Error ? err.message : "未知错误";
        addMessage("assistant", `❌ 请求失败：${errorMsg}`);
      } finally {
        setStreaming(false);
        abortRef.current = null;
      }
    },
    [addMessage, setStreaming, addToolStep, updateToolResult, clearSteps]
  );

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    setStreaming(false);
  }, [setStreaming]);

  return { sendMessage, cancelStream };
}
