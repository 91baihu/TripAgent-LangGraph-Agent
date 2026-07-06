-- TripAgent 数据库初始化脚本
-- 创建扩展和基础表结构

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ========== 用户表 ==========
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nickname VARCHAR(100),
    avatar_url TEXT,
    password_hash VARCHAR(255),           -- 邮箱密码登录
    oauth_provider VARCHAR(50),           -- google | wechat | github
    oauth_id VARCHAR(255),                -- OAuth 第三方 ID
    role VARCHAR(20) DEFAULT 'free',      -- free | pro | family | admin
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========== 行程表 ==========
CREATE TABLE IF NOT EXISTS trips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    days INT NOT NULL DEFAULT 3,
    itinerary_json JSONB NOT NULL DEFAULT '{}',  -- 完整行程 JSON
    status VARCHAR(20) DEFAULT 'draft',           -- draft | confirmed | completed | archived
    share_token VARCHAR(64) UNIQUE,               -- 分享链接 token
    share_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trips_user_id ON trips(user_id);
CREATE INDEX idx_trips_share_token ON trips(share_token);
CREATE INDEX idx_trips_city ON trips(city);

-- ========== 工具调用审计表 ==========
CREATE TABLE IF NOT EXISTS tool_call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(64) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    input_json JSONB NOT NULL DEFAULT '{}',
    output_json JSONB,
    latency_ms INT,
    token_count INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tool_logs_session ON tool_call_logs(session_id);
CREATE INDEX idx_tool_logs_tool_name ON tool_call_logs(tool_name);
CREATE INDEX idx_tool_logs_created ON tool_call_logs(created_at);

-- ========== API Key 表（B2B 客户） ==========
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(8) NOT NULL,        -- 用于 UI 展示: "ta_ab12..."
    name VARCHAR(100),
    call_limit_per_day INT DEFAULT 500,
    call_count_today INT DEFAULT 0,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

-- ========== 用户偏好表 ==========
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    budget_level VARCHAR(20) DEFAULT 'mid',      -- budget | mid | luxury
    travel_style JSONB DEFAULT '[]',              -- ["亲子","文化","户外","美食"]
    favorite_cities JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ========== 更新触发器 ==========
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_trips_updated
    BEFORE UPDATE ON trips
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_user_prefs_updated
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
