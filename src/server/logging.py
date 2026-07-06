"""TripAgent 结构化日志系统

基于 structlog 实现 JSON 格式结构化日志，支持全链路追踪。
如果 structlog 未安装，降级使用标准 logging。
"""

import logging
import sys
import time
from typing import Optional

# ========== 尝试导入 structlog ==========
try:
    import structlog

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


# ========== 日志级别 ==========
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def setup_logging(log_level: str = "INFO", use_json: bool = True):
    """初始化结构化日志

    Args:
        log_level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        use_json: 生产环境使用 JSON 格式，开发环境可使用彩色输出
    """
    level = LOG_LEVELS.get(log_level.upper(), logging.INFO)

    if STRUCTLOG_AVAILABLE and use_json:
        # ===== structlog JSON 模式 =====
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # ===== 标准 logging 降级 =====
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
            stream=sys.stdout,
        )


def get_logger(name: str = "tripagent"):
    """获取日志器

    Usage:
        logger = get_logger(__name__)
        logger.info("tool_called", tool="search_attractions", latency_ms=120)
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


# ========== 预定义日志字段 ==========
class LogContext:
    """日志上下文字段定义 — 确保全链路统一"""

    # 请求级
    REQUEST_ID = "request_id"
    USER_ID = "user_id"
    SESSION_ID = "session_id"

    # 工具级
    TOOL_NAME = "tool_name"
    TOOL_ARGS = "tool_args"
    TOOL_RESULT_LEN = "tool_result_len"
    LATENCY_MS = "latency_ms"
    TOKEN_COUNT = "token_count"

    # LLM 级
    MODEL_NAME = "model_name"
    PROMPT_LEN = "prompt_len"

    # 错误级
    ERROR_TYPE = "error_type"
    ERROR_MSG = "error_msg"
    HTTP_STATUS = "http_status"


# ========== 全局初始化 ==========
setup_logging(log_level="INFO")
logger = get_logger("tripagent")


# ========== 中间件辅助 ==========
class RequestLogger:
    """请求日志中间件（用于 FastAPI 中间件）"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        request_id = "-"

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                latency = (time.time() - start_time) * 1000
                logger.info(
                    "request_completed",
                    request_id=request_id,
                    method=scope.get("method", ""),
                    path=scope.get("path", ""),
                    status=message.get("status", 0),
                    latency_ms=round(latency, 1),
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)
