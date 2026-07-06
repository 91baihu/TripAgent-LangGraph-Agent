/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      // ===== QQ 极简色彩体系 =====
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
          page: "#F5F6F8",
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
      },

      // ===== 字体 =====
      fontFamily: {
        sans: [
          '"PingFang SC"',
          '"Microsoft YaHei"',
          '"Hiragino Sans GB"',
          "-apple-system",
          "sans-serif",
        ],
      },
      fontSize: {
        h1: ["24px", { lineHeight: "32px", fontWeight: "700" }],
        h2: ["20px", { lineHeight: "28px", fontWeight: "600" }],
        h3: ["17px", { lineHeight: "24px", fontWeight: "500" }],
        body: ["15px", { lineHeight: "22px", fontWeight: "400" }],
        caption: ["13px", { lineHeight: "18px", fontWeight: "400" }],
        small: ["11px", { lineHeight: "16px", fontWeight: "400" }],
      },

      // ===== 圆角（QQ 特色：Button/Input 用 10px） =====
      borderRadius: {
        button: "10px",
        input: "10px",
        card: "12px",
        "card-lg": "16px",
        bubble: "18px",
        tag: "6px",
        modal: "20px",
      },

      // ===== 阴影（极轻） =====
      boxShadow: {
        card: "0 2px 8px rgba(0,0,0,0.04)",
        "card-hover": "0 4px 12px rgba(0,0,0,0.06)",
        modal: "0 8px 24px rgba(0,0,0,0.10)",
        button: "0 4px 10px rgba(18,183,245,0.25)",
        nav: "0 1px 0 0 rgba(0,0,0,0.04)",
      },

      // ===== 间距（8px 体系，Tailwind 默认是 4px） =====
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
    },
  },
  plugins: [],
};
