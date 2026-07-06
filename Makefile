# TripAgent Makefile — 常用命令快捷方式
.PHONY: help up down logs build test clean

# 默认显示帮助
help:
	@echo "TripAgent 开发命令"
	@echo "==================="
	@echo ""
	@echo "  make up         启动全部服务 (api + db + redis)"
	@echo "  make up-dev     启动开发环境 (含 Streamlit 管理面板)"
	@echo "  make down       停止全部服务"
	@echo "  make down-clean 停止服务并清除数据卷"
	@echo "  make logs       查看所有服务日志"
	@echo "  make logs-api   仅查看 API 服务日志"
	@echo "  make build      重新构建镜像"
	@echo "  make test       运行单元测试"
	@echo "  make test-all   运行全部测试 (需要 API Key)"
	@echo "  make shell      进入 API 容器 shell"
	@echo "  make db-reset   重置数据库"
	@echo "  make clean      清除所有 Docker 资源"

# ========== 启动 / 停止 ==========

up:
	@echo "🚀 启动核心服务 (api + db + redis)..."
	docker-compose --env-file config/dev.env up -d postgres redis api
	@echo "✅ 服务已启动: http://localhost:8000"

up-dev:
	@echo "🚀 启动开发环境 (含 Streamlit 管理面板)..."
	docker-compose --env-file config/dev.env --profile dev up -d
	@echo "✅ API:      http://localhost:8000"
	@echo "✅ Admin:    http://localhost:8501"

up-prod:
	@echo "🚀 启动生产环境..."
	docker-compose --env-file config/prod.env --profile prod up -d
	@echo "✅ 服务已启动: http://localhost:80"

down:
	docker-compose --env-file config/dev.env down

down-clean:
	docker-compose --env-file config/dev.env down -v

# ========== 日志 ==========

logs:
	docker-compose --env-file config/dev.env logs -f --tail=50

logs-api:
	docker-compose --env-file config/dev.env logs -f api

# ========== 构建 ==========

build:
	docker-compose --env-file config/dev.env build --no-cache

# ========== 测试 ==========

test:
	docker-compose --env-file config/dev.env run --rm api pytest tests/ -v -k "not AgentIntegration"

test-all:
	docker-compose --env-file config/dev.env run --rm api pytest tests/ -v

# ========== 调试 ==========

shell:
	docker-compose --env-file config/dev.env exec api /bin/bash

db-reset:
	docker-compose --env-file config/dev.env down postgres -v
	docker-compose --env-file config/dev.env up -d postgres
	@echo "⏳ 等待数据库就绪..."
	@sleep 3
	@echo "✅ 数据库已重置"

# ========== 清理 ==========

clean:
	docker-compose --env-file config/dev.env down -v --rmi all
	@echo "✅ 已清除所有 Docker 资源"
