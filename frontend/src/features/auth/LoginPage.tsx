/** 登录页 — QQ 极简风格 */

import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Input } from "../../components/Input/Input";
import { Button } from "../../components/Button/Button";
import { useAuthStore } from "../../stores/authStore";
import { showToast } from "../../components/Toast/ToastContainer";

export function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const { login, register, isLoading } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  // 登录成功后回跳原页面
  const from = (location.state as { from?: string })?.from || "/";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (isRegister) {
        await register(email, password, nickname || undefined);
        showToast("注册成功！");
      } else {
        await login(email, password);
        showToast("登录成功！");
      }
      navigate(from);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "操作失败";
      showToast(msg, "error");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-dvh px-6 auth-bg-gradient animate-gradient-shift">
      {/* Logo */}
      <div
        className="
          w-[68px] h-[68px] rounded-2xl flex items-center justify-center
          bg-sand shadow-warm-sm mb-6
        "
      >
        <span className="text-[1.8rem]">✈️</span>
      </div>

      <h1 className="font-serif text-[1.8rem] font-black text-text-primary mb-1">
        {isRegister ? "创建账号" : "欢迎回来"}
      </h1>
      <p className="text-body text-ink-secondary mb-8">
        {isRegister ? "注册 TripAgent，开始旅行规划" : "登录 TripAgent 账号"}
      </p>

      {/* 表单 */}
      <form onSubmit={handleSubmit} className="w-full max-w-[320px] flex flex-col gap-3">
        {isRegister && (
          <Input
            label="昵称"
            placeholder="你的称呼（选填）"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
          />
        )}
        <Input
          label="邮箱"
          type="email"
          placeholder="your@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Input
          label="密码"
          type="password"
          placeholder="至少 8 位密码"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <Button type="submit" loading={isLoading} className="w-full">
          {isRegister ? "注册" : "登录"}
        </Button>
      </form>

      {/* 切换登录/注册 */}
      <button
        onClick={() => setIsRegister(!isRegister)}
        className="mt-[18px] text-sm text-ink-secondary hover:text-text-primary hover:underline transition-colors bg-transparent border-none cursor-pointer font-medium"
      >
        {isRegister ? "已有账号？登录" : "没有账号？注册"}
      </button>
    </div>
  );
}
