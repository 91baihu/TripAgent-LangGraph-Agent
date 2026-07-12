/** 设备指纹 Hook — 首次访问时生成并缓存，后续从 localStorage 读取 */

import { useEffect, useState } from "react";
import { setDeviceFingerprint } from "../services/api";

let fpPromise: Promise<string> | null = null;

async function loadFingerprint(): Promise<string> {
  const stored = localStorage.getItem("device_fp");
  if (stored) return stored;

  // 动态导入 fingerprintjs（减小首屏体积）
  const FingerprintJS = await import("@fingerprintjs/fingerprintjs");
  const fp = await FingerprintJS.default.load();
  const result = await fp.get();
  const visitorId = result.visitorId;

  setDeviceFingerprint(visitorId);
  return visitorId;
}

export function useDeviceFingerprint() {
  const [fingerprint, setFingerprint] = useState<string | null>(
    localStorage.getItem("device_fp")
  );
  const [loading, setLoading] = useState(!fingerprint);

  useEffect(() => {
    if (fingerprint) {
      setLoading(false);
      return;
    }

    if (!fpPromise) {
      fpPromise = loadFingerprint();
    }

    fpPromise
      .then((fp) => {
        setFingerprint(fp);
        setLoading(false);
      })
      .catch(() => {
        // 指纹生成失败，使用时间戳兜底
        const fallback = `fp_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
        setDeviceFingerprint(fallback);
        setFingerprint(fallback);
        setLoading(false);
      });
  }, [fingerprint]);

  return { fingerprint, loading };
}
