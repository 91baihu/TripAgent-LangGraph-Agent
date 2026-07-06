/** 高德地图 Hook — 动态加载 JS API，封装 Marker/路线操作
 *
 * 配色映射（来自项目 design-tokens）：
 * - 景点 Marker = primary #12B7F5
 * - 路线       = primary-hover #0E9FD6
 * - 步行路线   = semantic-success #07C160
 * - 餐厅标记   = semantic-warning #FA9D3B
 * - 酒店标记   = #576B95
 */

import { useEffect, useRef, useState, useCallback } from "react";

const COLORS = {
  spot: "#12B7F5",           // 景点标记 → primary
  route: "#0E9FD6",          // 路线 → primary-hover
  walk: "#07C160",           // 步行路线 → semantic-success
  restaurant: "#FA9D3B",      // 餐厅标记 → semantic-warning
  hotel: "#576B95",           // 酒店标记
};

export interface Spot {
  name: string;
  lat: number;
  lng: number;
  order: number;
}

export interface Route {
  from: Spot;
  to: Spot;
  distance_km: number;
  transport: string;
}

// 声明 window.AMap 类型
declare global {
  interface Window {
    AMap: any;
    _amap_loading: boolean;
    _amap_callbacks: Array<() => void>;
  }
}

/**
 * 动态加载高德 JS API SDK
 * 文档：https://lbs.amap.com/api/javascript-api-v2/summary
 */
function loadAmapSDK(): Promise<void> {
  return new Promise((resolve) => {
    // 已加载
    if (window.AMap) {
      resolve();
      return;
    }

    // 正在加载，排队等待
    if (window._amap_loading) {
      window._amap_callbacks.push(resolve);
      return;
    }

    window._amap_loading = true;
    window._amap_callbacks = [resolve];

    const key = import.meta.env.VITE_AMAP_JS_KEY || "";
    const script = document.createElement("script");
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${key}&plugin=AMap.PolylineEditor,AMap.MoveAnimation`;
    script.async = true;
    script.onload = () => {
      window._amap_loading = false;
      window._amap_callbacks.forEach((cb) => cb());
      window._amap_callbacks = [];
    };
    script.onerror = () => {
      // 加载失败也 resolve，避免阻塞
      window._amap_loading = false;
      window._amap_callbacks.forEach((cb) => cb());
      window._amap_callbacks = [];
    };
    document.head.appendChild(script);
  });
}

export function useAmap(containerId: string) {
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const polylinesRef = useRef<any[]>([]);
  const [loaded, setLoaded] = useState(false);

  // 加载 SDK 并初始化地图
  useEffect(() => {
    let cancelled = false;

    const init = async () => {
      await loadAmapSDK();
      if (cancelled || !window.AMap) return;

      const container = document.getElementById(containerId);
      if (!container) return;

      const map = new window.AMap.Map(containerId, {
        zoom: 12,
        center: [116.3972, 39.9163], // 默认北京
        mapStyle: "amap://styles/light",
      });
      mapRef.current = map;
      setLoaded(true);
    };

    init();

    return () => {
      cancelled = true;
      // 清理地图实例
      if (mapRef.current) {
        mapRef.current.destroy?.();
        mapRef.current = null;
      }
    };
  }, [containerId]);

  // 添加景点标记
  const addSpotMarker = useCallback((spot: Spot) => {
    if (!mapRef.current || !window.AMap) return null;

    const marker = new window.AMap.Marker({
      position: [spot.lng, spot.lat],
      content: `
        <div style="
          background: ${COLORS.spot}; color: white;
          width: 28px; height: 28px; border-radius: 14px;
          display: flex; align-items: center; justify-content: center;
          font-size: 12px; font-weight: 700;
          box-shadow: 0 2px 6px rgba(18,183,245,0.3);
          border: 2px solid white;
        ">${spot.order}</div>
      `,
      offset: new window.AMap.Pixel(-14, -14),
    });
    marker.setMap(mapRef.current);

    // 点击弹窗
    marker.on("click", () => {
      const info = new window.AMap.InfoWindow({
        content: `<div style="padding:4px 8px;font-size:14px;font-family:'PingFang SC'"><b>${spot.name}</b></div>`,
        offset: new window.AMap.Pixel(0, -35),
      });
      info.open(mapRef.current, [spot.lng, spot.lat]);
    });

    markersRef.current.push(marker);
    return marker;
  }, []);

  // 清除所有标记
  const clearMarkers = useCallback(() => {
    markersRef.current.forEach((m) => m.setMap?.(null));
    markersRef.current = [];
  }, []);

  // 绘制路线（步行=绿实线, 驾车=蓝虚线）
  const addRoute = useCallback(
    (from: Spot, to: Spot, transport: string) => {
      if (!mapRef.current || !window.AMap) return null;

      const colorMap: Record<string, string> = {
        "步行": COLORS.walk,
        "骑车": COLORS.walk,
        "骑行/公交": COLORS.route,
        "驾车": COLORS.route,
        "打车": COLORS.route,
        "打车/驾车": COLORS.route,
        "地铁": COLORS.route,
        "公交": COLORS.route,
      };
      const color = colorMap[transport] || COLORS.route;
      const isWalk = transport === "步行";

      const polyline = new window.AMap.Polyline({
        path: [
          [from.lng, from.lat],
          [to.lng, to.lat],
        ],
        strokeColor: color,
        strokeWeight: 3,
        strokeOpacity: 0.7,
        strokeStyle: isWalk ? "solid" : "dashed",
        showDir: true,
      });
      polyline.setMap(mapRef.current);
      polylinesRef.current.push(polyline);
      return polyline;
    },
    []
  );

  // 清除所有路线
  const clearRoutes = useCallback(() => {
    polylinesRef.current.forEach((p) => p.setMap?.(null));
    polylinesRef.current = [];
  }, []);

  // 清除全部
  const clearAll = useCallback(() => {
    clearMarkers();
    clearRoutes();
  }, [clearMarkers, clearRoutes]);

  // 调整地图视野以包含所有 spots
  const fitBounds = useCallback(
    (spots: Spot[]) => {
      if (!mapRef.current || !window.AMap || spots.length === 0) return;

      const bounds = new window.AMap.Bounds();
      spots.forEach((s) => {
        bounds.extend([s.lng, s.lat]);
      });
      mapRef.current.setBounds(bounds, false, [60, 60, 60, 60]);
    },
    []
  );

  return {
    map: mapRef,
    loaded,
    addSpotMarker,
    addRoute,
    clearMarkers,
    clearRoutes,
    clearAll,
    fitBounds,
  };
}
