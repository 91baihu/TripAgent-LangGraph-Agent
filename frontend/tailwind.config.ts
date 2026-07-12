/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      // ===== QQ 极简色彩体系（保留向后兼容） =====
      colors: {
        primary: {
          DEFAULT: "#12B7F5", // QQ 蓝
          hover: "#0E9FD6",
          light: "#E8F7FE",
          shadow: "rgba(18,183,245,0.25)",
        },
        text: {
          primary: "#1A1C1E",
          secondary: "#6B6F75",
          tertiary: "#B0B3B8",
          inverse: "#FFFFFF",
        },
        surface: {
          page: "#E8E4DC",   // Demo V3 暖灰背景
          card: "#FFFFFF",
          input: "#F0F1F3",
        },
        semantic: {
          success: "#07C160",
          warning: "#FA9D3B",
          error: "#FA5151",
          link: "#576B95",
        },
        divider: "#EDEDEF",

        // 🆕 Demo V3 暖色调色板（编辑风格）
        ink: {
          DEFAULT: "#1A1D20",
          secondary: "#4A5568",
          tertiary: "#8899AA",
        },
        teal: {
          DEFAULT: "#0D9488",
          dark: "#0F766E",
          light: "#CCFBF1",
        },
        rust: {
          DEFAULT: "#E85D3F",
          light: "#FEF2EE",
        },
        sand: {
          DEFAULT: "#FBF7F2",
          dark: "#F0EAE0",
          bg: "#E8E4DC",
        },
        warm: {
          border: "#E8E3DD",
          border2: "#F2EFEB",
        },
      },

      // ===== 字体（新增衬线标题） =====
      fontFamily: {
        sans: [
          '"Inter"',
          '"PingFang SC"',
          '"Microsoft YaHei"',
          '"Hiragino Sans GB"',
          "-apple-system",
          "sans-serif",
        ],
        serif: [
          '"Noto Serif SC"',
          '"STSong"',
          '"SimSun"',
          "serif",
        ],
      },
      fontSize: {
        h1: ["24px", { lineHeight: "32px", fontWeight: "700" }],
        h2: ["20px", { lineHeight: "28px", fontWeight: "600" }],
        h3: ["17px", { lineHeight: "24px", fontWeight: "500" }],
        h4: ["15px", { lineHeight: "22px", fontWeight: "600" }],
        body: ["15px", { lineHeight: "22px", fontWeight: "400" }],
        caption: ["13px", { lineHeight: "18px", fontWeight: "400" }],
        small: ["11px", { lineHeight: "16px", fontWeight: "400" }],
      },

      // ===== 圆角（新增 xs/xl 档位） =====
      borderRadius: {
        button: "10px",
        input: "10px",
        card: "12px",
        "card-lg": "16px",
        bubble: "18px",
        tag: "6px",
        modal: "20px",
        xs: "6px",
        xl: "32px",
      },

      // ===== 阴影 =====
      boxShadow: {
        card: "0 2px 8px rgba(0,0,0,0.04)",
        "card-hover": "0 4px 12px rgba(0,0,0,0.06)",
        modal: "0 8px 24px rgba(0,0,0,0.10)",
        button: "0 4px 10px rgba(18,183,245,0.25)",
        nav: "0 1px 0 0 rgba(0,0,0,0.04)",
        // 🆕 Demo 风格阴影
        "warm-sm": "0 1px 3px rgba(26,29,32,0.06)",
        "warm-md": "0 4px 16px rgba(26,29,32,0.08)",
        "warm-lg": "0 12px 32px rgba(26,29,32,0.10)",
      },

      // ===== 间距（8px 体系） =====
      spacing: {
        0: "0",
        1: "4px",
        2: "8px",
        3: "12px",
        4: "16px",
        5: "20px",
        6: "24px",
        8: "32px",
        12: "48px",
      },

      // 🆕 动画关键帧
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        breathe: {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.04)" },
        },
        "pulse-ring": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(13,148,136,0.3)" },
          "50%": { boxShadow: "0 0 0 8px rgba(13,148,136,0)" },
        },
        "dot-bounce": {
          "0%, 80%, 100%": { transform: "scale(0.3)", opacity: "0.3" },
          "40%": { transform: "scale(1)", opacity: "1" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "fade-out": {
          from: { opacity: "1" },
          to: { opacity: "0" },
        },
        "fade-up": {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.94)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "slide-right": {
          from: { opacity: "0", transform: "translateX(-12px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        // 🆕 天气粒子动效
        "sun-ray": {
          "0%": { opacity: "0", transform: "translate(0,0) scale(0)" },
          "50%": { opacity: "0.6", transform: "translate(var(--tw-drift-x,20px),var(--tw-drift-y,-15px)) scale(0.8)" },
          "100%": { opacity: "0", transform: "translate(calc(var(--tw-drift-x,20px)*2),calc(var(--tw-drift-y,-15px)*2)) scale(0)" },
        },
        "rain-drop": {
          "0%": { transform: "translateY(-40px)", opacity: "0" },
          "20%": { opacity: "0.5" },
          "100%": { transform: "translateY(140px)", opacity: "0" },
        },
        "snow-fall": {
          "0%": { transform: "translateY(-20px) rotate(0deg)", opacity: "0" },
          "10%": { opacity: "0.8" },
          "100%": { transform: "translateY(140px) rotate(360deg)", opacity: "0" },
        },
        "cloud-drift": {
          "0%": { transform: "translateX(-30px)", opacity: "0.3" },
          "50%": { opacity: "0.6" },
          "100%": { transform: "translateX(30px)", opacity: "0.3" },
        },
        "temp-pulse": {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.03)" },
        },
        "gradient-shift": {
          "0%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
          "100%": { backgroundPosition: "0% 50%" },
        },
      },
      animation: {
        shimmer: "shimmer 1.6s ease-in-out infinite",
        breathe: "breathe 3s ease-in-out infinite",
        "pulse-ring": "pulse-ring 2s infinite",
        "dot-bounce": "dot-bounce 1.3s ease-in-out infinite",
        "fade-in": "fade-in 0.3s cubic-bezier(0.4,0,0.2,1) both",
        "fade-out": "fade-out 0.2s ease-in forwards",
        "fade-up": "fade-up 0.4s cubic-bezier(0.4,0,0.2,1) both",
        "scale-in": "scale-in 0.3s cubic-bezier(0.34,1.56,0.64,1) both",
        "slide-right": "slide-right 0.3s cubic-bezier(0.4,0,0.2,1) both",
        "sun-ray": "sun-ray 3s ease-in-out infinite",
        "rain-drop": "rain-drop 0.8s linear infinite",
        "snow-fall": "snow-fall 4s linear infinite",
        "cloud-drift": "cloud-drift 6s ease-in-out infinite",
        "temp-pulse": "temp-pulse 6s ease-in-out infinite",
        "gradient-shift": "gradient-shift 8s ease infinite",
      },
    },
  },
  plugins: [],
};
