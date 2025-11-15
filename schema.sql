-- ============================================
-- DENSO FORECAST SUITE V3 - DATABASE SCHEMA
-- Database: denso_forecast
-- ============================================

-- 0. SCHEMAS
CREATE SCHEMA IF NOT EXISTS dim;
CREATE SCHEMA IF NOT EXISTS fact;
CREATE SCHEMA IF NOT EXISTS feature;
CREATE SCHEMA IF NOT EXISTS mart;

-- ============================================
-- 1. DIMENSIONS
-- ============================================

-- 1.1 Product Dimension (Spark Plug + Inverter)
CREATE TABLE IF NOT EXISTS dim.dim_product (
    product_key SERIAL PRIMARY KEY,
    sku         VARCHAR(64) UNIQUE NOT NULL,
    name        TEXT,
    family      TEXT,        -- 'Spark Plug' / 'Inverter'
    category    TEXT,        -- 'Ignition', 'Inverter', ...
    type        TEXT,        -- 'Iridium', 'Copper Core', ...
    channel     TEXT         -- 'OEM' / 'Aftermarket' / 'Both'
);

-- 1.2 Market Dimension
CREATE TABLE IF NOT EXISTS dim.dim_market (
    market_key SERIAL PRIMARY KEY,
    country    TEXT NOT NULL,
    region     TEXT,          -- 'Southeast Asia'
    channel    TEXT           -- 'Dealer' / 'E-commerce' / 'OEM'
);

-- ============================================
-- 2. FACTS & FEATURES
-- ============================================

-- 2.1 Weekly Sales Fact (used by dashboard + forecast)
CREATE TABLE IF NOT EXISTS fact.fact_sales_weekly (
    sales_key    SERIAL PRIMARY KEY,
    product_key  INTEGER NOT NULL REFERENCES dim.dim_product(product_key),
    market_key   INTEGER NOT NULL REFERENCES dim.dim_market(market_key),
    week_start   DATE NOT NULL,      -- Monday of week
    units_sold   NUMERIC,
    revenue_usd  NUMERIC,
    CONSTRAINT uq_sales UNIQUE (product_key, market_key, week_start)
);

-- 2.2 Weekly Exogenous Features (Prophet & XGBoost)
CREATE TABLE IF NOT EXISTS feature.ts_features_weekly (
    feature_key                  SERIAL PRIMARY KEY,
    week_start                   DATE NOT NULL,      -- ds
    pmi                          NUMERIC,
    gdp_growth                   NUMERIC,
    cpi                          NUMERIC,
    gas_price                    NUMERIC,
    gtrends_score                NUMERIC,
    new_ice_and_hybrid_sales     NUMERIC,
    bev_penetration_rate         NUMERIC,
    weather_event_flag           BOOLEAN,
    holiday_flag                 BOOLEAN,
    total_ice_and_hybrid_on_road NUMERIC,
    own_price_aftermarket        NUMERIC,
    comp_price_aftermarket       NUMERIC,
    promo_depth                  NUMERIC,
    total_new_vehicle_sales      NUMERIC
);

-- ============================================
-- 3. MART: DASHBOARD (A tab)
-- ============================================

