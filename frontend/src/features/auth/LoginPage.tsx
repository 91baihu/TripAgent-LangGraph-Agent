/** 登录页 — QQ 极简风格 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
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
      navigate("/");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "操作失败";
      showToast(msg, "error");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-dvh px-6 bg-surface-page">
      {/* Logo */}
      <div
        className="
          w-16 h-16 rounded-full flex items-center justify-center
          bg-gradient-to-br from-primary to-primary-hover
          shadow-button mb-6
        "
      >
        <span className="text-2xl">✈️</span>
      </div>

      <h1 className="text-h1 text-text-primary mb-1">
        {isRegister ? "创建账号" : "欢迎回来"}
      </h1>
      <p className="text-body text-text-secondary mb-8">
        {isRegister ? "注册 TripAgent，开始智能旅行规划" : "登录你的 TripAgent 账号"}
      </p>

      {/* 表单 */}
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
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
        className="mt-6 text-body text-primary hover:text-primary-hover transition-colors"
      >
        {isRegister ? "已有账号？登录" : "没有账号？注册"}
      </button>
    </div>
  );
}
