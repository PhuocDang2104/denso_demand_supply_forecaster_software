-- ============================================
-- Patch schema cũ lên phiên bản V3
-- Thêm những cột đang thiếu để seed_data.sql chạy được
-- ============================================

-- 1) Alerts log: thêm cột message (main.js dùng field msg, mình có thể map trong API)
ALTER TABLE mart.alerts_log
    ADD COLUMN IF NOT EXISTS message TEXT;

-- 2) Model backtest: thêm các cột cho leaderboard
ALTER TABLE mart.model_backtest
    ADD COLUMN IF NOT EXISTS horizon_days INTEGER,
    ADD COLUMN IF NOT EXISTS pinball_p90  NUMERIC,
    ADD COLUMN IF NOT EXISTS coverage     NUMERIC,
    ADD COLUMN IF NOT EXISTS latency      NUMERIC,
    ADD COLUMN IF NOT EXISTS run_id       TEXT,
    ADD COLUMN IF NOT EXISTS trained_at   TIMESTAMPTZ;

-- 3) Model registry: thêm params & is_champion nếu chưa có
ALTER TABLE mart.model_registry
    ADD COLUMN IF NOT EXISTS dataset      TEXT,
    ADD COLUMN IF NOT EXISTS params       JSONB,
    ADD COLUMN IF NOT EXISTS is_champion  BOOLEAN DEFAULT FALSE;

-- 4) Model metrics over time: thiếu model_name
ALTER TABLE mart.model_metrics_over_time
    ADD COLUMN IF NOT EXISTS model_name TEXT;

-- 5) Data drift features: thêm feature_type, source, calc_at
ALTER TABLE mart.data_drift_features
    ADD COLUMN IF NOT EXISTS feature_type TEXT,
    ADD COLUMN IF NOT EXISTS source       TEXT,
    ADD COLUMN IF NOT EXISTS calc_at      TIMESTAMPTZ;

-- 6) Rolling metrics: thêm week (string như '2025-W40')
ALTER TABLE mart.model_metrics_rolling
    ADD COLUMN IF NOT EXISTS week TEXT,
    ADD COLUMN IF NOT EXISTS model_name TEXT,
    ADD COLUMN IF NOT EXISTS sku_group  TEXT;

-- 7) Market weather: thêm as_of_date
ALTER TABLE mart.market_weather_region
    ADD COLUMN IF NOT EXISTS as_of_date DATE;

-- 8) Port congestion: thêm name + as_of_date
ALTER TABLE mart.port_congestion
    ADD COLUMN IF NOT EXISTS name      TEXT,
    ADD COLUMN IF NOT EXISTS as_of_date DATE;

-- 9) Warehouse status: thêm as_of_date
ALTER TABLE mart.warehouse_status
    ADD COLUMN IF NOT EXISTS as_of_date DATE;
