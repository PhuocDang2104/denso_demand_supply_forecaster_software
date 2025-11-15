-- ============================================
-- DENSO FORECAST SUITE V3 - SEED DATA
-- Focus: Spark Plug (bugi) + Inverter
-- ============================================

-- 1. Seed dim_product (Spark Plugs + Inverters)
INSERT INTO dim.dim_product (sku, name, family, category, type, channel) VALUES
    -- Spark plugs
    ('K20PR-U',      'Spark Plug K20PR-U Standard',      'Spark Plug', 'Ignition', 'Copper Core',      'Aftermarket'),
    ('SC20HR11',     'Spark Plug Iridium SC20HR11',      'Spark Plug', 'Ignition', 'Iridium',          'Aftermarket'),
    ('IK20',         'Spark Plug Iridium Power IK20',    'Spark Plug', 'Ignition', 'Iridium Power',    'Aftermarket'),
    ('IK22',         'Spark Plug Iridium TT IK22',       'Spark Plug', 'Ignition', 'Iridium TT',       'Aftermarket'),
    ('K16R-U',       'Spark Plug K16R-U Compact',        'Spark Plug', 'Ignition', 'Copper Core',      'Aftermarket'),
    -- Inverters (OEM)
    ('INV-HEV-G1',   'Inverter HEV Gen1',                'Inverter',   'Inverter', 'HEV Inverter',     'OEM'),
    ('INV-PHEV-G2',  'Inverter PHEV Gen2',               'Inverter',   'Inverter', 'PHEV Inverter',    'OEM'),
    ('INV-BEV-G1',   'Inverter BEV Platform A',          'Inverter',   'Inverter', 'BEV Inverter',     'OEM')
ON CONFLICT (sku) DO NOTHING;

-- 2. Seed dim_market (Southeast Asia + basic channels)
INSERT INTO dim.dim_market (country, region, channel) VALUES
    ('Vietnam',     'Southeast Asia', 'Dealer'),
    ('Vietnam',     'Southeast Asia', 'E-commerce'),
    ('Vietnam',     'Southeast Asia', 'OEM'),
    ('Thailand',    'Southeast Asia', 'Dealer'),
    ('Indonesia',   'Southeast Asia', 'Dealer'),
    ('Philippines', 'Southeast Asia', 'Dealer'),
    ('Malaysia',    'Southeast Asia', 'Dealer'),
    ('Singapore',   'Southeast Asia', 'Dealer'),
    ('Thailand',    'Southeast Asia', 'OEM'),
    ('Indonesia',   'Southeast Asia', 'OEM')
ON CONFLICT DO NOTHING;

-- 3. Seed exogenous features (4 tuần gần đây)
INSERT INTO feature.ts_features_weekly
(week_start, pmi, gdp_growth, cpi, gas_price, gtrends_score,
 new_ice_and_hybrid_sales, bev_penetration_rate, weather_event_flag,
 holiday_flag, total_ice_and_hybrid_on_road, own_price_aftermarket,
 comp_price_aftermarket, promo_depth, total_new_vehicle_sales)
VALUES
('2025-10-06', 50.5, 5.8, 3.2, 23000, 60, 12000, 0.08, FALSE, FALSE, 2500000, 1.00, 1.05, 0.10, 18000),
('2025-10-13', 51.0, 5.9, 3.1, 23200, 62, 12500, 0.09, FALSE, FALSE, 2515000, 1.00, 1.04, 0.12, 18500),
('2025-10-20', 51.2, 6.0, 3.0, 23500, 65, 13000, 0.10, TRUE,  FALSE, 2530000, 1.00, 1.03, 0.15, 19000),
('2025-10-27', 50.8, 5.8, 3.1, 23800, 63, 12800, 0.11, FALSE, TRUE,  2540000, 1.02, 1.05, 0.10, 18800);

-- 4. Seed fact_sales_weekly cho 1 bugi + 1 inverter (VN Dealer + OEM)
-- Spark plug K20PR-U - Vietnam Dealer
INSERT INTO fact.fact_sales_weekly
(product_key, market_key, week_start, units_sold, revenue_usd)
SELECT p.product_key, m.market_key, d.week_start,
       v.units_sold, v.revenue_usd
