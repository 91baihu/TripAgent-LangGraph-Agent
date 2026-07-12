"""额度管理服务 — 游客设备额度 + 登录用户额度

提供额度检查、消费、状态查询。游客绑定设备指纹，登录用户绑定账户。
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import User, DeviceSession, UserCredit, CreditTransaction


# ========== 套餐定义 ==========
PLANS = {
    "free": {
        "name": "免费版",
        "price_cents": 0,
        "monthly_quota": 1,
        "features": ["基础行程规划", "景点搜索", "天气查询"],
    },
    "pro_monthly": {
        "name": "Pro 月付",
        "price_cents": 2990,
        "monthly_quota": 100,
        "features": ["高清导出", "优先队列", "无限历史记录"],
    },
    "pro_yearly": {
        "name": "Pro 年付",
        "price_cents": 29900,
        "monthly_quota": 1500,
        "features": ["8.3折优惠", "高清导出", "优先队列", "无限历史记录"],
    },
    "family": {
        "name": "家庭版",
        "price_cents": 5990,
        "monthly_quota": 500,
        "features": ["最多5人共享", "家庭行程协作", "高清导出"],
    },
}

GUEST_FREE_QUOTA = 1
NEW_USER_TRIAL_QUOTA = 10


class QuotaResult:
    """额度检查结果"""

    def __init__(
        self,
        has_quota: bool,
        remaining: int,
        total: int,
        is_guest: bool = False,
        quota_type: str = "device",
        plan_name: str = "免费版",
        status: str = "normal",
        message: str = "",
    ):
        self.has_quota = has_quota
        self.remaining = remaining
        self.total = total
        self.is_guest = is_guest
        self.quota_type = quota_type
        self.plan_name = plan_name
        self.status = status  # normal | warning | exhausted
        self.message = message

    def to_dict(self) -> dict:
        percent = round((1 - self.remaining / max(self.total, 1)) * 100, 1)
        return {
            "is_guest": self.is_guest,
            "quota_type": self.quota_type,
            "remaining": self.remaining,
            "total": self.total,
            "percent": min(percent, 100.0),
            "status": self.status,
            "plan_name": self.plan_name,
            "message": self.message,
        }


class CreditService:
    """额度管理核心服务"""

    GUEST_FREE_QUOTA = GUEST_FREE_QUOTA
    NEW_USER_TRIAL_QUOTA = NEW_USER_TRIAL_QUOTA

    # ========== 设备管理 ==========

    async def get_or_create_device(
        self,
        db: AsyncSession,
        fingerprint: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> DeviceSession:
        """获取或创建设备会话记录"""
        result = await db.execute(
            select(DeviceSession).where(DeviceSession.fingerprint == fingerprint)
        )
        device = result.scalar_one_or_none()

        if device is None:
            device = DeviceSession(
                fingerprint=fingerprint,
                remaining_quota=self.GUEST_FREE_QUOTA,
                user_agent=user_agent,
                ip_address=ip_address,
            )
            db.add(device)
            await db.flush()
        else:
            # 更新最后活跃信息
            device.ip_address = ip_address or device.ip_address
            device.user_agent = user_agent or device.user_agent
            device.last_used_at = datetime.now(timezone.utc)

        return device

    # ========== 额度检查 ==========

    async def check_quota(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
    ) -> QuotaResult:
        """检查是否有可用额度。

        优先级：登录用户 > 游客设备

        Args:
            db: 数据库会话
            user_id: 登录用户 ID（可选）
            device_fingerprint: 设备指纹（可选）

        Returns:
            QuotaResult 包含额度状态信息
        """
        # ── 登录用户 ──
        if user_id:
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if user is None:
                return QuotaResult(
                    has_quota=False,
                    remaining=0,
                    total=0,
                    is_guest=False,
                    quota_type="account",
                    status="exhausted",
                    message="用户不存在",
                )

            # 检查是否需要重置月度配额
            await self._maybe_reset_monthly_quota(db, user)

            remaining = user.credits_balance
            total = user.monthly_quota

            if total == 0:
                # 未购买套餐的用户（role=free 但已注册）
                # 检查 user_credits 表
                credit_result = await db.execute(
                    select(UserCredit).where(UserCredit.user_id == user_id)
                )
                user_credit = credit_result.scalar_one_or_none()
                if user_credit:
                    total = user_credit.total_purchased
                    remaining = total - user_credit.used_this_month

            if remaining > 0:
                return QuotaResult(
                    has_quota=True,
                    remaining=remaining,
                    total=total,
                    is_guest=False,
                    quota_type="account",
                    plan_name=PLANS.get(user.role, PLANS["free"])["name"],
                    status="normal",
                )
            else:
                # 软限制：登录用户即使额度为0也放行（体验模式）
                return QuotaResult(
                    has_quota=True,  # 放行，体验模式
                    remaining=0,
                    total=max(total, 1),
                    is_guest=False,
                    quota_type="account",
                    plan_name=PLANS.get(user.role, PLANS["free"])["name"],
                    status="exhausted",
                    message="额度已用尽，当前为体验模式。生成的计划无法保存和导出。",
                )

        # ── 游客 ──
        if device_fingerprint:
            result = await db.execute(
                select(DeviceSession).where(
                    DeviceSession.fingerprint == device_fingerprint
                )
            )
            device = result.scalar_one_or_none()

            if device is None:
                # 新设备，有完整免费额度
                return QuotaResult(
                    has_quota=True,
                    remaining=self.GUEST_FREE_QUOTA,
                    total=self.GUEST_FREE_QUOTA,
                    is_guest=True,
                    quota_type="device",
                    plan_name="免费版（游客）",
                    status="normal",
                    message=f"新设备，免费体验 {self.GUEST_FREE_QUOTA} 次",
                )

            if device.remaining_quota > 0:
                return QuotaResult(
                    has_quota=True,
                    remaining=device.remaining_quota,
                    total=self.GUEST_FREE_QUOTA,
                    is_guest=True,
                    quota_type="device",
                    plan_name="免费版（游客）",
                    status="normal" if device.remaining_quota > 1 else "warning",
                )
            else:
                # 游客硬限制：用完即止
                return QuotaResult(
                    has_quota=False,
                    remaining=0,
                    total=self.GUEST_FREE_QUOTA,
                    is_guest=True,
                    quota_type="device",
                    plan_name="免费版（游客）",
                    status="exhausted",
                    message="免费体验次数已用完，请注册登录后继续使用",
                )

        # ── 无任何标识 ──
        return QuotaResult(
            has_quota=False,
            remaining=0,
            total=0,
            is_guest=True,
            status="exhausted",
            message="无法识别设备，请刷新页面后重试",
        )

    # ========== 额度消费 ==========

    async def consume_quota(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """消费 1 次额度。

        登录用户：扣减 user.credits_balance 和 user_credits.used_this_month
        游客：扣减 device_sessions.remaining_quota

        Returns:
            True = 消费成功, False = 额度不足
        """
        # ── 登录用户 ──
        if user_id:
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user is None:
                return False

            # 检查并重置月度配额
            await self._maybe_reset_monthly_quota(db, user)

            # 扣减 credits_balance
            if user.credits_balance > 0:
                user.credits_balance -= 1

            # 更新 user_credits
            credit_result = await db.execute(
                select(UserCredit).where(UserCredit.user_id == user_id)
            )
            user_credit = credit_result.scalar_one_or_none()
            if user_credit:
                user_credit.used_this_month += 1

            # 记录流水
            tx = CreditTransaction(
                user_id=user_id,
                type="consume",
                amount=-1,
                balance_after=user.credits_balance,
                description="生成旅行计划",
                session_id=session_id,
            )
            db.add(tx)
            await db.flush()
            return True

        # ── 游客 ──
        if device_fingerprint:
            result = await db.execute(
                select(DeviceSession).where(
                    DeviceSession.fingerprint == device_fingerprint
                )
            )
            device = result.scalar_one_or_none()

            if device is None:
                # 首次使用，创建设备并扣减
                device = DeviceSession(
                    fingerprint=device_fingerprint,
                    remaining_quota=self.GUEST_FREE_QUOTA - 1,
                    total_used=1,
                )
                db.add(device)
                await db.flush()
                return True

            if device.remaining_quota <= 0:
                return False

            device.remaining_quota -= 1
            device.total_used += 1
            device.last_used_at = datetime.now(timezone.utc)
            await db.flush()
            return True

        return False

    # ========== 额度状态查询 ==========

    async def get_quota_status(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
    ) -> dict:
        """返回当前额度状态，供前端进度条展示"""
        result = await self.check_quota(db, user_id, device_fingerprint)
        return result.to_dict()

    # ========== 套餐管理 ==========

    async def get_plans(self) -> list[dict]:
        """获取所有套餐列表"""
        return [
            {
                "id": plan_id,
                "name": plan["name"],
                "price_cents": plan["price_cents"],
                "price_display": f"¥{plan['price_cents'] / 100:.2f}"
                if plan["price_cents"] > 0
                else "免费",
                "monthly_quota": plan["monthly_quota"],
                "features": plan["features"],
            }
            for plan_id, plan in PLANS.items()
        ]

    async def purchase_plan(
        self,
        db: AsyncSession,
        user_id: str,
        plan_id: str,
    ) -> dict:
        """为用户购买套餐（手动充值/支付回调调用）

        Args:
            user_id: 用户 ID
            plan_id: 套餐标识 (free | pro_monthly | pro_yearly | family)

        Returns:
            购买结果信息
        """
        plan = PLANS.get(plan_id)
        if not plan:
            raise ValueError(f"未知套餐: {plan_id}")

        # 更新用户角色
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            raise ValueError("用户不存在")

        user.role = "pro" if "pro" in plan_id else plan_id
        user.monthly_quota = plan["monthly_quota"]
        user.credits_balance = plan["monthly_quota"]
        user.quota_reset_at = datetime.now(timezone.utc)

        # 更新或创建 user_credits
        credit_result = await db.execute(
            select(UserCredit).where(UserCredit.user_id == user_id)
        )
        user_credit = credit_result.scalar_one_or_none()

        if user_credit is None:
            user_credit = UserCredit(
                user_id=user_id,
                total_purchased=plan["monthly_quota"],
                used_this_month=0,
            )
            db.add(user_credit)
        else:
            user_credit.total_purchased += plan["monthly_quota"]
            user_credit.used_this_month = 0

        # 记录流水
        tx = CreditTransaction(
            user_id=user_id,
            type="earn",
            amount=plan["monthly_quota"],
            balance_after=user.credits_balance,
            description=f"购买套餐: {plan['name']}",
        )
        db.add(tx)
        await db.flush()

        return {
            "plan_id": plan_id,
            "plan_name": plan["name"],
            "credits_added": plan["monthly_quota"],
            "new_balance": user.credits_balance,
        }

    # ========== 新用户试用额度 ==========

    async def grant_trial_credits(self, db: AsyncSession, user_id: str):
        """新用户注册时赠送试用额度"""
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            return

        user.credits_balance = self.NEW_USER_TRIAL_QUOTA
        user.monthly_quota = self.NEW_USER_TRIAL_QUOTA
        user.quota_reset_at = None  # 试用额度不过期

        # 创建 user_credits
        user_credit = UserCredit(
            user_id=user_id,
            total_purchased=self.NEW_USER_TRIAL_QUOTA,
            used_this_month=0,
        )
        db.add(user_credit)

        # 记录流水
        tx = CreditTransaction(
            user_id=user_id,
            type="earn",
            amount=self.NEW_USER_TRIAL_QUOTA,
            balance_after=self.NEW_USER_TRIAL_QUOTA,
            description="新用户注册赠送试用额度",
        )
        db.add(tx)
        await db.flush()

    # ========== 内部辅助方法 ==========

    async def _maybe_reset_monthly_quota(self, db: AsyncSession, user: User):
        """检查是否需要重置月度配额"""
        if user.quota_reset_at is None:
            return

        now = datetime.now(timezone.utc)
        if now >= user.quota_reset_at:
            # 重置月度额度
            user.credits_balance = user.monthly_quota
            # 下一个重置时间：下个月同一天
            if user.quota_reset_at.month == 12:
                user.quota_reset_at = user.quota_reset_at.replace(
                    year=user.quota_reset_at.year + 1, month=1
                )
            else:
                user.quota_reset_at = user.quota_reset_at.replace(
                    month=user.quota_reset_at.month + 1
                )

            # 重置 user_credits 月度计数
            credit_result = await db.execute(
                select(UserCredit).where(UserCredit.user_id == user.id)
            )
            user_credit = credit_result.scalar_one_or_none()
            if user_credit:
                user_credit.used_this_month = 0

            await db.flush()


# 全局服务实例
credit_service = CreditService()
