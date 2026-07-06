"""认证路由 — 注册/登录/刷新令牌"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    bearer_scheme,
)

router = APIRouter(prefix="/auth", tags=["认证"])


# ========== 请求模型 ==========
class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=72)
    nickname: str = Field(default="", max_length=50)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒


class RefreshRequest(BaseModel):
    refresh_token: str


# ========== 临时用户存储（后续替换为 PostgreSQL） ==========
_users_db: dict = {}  # email -> {id, email, password_hash, nickname, role, ...}


# ========== 路由 ==========
@router.post("/register", status_code=201)
async def register(req: RegisterRequest):
    """用户注册"""
    import uuid

    if req.email in _users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已被注册",
        )

    user_id = str(uuid.uuid4())
    _users_db[req.email] = {
        "id": user_id,
        "email": req.email,
        "password_hash": hash_password(req.password),
        "nickname": req.nickname or req.email.split("@")[0],
        "role": "free",
    }

    access_token = create_access_token(user_id, "free")
    refresh_token = create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60,  # 15 分钟
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """用户登录"""
    user = _users_db.get(req.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    access_token = create_access_token(user["id"], user["role"])
    refresh_token = create_refresh_token(user["id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    """刷新访问令牌"""
    payload = verify_token(req.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌类型错误，需要 refresh token",
        )

    user_id = payload["sub"]
    # 查找用户角色
    role = "free"
    for user in _users_db.values():
        if user["id"] == user_id:
            role = user["role"]
            break

    new_access = create_access_token(user_id, role)
    new_refresh = create_refresh_token(user_id)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=15 * 60,
    )


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    user_id = user["sub"]
    for u in _users_db.values():
        if u["id"] == user_id:
            return {
                "id": u["id"],
                "email": u["email"],
                "nickname": u["nickname"],
                "role": u["role"],
            }
    raise HTTPException(status_code=404, detail="用户不存在")
