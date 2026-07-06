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
    collapseSteps,
    setProgress,
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
        let sseEventType = ""; // 跟踪 SSE event: 行类型

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            // 跟踪 SSE event: 行（sse-starlette 发送的标准格式）
            if (line.startsWith("event:")) {
              sseEventType = line.slice(6).trim();
              continue;
            }
            if (!line.startsWith("data:")) continue;
            const dataStr = line.slice(5).trim();
            if (!dataStr) continue;

            try {
              const data = JSON.parse(dataStr);

              if (typeof data === "object") {
                const type = sseEventType || data.event || "unknown";
                sseEventType = ""; // 消费后重置
                // data 本身就是 payload（sse-starlette 将 event.data 序列化到 data: 行）
                const payload = data;

                switch (type) {
                  case "tool_call":
                    addToolStep({
                      step: payload.step,
                      tool: payload.tool,
                      args: payload.args,
                    });
                    // 更新进度条（方案C）
                    {
                      const phaseMap: Record<string, string> = {
                        search_attractions: "🔍 正在搜索景点...",
                        get_weather: "🌤️ 正在查询天气...",
                        plan_route: "🗺️ 正在规划路线...",
                        search_restaurants: "🍜 正在搜索美食...",
                        search_hotels: "🏨 正在搜索酒店...",
                      };
                      const phase = phaseMap[payload.tool] || "🔧 正在检索信息...";
                      const { toolSteps } = useChatStore.getState();
                      setProgress(phase, Math.min(90, (toolSteps.length + 1) * 18));
                    }
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
                    setProgress("✍️ 正在生成旅行计划...", 95);
                    break;

                  case "error":
                    finalizeStreamingReply();
                    addMessage(
                      "assistant",
                      `❌ ${payload.message || "未知错误"}`
                    );
                    break;

                  case "geo_data":
                    // 解析可视化数据事件（payload 直接就是 geo 数据对象）
                    try {
                      if (payload.geo_type === "route") {
                        addGeoRoute({
                          spots: payload.spots || [],
                          distance_km: payload.distance_km || 0,
                          duration_min: payload.duration_min || 0,
                          transport: payload.transport || "",
                        });
                      } else if (
                        payload.geo_type === "restaurant_ranking"
                      ) {
                        addRestaurantRanking(payload.items || []);
                      } else if (payload.geo_type === "hotel_ranking") {
                        addHotelRanking(payload.items || []);
                      } else if (payload.geo_type === "weather") {
                        setWeatherData({
                          city: payload.city || "未知",
                          condition: payload.condition || "未知",
                          temperature: payload.temperature || "--",
                          humidity: payload.humidity || "--",
                          wind: payload.wind || "--",
                          details: payload.details || "",
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
                    // 进度条完成 → 0.5s 后清除
                    setProgress("✅ 完成!", 100);
                    setTimeout(() => setProgress("", 0), 800);
                    // 2s 后折叠工具步骤（方案A）
                    setTimeout(() => collapseSteps(), 2000);
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
      collapseSteps,
      setProgress,
    ]
  );

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    setStreaming(false);
  }, [setStreaming]);

  return { sendMessage, cancelStream };
}
