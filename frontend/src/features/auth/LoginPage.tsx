/** 登录页 — 多色彩分层视觉 + 邮箱/手机双渠道 + 验证码注册 */

import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Input } from "../../components/Input/Input";
import { Button } from "../../components/Button/Button";
import { useAuthStore } from "../../stores/authStore";
import { showToast } from "../../components/Toast/ToastContainer";
import { api } from "../../services/api";
import { endpoints } from "../../services/endpoints";

type LoginMode = "email" | "phone";

export function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [loginMode, setLoginMode] = useState<LoginMode>("email");

  // 表单字段
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");

  // 验证码
  const [code, setCode] = useState("");
  const [codeSent, setCodeSent] = useState(false);
  const [codeCountdown, setCodeCountdown] = useState(0);

  const { login, loginWithPhone, register, isLoading } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  // 登录成功后回跳原页面
  const from = (location.state as { from?: string })?.from || "/";

  // 验证码倒计时
  useEffect(() => {
    if (codeCountdown <= 0) return;
    const timer = setTimeout(() => setCodeCountdown(codeCountdown - 1), 1000);
    return () => clearTimeout(timer);
  }, [codeCountdown]);

  // 发送验证码
  const handleSendCode = async () => {
    const target = loginMode === "email" ? email : phone;
    if (!target) {
      showToast(loginMode === "email" ? "请先输入邮箱" : "请先输入手机号", "error");
      return;
    }
    // 邮箱格式校验
    if (loginMode === "email" && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(target)) {
      showToast("请输入正确的邮箱格式", "error");
      return;
    }
    // 手机号格式校验
    if (loginMode === "phone" && !/^1[3-9]\d{9}$/.test(target)) {
      showToast("请输入正确的手机号", "error");
      return;
    }

    try {
      await api.post(
        endpoints.auth.sendCode,
        { target, type: loginMode },
        { skipAuth: true }
      );
      setCodeSent(true);
      setCodeCountdown(60);
      showToast("验证码已发送");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "发送失败";
      showToast(msg, "error");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (isRegister) {
        // 注册需要验证码
        if (!code) {
          showToast("请输入验证码", "error");
          return;
        }
        await register(
          email,
          password,
          nickname || undefined,
          code,
          loginMode === "phone" ? phone : undefined
        );
        showToast("注册成功！");
      } else {
        if (loginMode === "email") {
          await login(email, password);
        } else {
          await loginWithPhone(phone, password);
        }
        showToast("登录成功！");
      }
      navigate(from);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "操作失败";
      showToast(msg, "error");
    }
  };

  return (
    <div className="relative flex flex-col items-center justify-center min-h-dvh px-6 overflow-hidden auth-aurora">
      {/* ===== 极光流动背景 ===== */}
      {/* 暖橙极光（左上） */}
      <div
        className="aurora-blob aurora-drift-1 -top-[15%] -left-[12%] w-[52%] h-[52%] opacity-60"
        style={{
          background:
            "radial-gradient(circle, rgba(232,93,63,0.42) 0%, rgba(245,158,98,0.18) 45%, transparent 72%)",
        }}
      />
      {/* teal 极光（右上） */}
      <div
        className="aurora-blob aurora-drift-2 -top-[10%] -right-[10%] w-[48%] h-[48%] opacity-55"
        style={{
          background:
            "radial-gradient(circle, rgba(13,148,136,0.4) 0%, rgba(45,212,191,0.14) 45%, transparent 72%)",
        }}
      />
      {/* 靛蓝极光（右下） */}
      <div
        className="aurora-blob aurora-drift-3 -bottom-[18%] -right-[6%] w-[46%] h-[46%] opacity-45"
        style={{
          background:
            "radial-gradient(circle, rgba(99,132,241,0.38) 0%, rgba(139,162,248,0.12) 45%, transparent 74%)",
        }}
      />
      {/* 暖金极光（左下） */}
      <div
        className="aurora-blob aurora-drift-1 -bottom-[12%] -left-[8%] w-[40%] h-[42%] opacity-45"
        style={{
          background:
            "radial-gradient(circle, rgba(252,211,77,0.32) 0%, rgba(251,191,36,0.1) 45%, transparent 74%)",
        }}
      />

      {/* 装饰性几何图形（缓慢漂浮） */}
      <div
        className="absolute top-[12%] right-[16%] w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm border border-white/30 float-slow shadow-warm-sm"
        style={{ ["--rot" as string]: "12deg", animationDelay: "0s" }}
      />
      <div
        className="absolute bottom-[22%] left-[11%] w-11 h-11 rounded-full bg-white/15 backdrop-blur-sm border border-white/25 float-slow"
        style={{ ["--rot" as string]: "0deg", animationDelay: "1.4s" }}
      />
      <div
        className="absolute top-[36%] left-[9%] w-7 h-7 rounded-md bg-teal/15 backdrop-blur-sm float-slow"
        style={{ ["--rot" as string]: "45deg", animationDelay: "0.7s" }}
      />

      {/* ===== 登录卡片 ===== */}
      <div
        className="
          relative w-full max-w-[400px]
          bg-white/70 backdrop-blur-2xl
          rounded-[28px] shadow-warm-lg
          border border-white/70
          px-8 py-9 animate-scale-in
        "
        style={{
          boxShadow:
            "0 20px 48px -12px rgba(26,29,32,0.18), 0 0 0 1px rgba(255,255,255,0.5) inset",
        }}
      >
        {/* Logo */}
        <div className="flex flex-col items-center mb-7">
          <div
            className="
              w-[68px] h-[68px] rounded-[20px] flex items-center justify-center
              bg-gradient-to-br from-amber-100 via-orange-100 to-rose-100
              mb-4 logo-glow
            "
          >
            <span className="text-[1.8rem] drop-shadow-sm">✈️</span>
          </div>
          <h1 className="font-serif text-[1.65rem] font-black text-text-primary tracking-tight">
            {isRegister ? "创建账号" : "欢迎回来"}
          </h1>
          <p className="text-sm text-ink-tertiary mt-1.5 text-center">
            {isRegister
              ? "注册 TripAgent，开启智能旅行规划"
              : "登录 TripAgent，继续你的旅行计划"}
          </p>
        </div>

        {/* 登录方式切换 Tab（仅登录模式） */}
        {!isRegister && (
          <div className="relative flex bg-sand-dark/70 rounded-[12px] p-1 mb-5">
            {/* 滑动指示块 */}
            <div
              className="absolute top-1 bottom-1 w-[calc(50%-4px)] rounded-[9px] bg-white shadow-warm-sm transition-transform duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
              style={{
                transform:
                  loginMode === "email" ? "translateX(0)" : "translateX(100%)",
              }}
            />
            <button
              onClick={() => setLoginMode("email")}
              className={`
                relative z-10 flex-1 h-9 text-sm font-medium rounded-[9px] transition-colors duration-200
                border-none cursor-pointer bg-transparent
                ${loginMode === "email" ? "text-text-primary" : "text-ink-tertiary hover:text-ink-secondary"}
              `}
            >
              📧 邮箱
            </button>
            <button
              onClick={() => setLoginMode("phone")}
              className={`
                relative z-10 flex-1 h-9 text-sm font-medium rounded-[9px] transition-colors duration-200
                border-none cursor-pointer bg-transparent
                ${loginMode === "phone" ? "text-text-primary" : "text-ink-tertiary hover:text-ink-secondary"}
              `}
            >
              📱 手机号
            </button>
          </div>
        )}

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
          {/* 昵称（仅注册） */}
          {isRegister && (
            <div className="field-rise" style={{ animationDelay: "40ms" }}>
              <Input
                label="昵称"
                placeholder="你的称呼（选填）"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
              />
            </div>
          )}

          {/* 邮箱输入（邮箱模式 或 注册邮箱模式） */}
          {(loginMode === "email" || isRegister) && (
            <div className="field-rise" style={{ animationDelay: "80ms" }}>
              <Input
                label="邮箱"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required={loginMode === "email" || isRegister}
              />
            </div>
          )}

          {/* 手机号输入（手机登录模式） */}
          {loginMode === "phone" && !isRegister && (
            <div className="field-rise" style={{ animationDelay: "80ms" }}>
              <Input
                label="手机号"
                type="tel"
                placeholder="请输入手机号"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                prefix="+86"
                required
              />
            </div>
          )}

          {/* 注册时手机号（选填） */}
          {isRegister && (
            <div className="field-rise" style={{ animationDelay: "120ms" }}>
              <Input
                label="手机号（选填）"
                type="tel"
                placeholder="用于手机号登录（选填）"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                prefix="+86"
              />
            </div>
          )}

          {/* 密码 */}
          <div className="field-rise" style={{ animationDelay: "160ms" }}>
            <Input
              label="密码"
              type="password"
              placeholder="至少 8 位密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {/* 验证码（仅注册） */}
          {isRegister && (
            <div className="w-full field-rise" style={{ animationDelay: "200ms" }}>
              <label className="block mb-1 text-caption text-text-secondary">
                验证码
              </label>
              <div className="flex gap-2">
                <div className="flex-1">
                  <Input
                    placeholder="请输入验证码"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    required
                  />
                </div>
                <button
                  type="button"
                  onClick={handleSendCode}
                  disabled={codeCountdown > 0}
                  className="
                    h-[44px] px-4 text-sm font-medium
                    rounded-input border-[1.5px] border-warm-border
                    whitespace-nowrap transition-all duration-200
                    disabled:opacity-50 disabled:cursor-not-allowed
                    hover:border-teal hover:text-teal
                    active:scale-[0.97]
                    bg-white/60 text-ink-secondary
                    cursor-pointer flex-shrink-0
                  "
                >
                  {codeCountdown > 0 ? `${codeCountdown}s` : codeSent ? "重新发送" : "发送验证码"}
                </button>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="
              btn-ripple relative w-full h-[46px] mt-2
              rounded-button font-medium text-text-inverse
              bg-gradient-to-r from-ink to-[#2D3238]
              shadow-[0_6px_18px_-6px_rgba(26,29,32,0.5)]
              transition-all duration-200
              hover:shadow-[0_10px_26px_-8px_rgba(26,29,32,0.55)] hover:-translate-y-0.5
              active:translate-y-0 active:scale-[0.98]
              disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0
              flex items-center justify-center gap-2
              cursor-pointer border-none
            "
          >
            {isLoading && (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
                <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
              </svg>
            )}
            {isRegister ? "注 册" : "登 录"}
          </button>
        </form>

        {/* 切换登录/注册 */}
        <button
          onClick={() => {
            setIsRegister(!isRegister);
            setCode("");
            setCodeSent(false);
            setCodeCountdown(0);
          }}
          className="
            group mt-6 w-full text-sm text-ink-secondary hover:text-text-primary
            transition-colors bg-transparent border-none cursor-pointer font-medium
          "
        >
          {isRegister ? "已有账号？" : "没有账号？"}
          <span className="text-teal font-semibold ml-0.5 group-hover:underline underline-offset-2">
            {isRegister ? "去登录" : "去注册"}
          </span>
        </button>

        {/* 游客入口 */}
        <div className="mt-5 pt-5 border-t border-warm-border2 text-center">
          <button
            onClick={() => navigate("/")}
            className="
              group inline-flex items-center gap-1 text-xs text-ink-tertiary hover:text-teal
              transition-colors bg-transparent border-none cursor-pointer
            "
          >
            先看看
            <span className="transition-transform duration-200 group-hover:translate-x-0.5">
              游客体验模式 →
            </span>
          </button>
        </div>
      </div>

      {/* 底部品牌标语 */}
      <p className="relative mt-8 text-xs text-ink-tertiary/70 animate-fade-in" style={{ animationDelay: "300ms" }}>
        © TripAgent · 让每一次旅行都值得期待
      </p>
    </div>
  );
}
