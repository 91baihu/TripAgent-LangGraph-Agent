/** TripAgent 8px 间距体系 */

export const spacing = {
  xs: 4,   // 紧密
  sm: 8,   // 同类元素
  md: 12,  // 相关但不同类
  base: 16, // 卡片内边距
  lg: 20,  // 段落间距
  xl: 24,  // 模块间距
  "2xl": 32, // 大模块
  "3xl": 48, // 页面安全区
} as const;

/** 圆角 */
export const radius = {
  tag: 6,
  button: 10,
  input: 10,
  card: 12,
  cardLg: 16,
  bubble: 18,
  modal: 20,
  full: 9999,
} as const;

/** 组件高度 */
export const heights = {
  button: 44,
  input: 44,
  bottomNav: 56,
  navbar: 56,
  toast: 44,
} as const;