FROM dim.dim_product p
JOIN dim.dim_market m ON m.country = 'Vietnam' AND m.channel = 'Dealer'
JOIN (VALUES
    ('2025-10-06'::date, 1400::numeric, 7000::numeric),
    ('2025-10-13'::date, 1450::numeric, 7250::numeric),
    ('2025-10-20'::date, 1500::numeric, 7500::numeric),
    ('2025-10-27'::date, 1520::numeric, 7600::numeric)
) AS v(week_start, units_sold, revenue_usd) ON TRUE
JOIN (SELECT DISTINCT week_start FROM feature.ts_features_weekly) d ON d.week_start = v.week_start
WHERE p.sku = 'K20PR-U'
ON CONFLICT ON CONSTRAINT uq_sales DO NOTHING;

-- Inverter INV-HEV-G1 - Vietnam OEM
INSERT INTO fact.fact_sales_weekly
(product_key, market_key, week_start, units_sold, revenue_usd)
SELECT p.product_key, m.market_key, d.week_start,
       v.units_sold, v.revenue_usd
FROM dim.dim_product p
JOIN dim.dim_market m ON m.country = 'Vietnam' AND m.channel = 'OEM'
JOIN (VALUES
    ('2025-10-06'::date, 120::numeric, 120000::numeric),
    ('2025-10-13'::date, 130::numeric, 130000::numeric),
    ('2025-10-20'::date, 125::numeric, 125000::numeric),
    ('2025-10-27'::date, 135::numeric, 135000::numeric)
) AS v(week_start, units_sold, revenue_usd) ON TRUE
JOIN (SELECT DISTINCT week_start FROM feature.ts_features_weekly) d ON d.week_start = v.week_start
WHERE p.sku = 'INV-HEV-G1'
ON CONFLICT ON CONSTRAINT uq_sales DO NOTHING;

-- 5. Seed demand_forecast_weekly (fan chart 4 tuần tới)
-- Spark plug K20PR-U - VN Dealer, horizon 28d, model prophet_v1
INSERT INTO mart.demand_forecast_weekly
(product_key, market_key, week_start, horizon_days, model_name, p10, p50, p90, actual)
SELECT p.product_key, m.market_key, v.week_start, 28, 'prophet_v1',
       v.p10, v.p50, v.p90, v.actual
FROM dim.dim_product p
JOIN dim.dim_market m ON m.country = 'Vietnam' AND m.channel = 'Dealer'
JOIN (VALUES
    ('2025-11-03'::date, 1400::numeric, 1500::numeric, 1650::numeric, NULL::numeric),
    ('2025-11-10'::date, 1450::numeric, 1550::numeric, 1700::numeric, NULL::numeric),
    ('2025-11-17'::date, 1470::numeric, 1570::numeric, 1720::numeric, NULL::numeric),
    ('2025-11-24'::date, 1490::numeric, 1600::numeric, 1750::numeric, NULL::numeric)
) AS v(week_start, p10, p50, p90, actual) ON TRUE
WHERE p.sku = 'K20PR-U'
ON CONFLICT DO NOTHING;

-- Inverter INV-HEV-G1 - VN Dealer (để dùng cho dashboard by_category)
INSERT INTO mart.demand_forecast_weekly
(product_key, market_key, week_start, horizon_days, model_name, p10, p50, p90, actual)
SELECT p.product_key, m.market_key, v.week_start, 28, 'xgboost_v1',
       v.p10, v.p50, v.p90, v.actual
FROM dim.dim_product p
JOIN dim.dim_market m ON m.country = 'Vietnam' AND m.channel = 'Dealer'
JOIN (VALUES
    ('2025-11-03'::date, 110::numeric, 120::numeric, 135::numeric, NULL::numeric),
    ('2025-11-10'::date, 115::numeric, 125::numeric, 140::numeric, NULL::numeric),
    ('2025-11-17'::date, 118::numeric, 128::numeric, 145::numeric, NULL::numeric),
    ('2025-11-24'::date, 120::numeric, 130::numeric, 148::numeric, NULL::numeric)
) AS v(week_start, p10, p50, p90, actual) ON TRUE
WHERE p.sku = 'INV-HEV-G1'
ON CONFLICT DO NOTHING;

-- Inverter INV-HEV-G1 - VN OEM
INSERT INTO mart.demand_forecast_weekly
(product_key, market_key, week_start, horizon_days, model_name, p10, p50, p90, actual)
SELECT p.product_key, m.market_key, v.week_start, 28, 'xgboost_v1',
       v.p10, v.p50, v.p90, v.actual
FROM dim.dim_product p
JOIN dim.dim_market m ON m.country = 'Vietnam' AND m.channel = 'OEM'
JOIN (VALUES
    ('2025-11-03'::date, 110::numeric, 120::numeric, 135::numeric, NULL::numeric),
    ('2025-11-10'::date, 115::numeric, 125::numeric, 140::numeric, NULL::numeric),
    ('2025-11-17'::date, 118::numeric, 128::numeric, 145::numeric, NULL::numeric),
    ('2025-11-24'::date, 120::numeric, 130::numeric, 148::numeric, NULL::numeric)
) AS v(week_start, p10, p50, p90, actual) ON TRUE
WHERE p.sku = 'INV-HEV-G1'
ON CONFLICT DO NOTHING;

