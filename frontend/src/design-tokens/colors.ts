/** TripAgent 完整色彩常量 — QQ 极简 + Demo V3 暖色调 */

export const colors = {
  // ===== Demo V3 暖色调色板（编辑风格） =====
  // 主文字
  ink: "#1A1D20",
  inkSecondary: "#4A5568",
  inkTertiary: "#8899AA",

  // 主色调
  teal: "#0D9488",
  tealDark: "#0F766E",
  tealLight: "#CCFBF1",

  // 强调色
  rust: "#E85D3F",
  rustLight: "#FEF2EE",

  // 暖色背景
  sand: "#FBF7F2",
  sandDark: "#F0EAE0",
  sandBg: "#E8E4DC",

  // 边框
  warmBorder: "#E8E3DD",
  warmBorder2: "#F2EFEB",

  // 白色
  white: "#FFFFFF",

  // ===== QQ 极简色彩（保留向后兼容） =====
  primary: "#12B7F5",
  primaryHover: "#0E9FD6",
  primaryLight: "#E8F7FE",

  // 文字
  textPrimary: "#1A1C1E",
  textSecondary: "#6B6F75",
  textTertiary: "#B0B3B8",
  textInverse: "#FFFFFF",

  // 背景
  pageBg: "#F5F6F8",
  cardBg: "#FFFFFF",
  inputBg: "#F0F1F3",

  // 语义色
  success: "#07C160",
  warning: "#FA9D3B",
  error: "#FA5151",
  link: "#576B95",

  // 分割
  divider: "#EDEDEF",
} as const;

export type ColorKey = keyof typeof colors;
