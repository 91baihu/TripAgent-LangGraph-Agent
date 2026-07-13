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
    <div className="relative flex flex-col items-center justify-center min-h-dvh px-6 overflow-hidden">
      {/* ===== 多层渐变背景 ===== */}
      {/* 底层：暖色基调 */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#FBF7F2] via-[#F0EAE0] to-[#E8E0D5]" />

      {/* 中层：蓝紫渐变叠加（左上） */}
      <div
        className="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] rounded-full opacity-20 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, rgba(99,132,241,0.3) 0%, rgba(139,162,248,0.1) 40%, transparent 70%)",
        }}
      />

      {/* 中层：暖橙渐变叠加（右下） */}
      <div
        className="absolute -bottom-[10%] -right-[10%] w-[55%] h-[55%] rounded-full opacity-25 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, rgba(232,93,63,0.25) 0%, rgba(245,158,98,0.1) 40%, transparent 70%)",
        }}
      />

      {/* 中层：teal 渐变叠加（右上） */}
      <div
        className="absolute top-[30%] -right-[5%] w-[30%] h-[40%] rounded-full opacity-15 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, rgba(13,148,136,0.3) 0%, rgba(45,212,191,0.08) 50%, transparent 80%)",
        }}
      />

      {/* 装饰性几何图形 */}
      <div className="absolute top-[10%] right-[15%] w-16 h-16 rounded-2xl bg-white/15 rotate-12 backdrop-blur-sm border border-white/20" />
      <div className="absolute bottom-[20%] left-[10%] w-10 h-10 rounded-full bg-white/10 backdrop-blur-sm border border-white/15" />
      <div className="absolute top-[35%] left-[8%] w-6 h-6 rounded-md bg-teal/10 rotate-45 backdrop-blur-sm" />

      {/* ===== 登录卡片 ===== */}
      <div
        className="
          relative w-full max-w-[380px]
          bg-white/75 backdrop-blur-xl
          rounded-[24px] shadow-warm-lg
          border border-white/60
          p-8 animate-fade-up
        "
      >
        {/* Logo */}
        <div className="flex flex-col items-center mb-6">
          <div
            className="
              w-[64px] h-[64px] rounded-2xl flex items-center justify-center
              bg-gradient-to-br from-amber-100 to-orange-100
              shadow-warm-sm mb-4
            "
          >
            <span className="text-[1.7rem]">✈️</span>
          </div>
          <h1 className="font-serif text-[1.6rem] font-black text-text-primary">
            {isRegister ? "创建账号" : "欢迎回来"}
          </h1>
          <p className="text-sm text-ink-tertiary mt-1">
            {isRegister
              ? "注册 TripAgent，开启智能旅行规划"
              : "登录 TripAgent，继续你的旅行计划"}
          </p>
        </div>

        {/* 登录方式切换 Tab（仅登录模式） */}
        {!isRegister && (
          <div className="flex bg-sand rounded-button p-0.5 mb-5">
            <button
              onClick={() => setLoginMode("email")}
              className={`
                flex-1 h-9 text-sm font-medium rounded-[9px] transition-all duration-200
                border-none cursor-pointer
                ${loginMode === "email"
                  ? "bg-white text-text-primary shadow-warm-sm"
                  : "bg-transparent text-ink-tertiary hover:text-ink-secondary"
                }
              `}
            >
              📧 邮箱
            </button>
            <button
              onClick={() => setLoginMode("phone")}
              className={`
                flex-1 h-9 text-sm font-medium rounded-[9px] transition-all duration-200
                border-none cursor-pointer
                ${loginMode === "phone"
                  ? "bg-white text-text-primary shadow-warm-sm"
                  : "bg-transparent text-ink-tertiary hover:text-ink-secondary"
                }
              `}
            >
              📱 手机号
            </button>
          </div>
        )}

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {/* 昵称（仅注册） */}
          {isRegister && (
            <Input
              label="昵称"
              placeholder="你的称呼（选填）"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
            />
          )}

          {/* 邮箱输入（邮箱模式 或 注册邮箱模式） */}
          {(loginMode === "email" || isRegister) && (
            <Input
              label="邮箱"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required={loginMode === "email" || isRegister}
            />
          )}

          {/* 手机号输入（手机登录模式） */}
          {loginMode === "phone" && !isRegister && (
            <Input
              label="手机号"
              type="tel"
              placeholder="请输入手机号"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              prefix="+86"
              required
            />
          )}

          {/* 注册时手机号（选填） */}
          {isRegister && (
            <Input
              label="手机号（选填）"
              type="tel"
              placeholder="用于手机号登录（选填）"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              prefix="+86"
            />
          )}

          {/* 密码 */}
          <Input
            label="密码"
            type="password"
            placeholder="至少 8 位密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {/* 验证码（仅注册） */}
          {isRegister && (
            <div className="w-full">
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
                    rounded-input border border-warm-border
                    whitespace-nowrap transition-all duration-200
                    disabled:opacity-50 disabled:cursor-not-allowed
                    hover:border-ink-tertiary
                    bg-sand text-ink-secondary
                    cursor-pointer flex-shrink-0
                  "
                >
                  {codeCountdown > 0 ? `${codeCountdown}s` : codeSent ? "重新发送" : "发送验证码"}
                </button>
              </div>
            </div>
          )}

          <Button type="submit" loading={isLoading} className="w-full mt-1">
            {isRegister ? "注册" : "登录"}
          </Button>
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
            mt-5 w-full text-sm text-ink-secondary hover:text-text-primary
            transition-colors bg-transparent border-none cursor-pointer font-medium
          "
        >
          {isRegister ? "已有账号？登录" : "没有账号？注册"}
        </button>

        {/* 游客入口 */}
        <div className="mt-4 pt-4 border-t border-warm-border2 text-center">
          <button
            onClick={() => navigate("/")}
            className="
              text-xs text-ink-tertiary hover:text-ink-secondary
              transition-colors bg-transparent border-none cursor-pointer
            "
          >
            先看看 → 游客体验模式
          </button>
        </div>
      </div>
    </div>
  );
}