-- 6. KPI Summary (cho Dashboard Overview)
INSERT INTO mart.kpi_summary
(kpi_date, revenue_p50, revenue_p10, revenue_p90, mape_last_week, coverage_28d)
VALUES
('2025-11-03', 5.4, 4.8, 6.1, 8.7, 93.2)
ON CONFLICT (kpi_date) DO NOTHING;

-- 7. Alerts log (Dashboard Overview + Alert Center)
INSERT INTO mart.alerts_log (level, type, message, link) VALUES
('high', 'stockout_risk', 'Risk of stockout for K20PR-U in Vietnam Dealer within next 2 weeks.', '/dashboard/alerts'),
('med',  'demand_spike',  'Unexpected demand spike detected for SC20HR11 in Thailand Dealer.', '/dashboard/alerts'),
('low',  'coverage_drop', 'Coverage for INV-HEV-G1 OEM channel dropped below 85%.', '/dashboard/alerts');

-- 8. Error by Horizon (for Coverage tab - Error by Horizon chart)
INSERT INTO mart.error_horizon (horizon_days, mape) VALUES
(7,  6.5),
(14, 7.8),
(28, 9.3),
(56, 12.0);

-- 9. Prophet Components (Spark Plug K20PR-U)
INSERT INTO mart.prophet_components
(product_key, week_start, trend, weekly, yearly, holidays)
SELECT p.product_key, v.week_start, v.trend, v.weekly, v.yearly, v.holidays
FROM dim.dim_product p
JOIN (VALUES
    ('2025-11-03'::date, 1400::numeric, 50::numeric, 20::numeric, 10::numeric),
    ('2025-11-10'::date, 1420::numeric, 45::numeric, 18::numeric,  5::numeric),
    ('2025-11-17'::date, 1440::numeric, 48::numeric, 22::numeric,  0::numeric),
    ('2025-11-24'::date, 1460::numeric, 50::numeric, 24::numeric,  0::numeric)
) AS v(week_start, trend, weekly, yearly, holidays) ON TRUE
WHERE p.sku = 'K20PR-U';

-- 10. SHAP Global (Spark Plug K20PR-U)
INSERT INTO mart.shap_global (product_key, feature, importance)
SELECT p.product_key, v.feature, v.importance
FROM dim.dim_product p
JOIN (VALUES
    ('total_ice_and_hybrid_on_road', 0.85),
    ('new_ice_and_hybrid_sales',    0.72),
    ('bev_penetration_rate',       -0.68),
    ('gdp_growth',                  0.45),
    ('promo_depth',                 0.42),
    ('own_price_aftermarket',      -0.38),
    ('cpi',                        -0.35),
    ('gas_price',                  -0.28)
) AS v(feature, importance) ON TRUE
WHERE p.sku = 'K20PR-U';

-- 11. SHAP Local (một ngày cụ thể)
INSERT INTO mart.shap_local
(product_key, explanation_date, feature, impact)
SELECT p.product_key, '2025-11-03'::date, v.feature, v.impact
FROM dim.dim_product p
JOIN (VALUES
    ('promo_depth',               0.25),
    ('gtrends_score',             0.18),
    ('bev_penetration_rate',     -0.20),
    ('own_price_aftermarket',    -0.15),
    ('weather_event_flag',        0.05)
) AS v(feature, impact) ON TRUE
WHERE p.sku = 'K20PR-U';

-- 12. Regressor Status
INSERT INTO mart.regressor_status (feature, status, last_update) VALUES
('pmi',                        'ok',      '2025-10-27'),
('gdp_growth',                 'ok',      '2025-10-27'),
('cpi',                        'warning', '2025-10-27'),
('gas_price',                  'warning', '2025-10-27'),
('gtrends_score',              'warning', '2025-10-27'),
('new_ice_and_hybrid_sales',   'warning', '2025-10-27'),
('bev_penetration_rate',       'warning', '2025-10-27'),
('total_ice_and_hybrid_on_road','ok',     '2025-10-27'),
('own_price_aftermarket',      'ok',      '2025-10-27'),
('comp_price_aftermarket',     'warning', '2025-10-27'),
('promo_depth',                'ok',      '2025-10-27'),
('weather_event_flag',         'ok',      '2025-10-27'),
('holiday_flag',               'ok',      '2025-10-27');

