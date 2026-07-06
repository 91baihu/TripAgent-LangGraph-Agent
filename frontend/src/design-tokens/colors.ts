/** TripAgent QQ 极简色彩常量 */

export const colors = {
  // 主色
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
