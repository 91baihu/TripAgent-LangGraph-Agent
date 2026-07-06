# TripAgent Dockerfile — Multi-stage build
# Stage 1: 构建依赖
FROM python:3.12-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装构建依赖
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: 运行环境
FROM python:3.12-slim AS runtime

WORKDIR /app

# 创建非 root 用户
RUN groupadd -r tripagent && useradd -r -g tripagent tripagent

# 从 builder 复制已安装的包
COPY --from=builder /root/.local /home/tripagent/.local
ENV PATH=/home/tripagent/.local/bin:$PATH

# 复制源码
COPY src/ ./src/
COPY tests/ ./tests/

# 切换到非 root 用户
RUN chown -R tripagent:tripagent /app
USER tripagent

# 默认暴露 FastAPI 端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 默认启动 FastAPI（如无 uvicorn 则降级为 Streamlit）
CMD ["python", "-m", "uvicorn", "src.server.main:app", "--host", "0.0.0.0", "--port", "8000"]