-- 13. Model Backtest (Leaderboard)
INSERT INTO mart.model_backtest
(model_name, horizon_days, smape, mae, pinball_p90, coverage, latency, run_id, trained_at)
VALUES
('prophet_v1', 28, 9.2,  110.5, 12.3, 88.0, 1.1, 'run_2025_10_01', '2025-10-01'),
('xgboost_v1', 28, 8.6,  105.2, 11.1, 90.5, 0.8, 'run_2025_10_02', '2025-10-02'),
('tft_v1',     28, 8.1,  101.0, 10.8, 91.0, 1.5, 'run_2025_10_03', '2025-10-03');

-- 14. Model Registry
INSERT INTO mart.model_registry
(name, version, trained_at, dataset, params, is_champion)
VALUES
('prophet_sparkplug', 'v1', '2025-10-01', '10_sparkplug_dataset_final.csv',
 '{"seasonality":"weekly","changepoint_prior_scale":0.05}'::jsonb, FALSE),
('xgboost_sparkplug', 'v1', '2025-10-02', '10_sparkplug_dataset_final.csv',
 '{"max_depth":6,"eta":0.1,"n_estimators":300}'::jsonb, TRUE),
('tft_sparkplug',     'v1', '2025-10-03', '10_sparkplug_dataset_final.csv',
 '{"hidden_size":64,"num_heads":4}'::jsonb, FALSE);

-- 15. Model Metrics Over Time
INSERT INTO mart.model_metrics_over_time
(model_name, version, period, smape, mae)
VALUES
('xgboost_sparkplug', 'v1', '2025-W40', 8.9, 112.0),
('xgboost_sparkplug', 'v1', '2025-W41', 8.4, 108.0),
('xgboost_sparkplug', 'v1', '2025-W42', 8.1, 105.0),
('tft_sparkplug',     'v1', '2025-W42', 7.9, 103.0);

-- 16. Champion Model per SKU
INSERT INTO mart.model_champion_per_sku
(product_key, model_name, version, effective_from)
SELECT p.product_key, 'xgboost_sparkplug', 'v1', '2025-10-05'
FROM dim.dim_product p
WHERE p.sku IN ('K20PR-U', 'SC20HR11');

-- 17. Scenario Elasticity (dùng cho What-if)
INSERT INTO mart.scenario_elasticity
(product_key, beta_price, beta_promo, beta_ad_spend)
SELECT p.product_key, -1.2, 0.8, 0.3
FROM dim.dim_product p
WHERE p.sku = 'K20PR-U';

-- 18. Campaign Impact (dùng cho /api/campaign/impact)
INSERT INTO mart.campaign_impact
(name, sku, start_date, end_date, abs_lift, rel_lift, p_value, roi,
 observed_ts, counterfactual_ts, reasons)
VALUES
(
 'Spark Plug Tet Promo 2025',
 'K20PR-U',
 '2025-01-20',
 '2025-02-10',
  25000,
  18.5,
  0.012,
  3.8,
  '["day1","day2","day3","day4","day5","day6","day7"]'::jsonb,
  '["cf1","cf2","cf3","cf4","cf5","cf6","cf7"]'::jsonb,
  '["Deep retailer discount","Strong digital marketing","Bundle with free inspection"]'::jsonb
);

-- 19. Coverage by SKU (Monitoring & Coverage tab)
INSERT INTO mart.coverage_by_sku
(product_key, channel, period, coverage_pct)
SELECT p.product_key, v.channel, v.period, v.coverage_pct
FROM dim.dim_product p
JOIN (VALUES
    ('K20PR-U',   'Dealer',    '2025-W40', 92.0),
    ('K20PR-U',   'Dealer',    '2025-W41', 93.5),
    ('SC20HR11',  'Dealer',    '2025-W40', 88.0),
    ('INV-HEV-G1','OEM',       '2025-W40', 85.0),
    ('INV-BEV-G1','OEM',       '2025-W40', 80.0)
) AS v(sku, channel, period, coverage_pct)
ON TRUE
WHERE p.sku = v.sku;

