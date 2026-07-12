/** 套餐价格页 — 套餐选择 + 购买 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../../components/Button/Button";
import { Card } from "../../components/Card/Card";
import { api } from "../../services/api";
import { endpoints } from "../../services/endpoints";
import { showToast } from "../../components/Toast/ToastContainer";

interface Plan {
  id: string;
  name: string;
  price_cents: number;
  price_display: string;
  monthly_price: string;
  monthly_quota: number;
  features: string[];
  popular: boolean;
}

export function PricingPage() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Plan[]>(endpoints.plans.list)
      .then(setPlans)
      .catch(() => showToast("加载套餐失败", "error"))
      .finally(() => setLoading(false));
  }, []);

  const handleBuy = async (plan: Plan) => {
    if (plan.price_cents === 0) {
      navigate("/");
      return;
    }

    const isLoggedIn = !!localStorage.getItem("access_token");
    if (!isLoggedIn) {
      navigate("/login");
      return;
    }

    setBuying(plan.id);
    try {
      const order = await api.post<{
        order_id: string;
        amount_display: string;
        status: string;
      }>(endpoints.plans.list.replace("/plans", "/orders"), {
        plan_id: plan.id,
        payment_method: "manual",
      });
      showToast(`订单已创建：${order.amount_display}`);
      // 开发环境自动模拟支付
      try {
        await api.post(`/orders/${order.order_id}/pay`);
        showToast(`✅ 购买成功！额度已到账`);
        navigate("/");
      } catch {
        showToast("订单已创建，请联系管理员确认支付", "info");
      }
    } catch (err: any) {
      showToast(err?.message || "购买失败", "error");
    } finally {
      setBuying(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-dvh bg-surface-page flex items-center justify-center">
        <p className="text-ink-tertiary">加载中...</p>
      </div>
    );
  }

  return (
    <div className="min-h-dvh bg-surface-page animate-fade-in">
      {/* Header */}
      <header className="text-center pt-8 pb-4 px-4">
        <button
          onClick={() => navigate(-1)}
          className="absolute top-4 left-4 w-[34px] h-[34px] rounded-full bg-white/80 border border-divider flex items-center justify-center text-sm"
        >
          ←
        </button>
        <h1 className="font-serif text-3xl font-black text-text-primary">
          选择适合你的方案
        </h1>
        <p className="text-ink-secondary mt-2 text-body">
          新用户注册即送 10 次试用额度
        </p>
      </header>

      {/* 套餐卡片 */}
      <div className="max-w-4xl mx-auto px-4 pb-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {plans.map((plan) => (
          <Card
            key={plan.id}
            padding
            className={`relative ${
              plan.popular
                ? "ring-2 ring-accent-blue shadow-lg"
                : "shadow-card"
            }`}
          >
            {plan.popular && (
              <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-accent-blue text-white text-xs font-bold px-3 py-0.5 rounded-full">
                推荐
              </span>
            )}

            <div className="text-center">
              <h3 className="font-serif text-xl font-bold text-text-primary">
                {plan.name}
              </h3>
              <div className="mt-2 mb-1">
                <span className="text-3xl font-black text-text-primary">
                  {plan.price_display}
                </span>
              </div>
              <p className="text-xs text-ink-tertiary">{plan.monthly_price}</p>
            </div>

            <div className="mt-4 pt-4 border-t border-divider">
              <div className="text-center mb-3">
                <span className="text-2xl font-bold text-accent-blue">
                  {plan.monthly_quota}
                </span>
                <span className="text-sm text-ink-tertiary"> 次/月</span>
              </div>

              <ul className="space-y-1.5">
                {plan.features.map((f, i) => (
                  <li
                    key={i}
                    className="text-sm text-ink-secondary flex items-start gap-1.5"
                  >
                    <span className="text-accent-green mt-0.5 flex-shrink-0">
                      ✓
                    </span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-5">
              <Button
                variant={plan.popular ? "primary" : "secondary"}
                className="w-full"
                disabled={buying === plan.id}
                onClick={() => handleBuy(plan)}
              >
                {buying === plan.id
                  ? "处理中..."
                  : plan.price_cents === 0
                  ? "当前方案"
                  : "立即购买"}
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