-- 3.1 KPI Summary for Dashboard Overview (/api/dashboard)
CREATE TABLE IF NOT EXISTS mart.kpi_summary (
    kpi_date        DATE PRIMARY KEY,
    revenue_p50     NUMERIC,
    revenue_p10     NUMERIC,
    revenue_p90     NUMERIC,
    mape_last_week  NUMERIC,
    coverage_28d    NUMERIC,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- 3.2 Demand Forecast Weekly (P10 / P50 / P90) - used by fan chart
CREATE TABLE IF NOT EXISTS mart.demand_forecast_weekly (
    forecast_key SERIAL PRIMARY KEY,
    product_key  INTEGER NOT NULL REFERENCES dim.dim_product(product_key),
    market_key   INTEGER NOT NULL REFERENCES dim.dim_market(market_key),
    week_start   DATE NOT NULL,
    horizon_days INTEGER NOT NULL,       -- 7 / 14 / 28 ...
    model_name   TEXT NOT NULL,          -- 'prophet' / 'xgboost' / ...
    p10          NUMERIC,
    p50          NUMERIC,
    p90          NUMERIC,
    actual       NUMERIC,                -- real sales (if known)
    created_at   TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_forecast UNIQUE (product_key, market_key, week_start, horizon_days, model_name)
);

-- 3.3 Alerts Log (Dashboard Overview + Alert Center)
CREATE TABLE IF NOT EXISTS mart.alerts_log (
    alert_id   SERIAL PRIMARY KEY,
    level      TEXT NOT NULL,      -- 'high' / 'med' / 'low'
    type       TEXT NOT NULL,      -- 'demand_spike' / 'stockout_risk' / ...
    message    TEXT NOT NULL,
    link       TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3.4 Error by Horizon (MAPE vs Horizon)
CREATE TABLE IF NOT EXISTS mart.error_horizon (
    id           SERIAL PRIMARY KEY,
    horizon_days INTEGER NOT NULL,
    mape         NUMERIC,
    created_at   TIMESTAMPTZ DEFAULT now()
);

-- 3.5 Coverage by SKU (for Monitoring & Coverage tab)
CREATE TABLE IF NOT EXISTS mart.coverage_by_sku (
    coverage_id  SERIAL PRIMARY KEY,
    product_key  INTEGER NOT NULL REFERENCES dim.dim_product(product_key),
    channel      TEXT NOT NULL,
    period       TEXT NOT NULL,         -- '2025-W40'
    coverage_pct NUMERIC
);

-- ============================================
-- 4. MART: FORECAST EXPLAINABILITY & BACKTEST (B tab)
-- ============================================

-- 4.1 Prophet Components per SKU
CREATE TABLE IF NOT EXISTS mart.prophet_components (
    component_id SERIAL PRIMARY KEY,
    product_key  INTEGER NOT NULL REFERENCES dim.dim_product(product_key),
    week_start   DATE NOT NULL,
    trend        NUMERIC,
    weekly       NUMERIC,
    yearly       NUMERIC,
    holidays     NUMERIC
);

-- 4.2 SHAP Global Importance (per SKU)
CREATE TABLE IF NOT EXISTS mart.shap_global (
    id          SERIAL PRIMARY KEY,
    product_key INTEGER NOT NULL REFERENCES dim.dim_product(product_key),
    feature     TEXT NOT NULL,
    importance  NUMERIC
);

-- 4.3 SHAP Local Explanation (single date)
CREATE TABLE IF NOT EXISTS mart.shap_local (
    id               SERIAL PRIMARY KEY,
    product_key      INTEGER NOT NULL REFERENCES dim.dim_product(product_key),
    explanation_date DATE NOT NULL,
    feature          TEXT NOT NULL,
    impact           NUMERIC
);

-- 4.4 Regressor Status (ok / warning / missing)
CREATE TABLE IF NOT EXISTS mart.regressor_status (
    id          SERIAL PRIMARY KEY,
    feature     TEXT NOT NULL,
    status      TEXT NOT NULL,       -- 'ok' / 'warning' / 'missing'
    last_update DATE
);

-- 4.5 Backtest Leaderboard (used by /api/forecast/backtest)
CREATE TABLE IF NOT EXISTS mart.model_backtest (
    backtest_id  SERIAL PRIMARY KEY,
    model_name   TEXT NOT NULL,      -- 'prophet', 'xgboost', 'tft', ...
    horizon_days INTEGER NOT NULL,
    smape        NUMERIC,
    mae          NUMERIC,
    pinball_p90  NUMERIC,
    coverage     NUMERIC,
    latency      NUMERIC,            -- seconds
    run_id       TEXT,
    trained_at   TIMESTAMPTZ
);

-- 4.6 Model Registry (/api/models/registry)
CREATE TABLE IF NOT EXISTS mart.model_registry (
    model_id    SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,           -- 'xgboost_sparkplug'
    version     TEXT NOT NULL,           -- 'v1', 'v2', ...
    trained_at  TIMESTAMPTZ,
    dataset     TEXT,
    params      JSONB,
    is_champion BOOLEAN DEFAULT FALSE
);

-- 4.7 Model Metrics Over Time (for registry metrics chart)
CREATE TABLE IF NOT EXISTS mart.model_metrics_over_time (
    metric_id  SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    version    TEXT NOT NULL,
    period     TEXT NOT NULL,      -- '2025-W40'
    smape      NUMERIC,
    mae        NUMERIC
);

-- 4.8 Champion Model per SKU (for /api/models/set_champion)
CREATE TABLE IF NOT EXISTS mart.model_champion_per_sku (
    id           SERIAL PRIMARY KEY,
    product_key  INTEGER NOT NULL REFERENCES dim.dim_product(product_key),
    model_name   TEXT NOT NULL,
    version      TEXT NOT NULL,
    effective_from DATE NOT NULL
);

-- ============================================
-- 5. MART: SCENARIO, CAMPAIGN, INVENTORY (C tab)
-- ============================================

-- 5.1 Scenario Elasticity (for /api/scenario/whatif)
CREATE TABLE IF NOT EXISTS mart.scenario_elasticity (
    id          SERIAL PRIMARY KEY,
    product_key INTEGER NOT NULL REFERENCES dim.dim_product(product_key),
    beta_price  NUMERIC,
    beta_promo  NUMERIC,
    beta_ad_spend NUMERIC
);

-- 5.2 Campaign Impact (for /api/campaign/impact)
CREATE TABLE IF NOT EXISTS mart.campaign_impact (
    campaign_id      SERIAL PRIMARY KEY,
    name             TEXT NOT NULL,
    sku              TEXT,
    start_date       DATE,
    end_date         DATE,
    abs_lift         NUMERIC,
    rel_lift         NUMERIC,
    p_value          NUMERIC,
    roi              NUMERIC,
    observed_ts      JSONB,
    counterfactual_ts JSONB,
    reasons          JSONB
);

-- (Inventory recommendations trong UI tính on-the-fly từ forecast,
--  nên không bắt buộc có bảng riêng; nếu sau này muốn log thì tạo thêm mart.inventory_policy_log)

-- ============================================
-- 6. MART: DATA & MONITORING (D_exogenous, D_monitoring)
-- ============================================

-- 6.1 Data Drift Features (for /api/monitoring)
CREATE TABLE IF NOT EXISTS mart.data_drift_features (
    drift_id     SERIAL PRIMARY KEY,
    feature_name TEXT NOT NULL,
    ks_stat      NUMERIC,
    psi          NUMERIC,
    status       TEXT,
    feature_type TEXT,
    source       TEXT,
    calc_at      TIMESTAMPTZ
);

-- 6.2 Rolling Model Metrics (Monitoring line chart)
CREATE TABLE IF NOT EXISTS mart.model_metrics_rolling (
    id        SERIAL PRIMARY KEY,
    week      TEXT NOT NULL,       -- '2025-W40'
    smape     NUMERIC,
    mae       NUMERIC,
    model_name TEXT,
    sku_group  TEXT
);

-- ============================================
-- 7. MART: MARKET INTELLIGENCE (D_market)
-- ============================================

-- 7.1 Market Price by Region (/api/market/intelligence)
CREATE TABLE IF NOT EXISTS mart.market_price_region (
    price_id         SERIAL PRIMARY KEY,
    region           TEXT NOT NULL,      -- 'Vietnam', 'Thailand', ...
    sku              TEXT,               -- optional filter by SKU
    avg_price        NUMERIC,
    competitor_price NUMERIC,
    price_trend      TEXT,               -- 'up' / 'down' / 'flat'
    market_share     NUMERIC,
    as_of_date       DATE
);

-- 7.2 Weather by Region
CREATE TABLE IF NOT EXISTS mart.market_weather_region (
    weather_id   SERIAL PRIMARY KEY,
    region       TEXT NOT NULL,
    condition    TEXT,          -- 'sunny', 'rainy', ...
    temperature  NUMERIC,
    humidity     NUMERIC,
    impact_score NUMERIC,
    as_of_date   DATE
);

-- 7.3 Port Congestion
CREATE TABLE IF NOT EXISTS mart.port_congestion (
    port_id        SERIAL PRIMARY KEY,
    name           TEXT NOT NULL,     -- 'Cat Lai', 'Laem Chabang', ...
    region         TEXT,
    congestion_pct NUMERIC,
    as_of_date     DATE
);

-- 7.4 Warehouse Status
CREATE TABLE IF NOT EXISTS mart.warehouse_status (
    warehouse_id SERIAL PRIMARY KEY,
    region       TEXT NOT NULL,
    capacity     NUMERIC,            -- pallet / CBM / units
    current_stock NUMERIC,
    as_of_date   DATE
);
