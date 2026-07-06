"""TripAgent 认证授权模块

提供：
- JWT Token 生成 & 验证
- 密码哈希 (bcrypt)
- API Key 验证
- FastAPI 依赖注入（get_current_user）
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

# bcrypt 直接调用（避免 passlib 版本兼容问题）
try:
    import bcrypt as _bcrypt

    def hash_password(password: str) -> str:
        return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return _bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
except ImportError:
    # 降级：使用 passlib（如果 bcrypt 不可用）
    from passlib.context import CryptContext
    _pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash_password = lambda p: _pwd_ctx.hash(p)  # noqa: E731
    verify_password = lambda p, h: _pwd_ctx.verify(p, h)  # noqa: E731


# ========== 配置 ==========
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_secret_key_change_in_production_12345678")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ========== HTTP Bearer ==========
bearer_scheme = HTTPBearer(auto_error=False)

# ========== JWT 工具 ==========
def create_access_token(user_id: str, role: str = "free") -> str:
    """生成访问令牌 (Access Token)

    Args:
        user_id: 用户 ID
        role: 用户角色 (free/pro/admin)

    Returns:
        JWT token string
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """生成刷新令牌 (Refresh Token)"""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """验证 JWT 令牌并返回 payload

    Raises:
        HTTPException: 令牌无效或过期时抛出
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无效的认证令牌: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ========== FastAPI 依赖注入 ==========
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """从 Bearer Token 中提取当前用户信息

    Usage:
        @router.get("/me")
        async def get_me(user: dict = Depends(get_current_user)):
            return {"user_id": user["sub"], "role": user["role"]}
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录才能访问此接口",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    return payload


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict]:
    """可选认证 — 不强制要求登录"""
    if credentials is None:
        return None
    try:
        return verify_token(credentials.credentials)
    except HTTPException:
        return None


def require_role(*allowed_roles: str):
    """角色权限检查工厂

    Usage:
        @router.get("/admin")
        async def admin_panel(user: dict = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要角色: {', '.join(allowed_roles)}",
            )
        return user

    return role_checker


# ========== API Key 工具 ==========
def generate_api_key() -> tuple[str, str, str]:
    """生成 API Key

    Returns:
        (prefix, raw_key, hashed_key)
        - prefix: 存储前缀，用于 UI 展示 "ta_abc123..."
        - raw_key: 完整 Key，仅生成时返回给用户
        - hashed_key: 哈希值，存入数据库
    """
    raw = "ta_" + secrets.token_urlsafe(24)
    prefix = raw[:10]
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return prefix, raw, hashed


def hash_api_key(raw_key: str) -> str:
    """对 API Key 进行哈希"""
    return hashlib.sha256(raw_key.encode()).hexdigest()