-- 20. Data Drift Features
INSERT INTO mart.data_drift_features
(feature_name, ks_stat, psi, status, feature_type, source, calc_at)
VALUES
('pmi',                         0.08, 0.05, 'stable',  'economic',  'GSO / S&P Global', now()),
('gdp_growth',                  0.12, 0.09, 'stable',  'economic',  'GSO',              now()),
('cpi',                         0.15, 0.13, 'medium',  'economic',  'GSO',              now()),
('gas_price',                   0.18, 0.16, 'medium',  'demand',    'MOIT',             now()),
('gtrends_score',               0.22, 0.19, 'medium',  'demand',    'Google Trends',    now()),
('total_new_vehicle_sales',     0.25, 0.23, 'high',    'demand',    'VAMA',             now()),
('new_ice_and_hybrid_sales',    0.28, 0.26, 'high',    'fleet',     'VAMA/TC Motor',    now()),
('bev_penetration_rate',        0.35, 0.31, 'high',    'fleet',     'Industry Report',  now()),
('total_ice_and_hybrid_on_road',0.14, 0.11, 'medium',  'fleet',     'Registry',         now()),
('own_price_aftermarket',       0.07, 0.04, 'stable',  'commercial','ERP',              now()),
('comp_price_aftermarket',      0.19, 0.17, 'medium',  'commercial','Market Intel',     now()),
('promo_depth',                 0.11, 0.08, 'stable',  'commercial','Marketing',        now()),
('weather_event_flag',          0.06, 0.03, 'stable',  'event',     'Weather Center',   now()),
('holiday_flag',                0.02, 0.01, 'stable',  'event',     'Calendar',         now());

-- 21. Rolling Model Metrics (Monitoring line chart)
INSERT INTO mart.model_metrics_rolling
(week, smape, mae, model_name, sku_group)
VALUES
('2025-W38', 9.5, 120.0, 'xgboost_sparkplug_v1', 'Spark Plug'),
('2025-W39', 9.1, 116.0, 'xgboost_sparkplug_v1', 'Spark Plug'),
('2025-W40', 8.8, 112.0, 'xgboost_sparkplug_v1', 'Spark Plug'),
('2025-W41', 8.4, 108.0, 'xgboost_sparkplug_v1', 'Spark Plug'),
('2025-W42', 8.1, 105.0, 'xgboost_sparkplug_v1', 'Spark Plug');

-- 22. Market Price by Region (/api/market/intelligence)
INSERT INTO mart.market_price_region
(region, sku, avg_price, competitor_price, price_trend, market_share, as_of_date)
VALUES
('Vietnam',    'K20PR-U',  15.0, 16.5, 'up',   32.0, '2025-10-27'),
('Thailand',   'K20PR-U',  14.5, 15.5, 'flat', 28.0, '2025-10-27'),
('Indonesia',  'K20PR-U',  13.8, 14.8, 'down', 30.0, '2025-10-27'),
('Philippines','K20PR-U',  16.0, 17.0, 'up',   26.0, '2025-10-27'),
('Malaysia',   'K20PR-U',  15.2, 16.0, 'flat', 29.0, '2025-10-27'),
('Singapore',  'K20PR-U',  18.0, 19.5, 'up',   24.0, '2025-10-27');

-- 23. Weather by Region
INSERT INTO mart.market_weather_region
(region, condition, temperature, humidity, impact_score, as_of_date)
VALUES
('Vietnam',    'rainy', 29.0, 82.0, 0.9, '2025-10-27'),
('Thailand',   'sunny', 32.0, 70.0, 1.1, '2025-10-27'),
('Indonesia',  'stormy',28.0, 88.0, 0.7, '2025-10-27'),
('Philippines','rainy', 30.0, 85.0, 0.8, '2025-10-27'),
('Malaysia',   'cloudy',31.0, 78.0, 1.0, '2025-10-27'),
('Singapore',  'sunny', 33.0, 65.0, 1.2, '2025-10-27');

-- 24. Port Congestion
INSERT INTO mart.port_congestion
(name, region, congestion_pct, as_of_date)
VALUES
('Cat Lai',        'Vietnam',    68.0, '2025-10-27'),
('Laem Chabang',   'Thailand',   55.0, '2025-10-27'),
('Tanjung Priok',  'Indonesia',  72.0, '2025-10-27'),
('Manila',         'Philippines',64.0, '2025-10-27'),
('Port Klang',     'Malaysia',   58.0, '2025-10-27'),
('Singapore Port', 'Singapore',  61.0, '2025-10-27');

-- 25. Warehouse Status
INSERT INTO mart.warehouse_status
(region, capacity, current_stock, as_of_date)
VALUES
('Vietnam',    100000, 82000, '2025-10-27'),
('Thailand',    80000, 62000, '2025-10-27'),
('Indonesia',   90000, 76000, '2025-10-27'),
('Philippines', 60000, 43000, '2025-10-27'),
('Malaysia',    70000, 48000, '2025-10-27'),
('Singapore',   50000, 38000, '2025-10-27');
