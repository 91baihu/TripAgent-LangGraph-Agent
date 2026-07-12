"""付费与订单路由 — 套餐/订单/支付"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_user, require_role
from ..services.billing_service import billing_service

router = APIRouter()


class CreateOrderRequest(BaseModel):
    plan_id: str = Field(..., pattern="^(pro_monthly|pro_yearly|family)$")
    payment_method: str = Field(default="manual", pattern="^(manual|alipay|wechat)$")


class GrantCreditsRequest(BaseModel):
    user_id: str
    amount: int = Field(..., gt=0, le=100000)
    description: str = Field(default="管理员赠送", max_length=200)


# ========== 套餐列表（公开） ==========
@router.get("/plans")
async def get_plans():
    """获取所有可用套餐（公开接口）"""
    return await billing_service.get_plans()


# ========== 用户订单 ==========
@router.post("/orders")
async def create_order(
    body: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """创建购买订单"""
    try:
        order = await billing_service.create_order(
            db,
            user_id=current_user["sub"],
            plan_id=body.plan_id,
            payment_method=body.payment_method,
        )
        await db.commit()
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders")
async def get_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取我的订单列表"""
    return await billing_service.get_user_orders(
        db, user_id=current_user["sub"], page=page, page_size=page_size
    )


@router.get("/orders/{order_id}")
async def get_order_detail(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取订单详情"""
    order = await billing_service.get_order_detail(
        db, order_id, user_id=current_user["sub"]
    )
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """取消订单"""
    ok = await billing_service.cancel_order(db, order_id, user_id=current_user["sub"])
    if not ok:
        raise HTTPException(status_code=400, detail="订单不存在或状态不允许取消")
    await db.commit()
    return {"status": "cancelled"}


# ========== 模拟支付（开发/测试） ==========
@router.post("/orders/{order_id}/pay")
async def simulate_payment(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """模拟支付 — 开发环境使用"""
    try:
        result = await billing_service.simulate_payment(
            db, order_id, user_id=current_user["sub"]
        )
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== 管理员接口 ==========
@router.get("/admin/orders")
async def get_all_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(pending|paid|cancelled|refunded)$"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """管理员查看所有订单"""
    return await billing_service.get_all_orders(
        db, page=page, page_size=page_size, status_filter=status
    )


@router.post("/admin/orders/{order_id}/confirm")
async def confirm_payment(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """管理员确认收款"""
    try:
        result = await billing_service.confirm_payment(db, order_id)
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/credits/grant")
async def grant_credits(
    body: GrantCreditsRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """管理员手动赠送额度"""
    try:
        result = await billing_service.grant_credits(
            db,
            user_id=body.user_id,
            amount=body.amount,
            description=body.description,
        )
        await db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
