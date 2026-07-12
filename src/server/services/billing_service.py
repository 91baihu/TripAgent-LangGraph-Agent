"""付费与订单服务 — 套餐购买、订单管理、支付确认

第一版采用手动充值流程（管理员后台确认），后续可接入支付宝/微信支付。
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from ..models import User, UserCredit, PurchaseOrder, CreditTransaction
from .credit_service import PLANS, credit_service


class BillingService:
    """付费与订单管理服务"""

    # ========== 套餐查询 ==========

    async def get_plans(self) -> list[dict]:
        """获取所有可用套餐"""
        return [
            {
                "id": plan_id,
                "name": plan["name"],
                "price_cents": plan["price_cents"],
                "price_display": (
                    f"¥{plan['price_cents'] / 100:.2f}"
                    if plan["price_cents"] > 0
                    else "免费"
                ),
                "monthly_price": (
                    f"¥{plan['price_cents'] / 100:.2f}/月"
                    if "monthly" in plan_id
                    else (
                        f"¥{plan['price_cents'] / 100 / 12:.2f}/月"
                        if "yearly" in plan_id
                        else "免费"
                    )
                ),
                "monthly_quota": plan["monthly_quota"],
                "features": plan["features"],
                "popular": plan_id == "pro_yearly",  # 推荐标记
            }
            for plan_id, plan in PLANS.items()
        ]

    # ========== 订单创建 ==========

    async def create_order(
        self,
        db: AsyncSession,
        user_id: str,
        plan_id: str,
        payment_method: str = "manual",
    ) -> dict:
        """创建购买订单

        Args:
            user_id: 用户 ID
            plan_id: 套餐标识
            payment_method: 支付方式 (manual/alipay/wechat)

        Returns:
            {"order_id": "...", "plan_name": "...", "amount_cents": ..., "status": "pending"}
        """
        plan = PLANS.get(plan_id)
        if not plan:
            raise ValueError(f"未知套餐: {plan_id}")

        if plan["price_cents"] == 0:
            raise ValueError("免费套餐无需购买")

        # 检查是否已有未支付订单
        existing = await db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.user_id == user_id,
                PurchaseOrder.plan_id == plan_id,
                PurchaseOrder.status == "pending",
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("您有一个待支付的相同套餐订单，请先完成或取消")

        order = PurchaseOrder(
            id=str(uuid.uuid4()),
            user_id=user_id,
            plan_id=plan_id,
            amount_cents=plan["price_cents"],
            credits_purchased=plan["monthly_quota"],
            status="pending",
            payment_method=payment_method,
        )
        db.add(order)
        await db.flush()

        return {
            "order_id": order.id,
            "plan_id": plan_id,
            "plan_name": plan["name"],
            "amount_cents": plan["price_cents"],
            "amount_display": f"¥{plan['price_cents'] / 100:.2f}",
            "credits_purchased": plan["monthly_quota"],
            "status": "pending",
        }

    # ========== 订单查询 ==========

    async def get_user_orders(
        self,
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取用户的订单列表"""
        count_result = await db.execute(
            select(func.count()).where(PurchaseOrder.user_id == user_id)
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.user_id == user_id)
            .order_by(desc(PurchaseOrder.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        orders = result.scalars().all()

        return {
            "orders": [
                {
                    "id": o.id,
                    "plan_id": o.plan_id,
                    "plan_name": PLANS.get(o.plan_id, {}).get("name", o.plan_id),
                    "amount_cents": o.amount_cents,
                    "amount_display": f"¥{o.amount_cents / 100:.2f}",
                    "credits_purchased": o.credits_purchased,
                    "status": o.status,
                    "payment_method": o.payment_method,
                    "payment_ref": o.payment_ref,
                    "paid_at": o.paid_at.isoformat() if o.paid_at else None,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in orders
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_order_detail(
        self,
        db: AsyncSession,
        order_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[dict]:
        """获取订单详情"""
        query = select(PurchaseOrder).where(PurchaseOrder.id == order_id)
        if user_id:
            query = query.where(PurchaseOrder.user_id == user_id)

        result = await db.execute(query)
        order = result.scalar_one_or_none()
        if not order:
            return None

        return {
            "id": order.id,
            "plan_id": order.plan_id,
            "plan_name": PLANS.get(order.plan_id, {}).get("name", order.plan_id),
            "amount_cents": order.amount_cents,
            "amount_display": f"¥{order.amount_cents / 100:.2f}",
            "credits_purchased": order.credits_purchased,
            "status": order.status,
            "payment_method": order.payment_method,
            "payment_ref": order.payment_ref,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }

    # ========== 取消订单 ==========

    async def cancel_order(
        self,
        db: AsyncSession,
        order_id: str,
        user_id: str,
    ) -> bool:
        """取消订单（仅 pending 状态）"""
        result = await db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.id == order_id,
                PurchaseOrder.user_id == user_id,
            )
        )
        order = result.scalar_one_or_none()
        if not order or order.status != "pending":
            return False

        order.status = "cancelled"
        await db.flush()
        return True

    # ========== 支付确认（管理员/模拟支付） ==========

    async def confirm_payment(
        self,
        db: AsyncSession,
        order_id: str,
        payment_ref: str = "",
    ) -> dict:
        """确认支付 — 管理员后台确认或支付回调

        执行流程：
        1. 更新订单状态为 paid
        2. 为用户充值额度
        3. 记录额度流水
        """
        result = await db.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("订单不存在")
        if order.status != "pending":
            raise ValueError(f"订单状态为 {order.status}，无法确认支付")

        # 更新订单
        order.status = "paid"
        order.payment_ref = payment_ref or f"manual_{order_id[:8]}"
        order.paid_at = datetime.now(timezone.utc)

        # 充值额度
        await credit_service.purchase_plan(db, order.user_id, order.plan_id)

        await db.flush()

        return {
            "order_id": order.id,
            "status": "paid",
            "plan_name": PLANS.get(order.plan_id, {}).get("name", ""),
            "credits_added": order.credits_purchased,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        }

    # ========== 模拟支付（开发/测试用） ==========

    async def simulate_payment(
        self,
        db: AsyncSession,
        order_id: str,
        user_id: str,
    ) -> dict:
        """模拟支付 — 仅开发环境使用

        自动将订单标记为 paid 并充值额度。
        """
        result = await db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.id == order_id,
                PurchaseOrder.user_id == user_id,
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("订单不存在")

        return await self.confirm_payment(
            db, order_id, payment_ref=f"simulated_{order_id[:8]}"
        )

    # ========== 管理员：所有订单 ==========

    async def get_all_orders(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        status_filter: Optional[str] = None,
    ) -> dict:
        """管理员查看所有订单"""
        query = select(PurchaseOrder)
        count_query = select(func.count()).select_from(PurchaseOrder)

        if status_filter:
            query = query.where(PurchaseOrder.status == status_filter)
            count_query = count_query.where(PurchaseOrder.status == status_filter)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        result = await db.execute(
            query
            .order_by(desc(PurchaseOrder.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        orders = result.scalars().all()

        return {
            "orders": [
                {
                    "id": o.id,
                    "user_id": o.user_id,
                    "plan_id": o.plan_id,
                    "plan_name": PLANS.get(o.plan_id, {}).get("name", o.plan_id),
                    "amount_cents": o.amount_cents,
                    "amount_display": f"¥{o.amount_cents / 100:.2f}",
                    "credits_purchased": o.credits_purchased,
                    "status": o.status,
                    "payment_method": o.payment_method,
                    "payment_ref": o.payment_ref,
                    "paid_at": o.paid_at.isoformat() if o.paid_at else None,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in orders
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    # ========== 管理员：手动赠送额度 ==========

    async def grant_credits(
        self,
        db: AsyncSession,
        user_id: str,
        amount: int,
        description: str = "管理员赠送",
    ) -> dict:
        """管理员手动赠送额度"""
        if amount <= 0:
            raise ValueError("赠送额度必须大于 0")

        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError("用户不存在")

        user.credits_balance += amount
        user.monthly_quota += amount

        # 更新或创建 user_credits
        credit_result = await db.execute(
            select(UserCredit).where(UserCredit.user_id == user_id)
        )
        user_credit = credit_result.scalar_one_or_none()
        if user_credit:
            user_credit.total_purchased += amount
        else:
            user_credit = UserCredit(
                user_id=user_id,
                total_purchased=amount,
                used_this_month=0,
            )
            db.add(user_credit)

        # 记录流水
        tx = CreditTransaction(
            user_id=user_id,
            type="gift",
            amount=amount,
            balance_after=user.credits_balance,
            description=description,
        )
        db.add(tx)
        await db.flush()

        return {
            "user_id": user_id,
            "credits_added": amount,
            "new_balance": user.credits_balance,
            "description": description,
        }


# 全局服务实例
billing_service = BillingService()
