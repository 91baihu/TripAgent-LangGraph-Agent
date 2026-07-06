/** SSE 流式对话 Hook — 增量回复 + 天气解析 + 可视化数据 */

import { useCallback, useRef } from "react";
import { useChatStore, type WeatherData } from "../stores/chatStore";
import { endpoints } from "../services/endpoints";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

/** 从 get_weather 工具返回的 Markdown 文本中解析天气数据 */
function parseWeatherFromText(text: string): WeatherData | null {
  try {
    // 尝试匹配结构化天气数据
    const cityMatch = text.match(/([^\s]+)\s*天气/);
    const tempMatch = text.match(/([+-]?\d+)\s*°C/);
    const condMatch = text.match(/(?:天气[：:]?\s*)([^\n]+)/);
    const humMatch = text.match(/湿度[：:]?\s*(\d+%|[^\s]+)/);
    const windMatch = text.match(/风[：:]?\s*([^\n]+)/);

    return {
      city: cityMatch?.[1] || "未知",
      condition: condMatch?.[1]?.trim() || "未知",
      temperature: tempMatch ? `${tempMatch[1]}°C` : "--",
      humidity: humMatch?.[1] || "--",
      wind: windMatch?.[1] || "--",
      details: text,
    };
  } catch {
    return null;
  }
}

export function useChatStream() {
  const {
    addMessage,
    setStreaming,
    addToolStep,
    updateToolResult,
    clearSteps,
    addGeoRoute,
    addRestaurantRanking,
    addHotelRanking,
    setWeatherData,
    setStreamingReply,
    finalizeStreamingReply,
  } = useChatStore();
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      const { messages } = useChatStore.getState();

      // 添加用户消息
      addMessage("user", content);
      setStreaming(true);
      clearSteps();
      setStreamingReply("");

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

              if (typeof event === "object") {
                const type = event.event || "unknown";
                // 兼容两种格式：data 嵌套和直接 payload
                const payload =
                  typeof event.data === "string"
                    ? JSON.parse(event.data)
                    : event.data || event;

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
                    // 解析天气数据
                    if (payload.tool === "get_weather" && payload.result) {
                      const weather = parseWeatherFromText(payload.result);
                      if (weather) setWeatherData(weather);
                    }
                    break;

                  case "reply":
                    // 增量显示回复文本
                    fullReply = payload.content || "";
                    setStreamingReply(fullReply);
                    break;

                  case "error":
                    finalizeStreamingReply();
                    addMessage(
                      "assistant",
                      `❌ ${payload.message || "未知错误"}`
                    );
                    break;

                  case "geo_data":
                    // 解析可视化数据事件
                    try {
                      const geoPayload =
                        typeof payload.data === "string"
                          ? JSON.parse(payload.data)
                          : payload;
                      if (geoPayload.geo_type === "route") {
                        addGeoRoute({
                          spots: geoPayload.spots || [],
                          distance_km: geoPayload.distance_km || 0,
                          duration_min: geoPayload.duration_min || 0,
                          transport: geoPayload.transport || "",
                        });
                      } else if (
                        geoPayload.geo_type === "restaurant_ranking"
                      ) {
                        addRestaurantRanking(geoPayload.items || []);
                      } else if (geoPayload.geo_type === "hotel_ranking") {
                        addHotelRanking(geoPayload.items || []);
                      } else if (geoPayload.geo_type === "weather") {
                        setWeatherData({
                          city: geoPayload.city || "未知",
                          condition: geoPayload.condition || "未知",
                          temperature: geoPayload.temperature || "--",
                          humidity: geoPayload.humidity || "--",
                          wind: geoPayload.wind || "--",
                          details: geoPayload.details || "",
                        });
                      }
                    } catch {
                      // 解析失败不影响主流程
                    }
                    break;

                  case "done":
                    // 最终化流式回复
                    if (fullReply) {
                      finalizeStreamingReply();
                    }
                    break;
                }
              }
            } catch {
              // 跳过解析失败的行
            }
          }
        }

        // 兜底：如果流结束后有未保存的回复
        if (fullReply) {
          finalizeStreamingReply();
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
    [
      addMessage,
      setStreaming,
      addToolStep,
      updateToolResult,
      clearSteps,
      addGeoRoute,
      addRestaurantRanking,
      addHotelRanking,
      setWeatherData,
      setStreamingReply,
      finalizeStreamingReply,
    ]
  );

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    setStreaming(false);
  }, [setStreaming]);

  return { sendMessage, cancelStream };
}
