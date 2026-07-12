"""额度查询路由 — 供前端进度条和套餐展示"""

from typing import Optional

from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_optional_user
from ..services.credit_service import credit_service

router = APIRouter()


@router.get("/credits/status")
async def get_credit_status(
    req: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_user),
    x_device_fingerprint: Optional[str] = Header(None, alias="X-Device-Fingerprint"),
):
    """获取当前用户的额度状态，供进度条展示。

    游客返回 device 额度，登录用户返回 account 额度。

    响应格式：
    {
        "is_guest": true,
        "quota_type": "device",
        "remaining": 0,
        "total": 1,
        "percent": 100.0,
        "status": "exhausted",
        "plan_name": "免费版（游客）",
        "message": "免费体验次数已用完，请注册登录后继续使用"
    }
    """
    user_id = current_user.get("sub") if current_user else None
    return await credit_service.get_quota_status(
        db, user_id=user_id, device_fingerprint=x_device_fingerprint
    )
