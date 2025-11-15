import os
import random
import json
from datetime import datetime, timedelta

from flask import Flask, render_template, jsonify, request

import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static"
)

# ===================== DB CONFIG =====================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "denso_forecast"),
    "user": os.getenv("DB_USER", "denso"),
    "password": os.getenv("DB_PASSWORD", "admin"),  
}


def query_all(sql, params=None):
    """Run SELECT and return all rows as list[dict]."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


def query_one(sql, params=None):
    """Run SELECT and return single row (dict) or None."""
    rows = query_all(sql, params)
    return rows[0] if rows else None


def execute_sql(sql, params=None):
    """Run INSERT/UPDATE/DELETE."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()


ROLES = ["viewer", "planner", "marketing", "manager", "admin"]

# ===================== PRODUCT LIST (KHỚP dim_product) =====================

# 5 Spark Plugs + 3 Inverters như seed_data.sql
DENSO_SKUS = [
    # Spark plugs
    {"code": "K20PR-U", "name": "Spark Plug K20PR-U Standard", "family": "Spark Plug", "category": "Ignition", "type": "Copper Core", "channel": "Aftermarket"},
    {"code": "SC20HR11", "name": "Spark Plug Iridium SC20HR11", "family": "Spark Plug", "category": "Ignition", "type": "Iridium", "channel": "Aftermarket"},
    {"code": "IK20", "name": "Spark Plug Iridium Power IK20", "family": "Spark Plug", "category": "Ignition", "type": "Iridium Power", "channel": "Aftermarket"},
    {"code": "IK22", "name": "Spark Plug Iridium TT IK22", "family": "Spark Plug", "category": "Ignition", "type": "Iridium TT", "channel": "Aftermarket"},
    {"code": "K16R-U", "name": "Spark Plug K16R-U Compact", "family": "Spark Plug", "category": "Ignition", "type": "Copper Core", "channel": "Aftermarket"},
    # Inverters
    {"code": "INV-HEV-G1", "name": "Inverter HEV Gen1", "family": "Inverter", "category": "Inverter", "type": "HEV Inverter", "channel": "OEM"},
    {"code": "INV-PHEV-G2", "name": "Inverter PHEV Gen2", "family": "Inverter", "category": "Inverter", "type": "PHEV Inverter", "channel": "OEM"},
    {"code": "INV-BEV-G1", "name": "Inverter BEV Platform A", "family": "Inverter", "category": "Inverter", "type": "BEV Inverter", "channel": "OEM"},
]

REGIONS = ["Vietnam", "Thailand", "Indonesia", "Philippines", "Malaysia", "Singapore"]
CHANNELS = ["Dealer", "Retailer", "E-commerce"]  # dùng cho monitoring giả lập / fallback


@app.route("/")
def index():
    role = request.args.get("role", "viewer").lower()
    if role not in ROLES:
        role = "viewer"
    return render_template("index.html", role=role, roles=ROLES)


# ============= A. DASHBOARD APIs =============

@app.get("/api/dashboard")
def api_dashboard():
    """
    Dashboard API:
    - Có thể filter theo sku / country / channel / mode từ query string.
    - Nếu thiếu / sai → rơi về default (K20PR-U, Vietnam, Dealer).
    """
    existing_sku_codes = [s["code"] for s in DENSO_SKUS]

    # ===== 0. Đọc query params từ frontend A =====
    sku_param = request.args.get("sku")
    country = (
        request.args.get("country")
        or request.args.get("region")
        or "Vietnam"
    )
    channel = request.args.get("channel") or "Dealer"
    mode = request.args.get("mode") or "baseline"  # tạm thời chưa dùng

    # SKU chính cho fan chart
    if sku_param and sku_param in existing_sku_codes:
        main_sku = sku_param
    else:
        main_sku = "K20PR-U"  # default nếu không có gì

    try:
        # ===== 1. KPI summary từ mart.kpi_summary (giữ y nguyên) =====
        kpi_row = query_one("""
            SELECT kpi_date,
                   revenue_p50,
                   revenue_p10,
                   revenue_p90,
                   mape_last_week,
                   coverage_28d
            FROM mart.kpi_summary
            ORDER BY kpi_date DESC
            LIMIT 1;
        """)

        if kpi_row:
            kpi = {
                "revenue_p50": float(kpi_row["revenue_p50"]),
                "range_p10_p90": [
                    float(kpi_row["revenue_p10"]),
                    float(kpi_row["revenue_p90"]),
                ],
                "mape_last_week": float(kpi_row["mape_last_week"]),
                "coverage_28d": float(kpi_row["coverage_28d"]),
                "risky_skus": [],
            }
        else:
            raise RuntimeError("No rows in mart.kpi_summary")

        # ===== 2. Risky SKUs (giữ y nguyên) =====
        risky_rows = query_all("""
            SELECT p.sku,
                   c.channel,
                   c.period,
                   c.coverage_pct
            FROM mart.coverage_by_sku c
            JOIN dim.dim_product p ON p.product_key = c.product_key
            ORDER BY c.coverage_pct ASC
            LIMIT 5;
        """)

        if risky_rows:
            kpi["risky_skus"] = [row["sku"] for row in risky_rows]
        else:
            kpi["risky_skus"] = random.sample(
                existing_sku_codes, min(5, len(existing_sku_codes))
            )

        # ===== 3. Fan chart cho SKU được chọn =====
        main_rows = query_all("""
            SELECT df.week_start,
                   df.p10,
                   df.p50,
                   df.p90,
                   df.actual
            FROM mart.demand_forecast_weekly df
            JOIN dim.dim_product p ON p.product_key = df.product_key
            JOIN dim.dim_market m ON m.market_key = df.market_key
            WHERE p.sku = %s
              AND m.country = %s
              AND m.channel = %s
            ORDER BY df.week_start;
        """, (main_sku, country, channel))

        if not main_rows:
            raise RuntimeError(
                f"No rows in mart.demand_forecast_weekly for {main_sku} {country} {channel}"
            )

        labels = [row["week_start"].strftime("%Y-%m-%d") for row in main_rows]
        fan = {
            "labels": labels,
            "p10": [float(row["p10"]) for row in main_rows],
            "p50": [float(row["p50"]) for row in main_rows],
            "p90": [float(row["p90"]) for row in main_rows],
            "actual": [
                float(row["actual"]) if row["actual"] is not None else None
                for row in main_rows
            ],
        }

        # ===== 3b. Category breakdown: tổng theo family trên cùng country/channel =====
        cat_rows = query_all("""
            SELECT df.week_start,
                   p.family,
                   SUM(df.p50) AS p50
            FROM mart.demand_forecast_weekly df
            JOIN dim.dim_product p ON p.product_key = df.product_key
            JOIN dim.dim_market m ON m.market_key = df.market_key
            WHERE m.country = %s
              AND m.channel = %s
            GROUP BY df.week_start, p.family
            ORDER BY df.week_start, p.family;
        """, (country, channel))

        if cat_rows:
            week_keys = sorted({r["week_start"].strftime("%Y-%m-%d") for r in cat_rows})
            families = sorted({r["family"] for r in cat_rows})
            value_map = {
                (r["week_start"].strftime("%Y-%m-%d"), r["family"]): float(r["p50"])
                for r in cat_rows
            }

            by_category = {"labels": week_keys}
            for fam in families:
                by_category[fam] = [
                    value_map.get((w, fam), None) for w in week_keys
                ]

            fan["by_category"] = by_category
        else:
            # nếu không có cat_rows thì giữ logic cũ cho by_category hoặc bỏ qua
            fan["by_category"] = {
                "labels": labels,
                "Ignition": [float(r["p50"]) for r in main_rows],
            }

        # ===== 4. Alerts (giữ nguyên) =====
        alert_rows = query_all("""
            SELECT level, type, message, link
            FROM mart.alerts_log
            ORDER BY created_at DESC;
        """)

        alerts = [
            {
                "level": row["level"],
                "type": row["type"],
                "msg": row["message"],
                "link": row["link"],
            }
            for row in alert_rows
        ] if alert_rows else []

        if not alerts:
            alerts = [
                {
                    "level": "low",
                    "type": "info",
                    "msg": "No alerts in mart.alerts_log table.",
                    "link": "/dashboard",
                }
            ]

        # ===== 5. Coverage heatmap (giữ nguyên) =====
        coverage_rows = query_all("""
            SELECT p.sku,
                   c.channel,
                   c.period,
                   c.coverage_pct
            FROM mart.coverage_by_sku c
            JOIN dim.dim_product p ON p.product_key = c.product_key
            ORDER BY c.period ASC, c.channel ASC;
        """)

        if coverage_rows:
            weeks = sorted({row["period"] for row in coverage_rows})
            channels = sorted({row["channel"] for row in coverage_rows})

            cov_map = {
                (row["channel"], row["period"]): float(row["coverage_pct"])
                for row in coverage_rows
            }

            grid = []
            for ch in channels:
                row_vals = []
                for w in weeks:
                    row_vals.append(cov_map.get((ch, w), None))
                grid.append(row_vals)

            coverage = {
                "weeks": weeks,
                "channels": channels,
                "grid": grid,
            }
        else:
            raise RuntimeError("No rows in mart.coverage_by_sku")

        # ===== 6. Error by horizon (giữ nguyên) =====
        err_rows = query_all("""
            SELECT horizon_days, mape
            FROM mart.error_horizon
            ORDER BY horizon_days;
        """)

        if err_rows:
            error_hz = {
                "horizons": [int(row["horizon_days"]) for row in err_rows],
                "errors": [float(row["mape"]) for row in err_rows],
            }
        else:
            raise RuntimeError("No rows in mart.error_horizon")

        return jsonify(
            {
                "kpi": kpi,
                "fan": fan,
                "alerts": alerts,
                "coverage": coverage,
                "error_horizon": error_hz,
            }
        )

    except Exception as e:
        print(
            ">>> [api_dashboard] DB error or missing data, falling back to random mock:",
            repr(e),
        )
        # phần fallback random của bạn giữ nguyên, không bắt buộc phải động vào
        # (cứ để y như code cũ)
        weeks = [f"W{i}" for i in range(1, 9)]

        kpi = {
            "revenue_p50": round(random.uniform(3.2, 5.8), 2),
            "range_p10_p90": [
                round(random.uniform(2.1, 2.8), 2),
                round(random.uniform(5.2, 6.9), 2),
            ],
            "mape_last_week": round(random.uniform(6.5, 15.2), 2),
            "coverage_28d": round(random.uniform(82, 96), 1),
            "risky_skus": random.sample(
                existing_sku_codes, min(5, len(existing_sku_codes))
            ),
        }

        days = [
            (datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(56)
        ][::-1]
        fan = {
            "labels": days,
            "p10": [random.randint(85, 115) for _ in days],
            "p50": [random.randint(115, 160) for _ in days],
            "p90": [random.randint(160, 205) for _ in days],
            "actual": [random.randint(95, 180) for _ in range(28)],
            "by_category": {
                "labels": days,
                "Ignition": [random.randint(45, 95) for _ in days],
                "Inverter": [random.randint(20, 60) for _ in days],
            },
        }

        alerts = [
            {
                "level": "high",
                "type": "break_seasonality",
                "msg": f"{existing_sku_codes[0]} deviates from seasonal pattern",
                "link": "/forecast/sku",
            },
            {
                "level": "high",
                "type": "error_threshold",
                "msg": "MAPE >20% for Thailand Dealer channel",
                "link": "/forecast/backtest",
            },
            {
                "level": "med",
                "type": "spike",
                "msg": "Spike detected in Indonesia Dealer (week W4)",
                "link": "/dashboard",
            },
            {
                "level": "med",
                "type": "coverage_drop",
                "msg": "Coverage dropped to 72% for Malaysia region",
                "link": "/monitoring",
            },
            {
                "level": "low",
                "type": "drift",
                "msg": "Minor data drift in feature 'price_idx'",
                "link": "/data/exogenous",
            },
        ]

        coverage = {
            "weeks": weeks,
            "channels": CHANNELS,
            "grid": [[random.randint(65, 98) for _ in weeks] for _ in CHANNELS],
        }

        error_hz = {
            "horizons": [1, 7, 14, 28],
            "errors": [round(random.uniform(5.2, 22.8), 1) for _ in range(4)],
        }

        return jsonify(
            {
                "kpi": kpi,
                "fan": fan,
                "alerts": alerts,
                "coverage": coverage,
                "error_horizon": error_hz,
            }
        )


# ============= B. FORECAST APIs =============

@app.get("/api/forecast/sku")
def api_forecast_sku():
    """
    Chi tiết forecast cho từng SKU:
    - Fan chart: mart.demand_forecast_weekly + dim_market
    - Prophet components: mart.prophet_components
    - SHAP global/local: mart.shap_global, mart.shap_local
    - Regressor status: mart.regressor_status
    """
    sku_code = request.args.get("sku", DENSO_SKUS[0]["code"])

    try:
        # ---- 0. Product info từ dim_product ----
        prod_row = query_one("""
            SELECT product_key, sku, name, family, category, type, channel
            FROM dim.dim_product
            WHERE sku = %s;
        """, (sku_code,))

        if not prod_row:
            # fallback: dùng struct từ DENSO_SKUS list
            sku_obj = next((s for s in DENSO_SKUS if s["code"] == sku_code), DENSO_SKUS[0])
            raise RuntimeError("SKU not found in dim_product, using fallback")

        sku_obj = {
            "code": prod_row["sku"],
            "name": prod_row["name"],
            "family": prod_row["family"],
            "category": prod_row["category"],
            "type": prod_row["type"],
            "channel": prod_row["channel"],
        }

        # ---- 1. Fan chart: mart.demand_forecast_weekly ----
        fan_rows = query_all("""
            SELECT df.week_start,
                   df.p10,
                   df.p50,
                   df.p90,
                   df.actual,
                   m.country,
                   m.channel
            FROM mart.demand_forecast_weekly df
            JOIN dim.dim_market m ON m.market_key = df.market_key
            WHERE df.product_key = %s
            ORDER BY df.week_start;
        """, (prod_row["product_key"],))

        if fan_rows:
            labels = [row["week_start"].strftime("%Y-%m-%d") for row in fan_rows]
            fan = {
                "labels": labels,
                "p10": [float(row["p10"]) for row in fan_rows],
                "p50": [float(row["p50"]) for row in fan_rows],
                "p90": [float(row["p90"]) for row in fan_rows],
                "actual": [float(row["actual"]) if row["actual"] is not None else None for row in fan_rows]
            }
        else:
            # nếu chưa có forecast trong DB cho SKU này → mock
            days = [(datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(56)][::-1]
            fan = {
                "labels": days,
                "p10": [random.randint(65, 100) for _ in days],
                "p50": [random.randint(95, 140) for _ in days],
                "p90": [random.randint(135, 180) for _ in days],
                "actual": [random.randint(75, 160) for _ in range(28)]
            }

        # ---- 2. Prophet components ----
        comp_rows = query_all("""
            SELECT week_start, trend, weekly, yearly, holidays
            FROM mart.prophet_components
            WHERE product_key = %s
            ORDER BY week_start;
        """, (prod_row["product_key"],))

        if comp_rows:
            comp_labels = [r["week_start"].strftime("%Y-%m-%d") for r in comp_rows]
            components = {
                "labels": comp_labels,
                "trend": [float(r["trend"]) for r in comp_rows],
                "weekly": [float(r["weekly"]) for r in comp_rows],
                "yearly": [float(r["yearly"]) for r in comp_rows],
                "holidays": [float(r["holidays"]) for r in comp_rows],
            }
        else:
            # fallback: synthetic components từ fan labels
            labels = fan["labels"]
            components = {
                "labels": labels,
                "trend": [random.uniform(-1.2, 1.2) for _ in labels],
                "weekly": [random.uniform(-0.7, 0.7) for _ in labels],
                "yearly": [random.uniform(-0.4, 0.4) for _ in labels],
                "holidays": [0 for _ in labels],
            }

        # ---- 3. Regressor status ----
        reg_rows = query_all("""
            SELECT feature, status, last_update
            FROM mart.regressor_status
            ORDER BY feature;
        """)

        regressors = [
            {
                "name": r["feature"],
                "status": r["status"]
            } for r in reg_rows
        ] if reg_rows else [
            {"name": "pmi", "status": "ok"},
            {"name": "gdp_growth", "status": "ok"},
            {"name": "cpi", "status": "warning"},
        ]

        # ---- 4. SHAP global ----
        shap_g_rows = query_all("""
            SELECT feature, importance
            FROM mart.shap_global
            WHERE product_key = %s
            ORDER BY importance DESC;
        """, (prod_row["product_key"],))

        shap_global = [
            {"feature": r["feature"], "importance": float(r["importance"])}
            for r in shap_g_rows
        ] if shap_g_rows else [
            {"feature": "price_idx", "importance": 0.32},
            {"feature": "promo_depth", "importance": 0.27},
        ]

        # ---- 5. SHAP local ----
        shap_l_rows = query_all("""
            SELECT explanation_date, feature, impact
            FROM mart.shap_local
            WHERE product_key = %s
            ORDER BY explanation_date DESC;
        """, (prod_row["product_key"],))

        if shap_l_rows:
            latest_date = shap_l_rows[0]["explanation_date"].strftime("%Y-%m-%d")
            items = [
                {
                    "feature": r["feature"],
                    "value": None,
                    "impact": float(r["impact"])
                }
                for r in shap_l_rows if r["explanation_date"] == shap_l_rows[0]["explanation_date"]
            ]
            shap_local = {
                "date": latest_date,
                "items": items
            }
        else:
            shap_local = {
                "date": (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "items": [
                    {"feature": "promo_depth", "value": 0.35, "impact": 0.18},
                    {"feature": "holiday_flag", "value": 1, "impact": 0.12},
                ]
            }

        data = {
            "sku": sku_obj,
            "fan": fan,
            "components": components,
            "regressors": regressors,
            "shap_global": shap_global,
            "shap_local": shap_local
        }

        return jsonify(data)

    except Exception as e:
        print(">>> [api_forecast_sku] error, falling back to mock:", repr(e))
        # fallback toàn bộ logic cũ
        sku_obj = next((s for s in DENSO_SKUS if s["code"] == sku_code), DENSO_SKUS[0])
        days = [(datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(56)][::-1]

        data = {
            "sku": sku_obj,
            "fan": {
                "labels": days,
                "p10": [random.randint(65, 100) for _ in days],
                "p50": [random.randint(95, 140) for _ in days],
                "p90": [random.randint(135, 180) for _ in days],
                "actual": [random.randint(75, 160) for _ in range(28)]
            },
            "components": {
                "labels": days,
                "trend": [random.uniform(-1.2, 1.2) for _ in days],
                "weekly": [random.uniform(-0.7, 0.7) for _ in days],
                "yearly": [random.uniform(-0.4, 0.4) for _ in days],
                "holidays": [0 if i % 15 else random.uniform(0.3, 1.5) for i, _ in enumerate(days)],
            },
            "regressors": [
                {"name": "price_idx", "status": "ok"},
                {"name": "promo_depth", "status": "ok"},
                {"name": "ad_spend", "status": "partial"},
                {"name": "competitor_price", "status": "ok"},
                {"name": "weather_index", "status": "ok"},
            ],
            "shap_global": [
                {"feature": "price_idx", "importance": 0.32},
                {"feature": "promo_depth", "importance": 0.27},
                {"feature": "holiday_flag", "importance": 0.16},
                {"feature": "ad_spend", "importance": 0.12},
                {"feature": "competitor_price", "importance": 0.08},
                {"feature": "weather_index", "importance": 0.05}
            ],
            "shap_local": {
                "date": (datetime.today() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "items": [
                    {"feature": "price_idx", "value": 1.03, "impact": -0.23},
                    {"feature": "promo_depth", "value": 0.35, "impact": 0.18},
                    {"feature": "holiday_flag", "value": 1, "impact": 0.12},
                    {"feature": "ad_spend", "value": 0.65, "impact": 0.08}
                ]
            }
        }
        return jsonify(data)


@app.get("/api/forecast/backtest")
def api_backtest():
    """
    Leaderboard backtest:
    - Dùng mart.model_backtest
    """
    try:
        rows = query_all("""
            SELECT model_name, horizon_days, smape, mae, pinball_p90, coverage, latency
            FROM mart.model_backtest
            ORDER BY horizon_days, smape;
        """)

        leaderboard = []
        for r in rows:
            leaderboard.append({
                "model": r["model_name"],
                "sMAPE": float(r["smape"]),
                "MAE": float(r["mae"]),
                "PinballP90": float(r["pinball_p90"]) if r["pinball_p90"] is not None else None,
                "Coverage": float(r["coverage"]) if r["coverage"] is not None else None,
                "Latency": float(r["latency"]) if r["latency"] is not None else None,
            })

        if not leaderboard:
            raise RuntimeError("No rows in mart.model_backtest")

        return jsonify({"leaderboard": leaderboard})

    except Exception as e:
        print(">>> [api_backtest] DB error, fallback to random:", repr(e))
        models = ["Prophet_1.3", "LGBM_1.0", "XGBoost"]
        leaderboard = []

        for m in models:
            leaderboard.append({
                "model": m,
                "sMAPE": round(random.uniform(7, 16), 2),
                "MAE": round(random.uniform(10, 32), 2),
                "PinballP90": round(random.uniform(0.05, 0.14), 3),
                "Coverage": round(random.uniform(78, 96), 1),
                "Latency": round(random.uniform(0.04, 0.38), 2)
            })

        return jsonify({"leaderboard": leaderboard})


# ============= C. SCENARIO, CAMPAIGN, INVENTORY APIs =============

@app.post("/api/scenario/whatif")
def api_whatif():
    """
    What-if: dùng hệ số beta trong mart.scenario_elasticity (nếu có),
    default SKU: K20PR-U.
    """
    body = request.json or {}
    sku_code = body.get("sku", "K20PR-U")

    baseline = 135.0  # có thể sau này lấy từ forecast P50

    price_delta = body.get("price_delta", 0.0)
    promo_depth = body.get("promo_depth", 0.0)
    ad_spend = body.get("ad_spend", 0.0)

    try:
        prod_row = query_one("""
            SELECT product_key
            FROM dim.dim_product
            WHERE sku = %s;
        """, (sku_code,))

        if not prod_row:
            raise RuntimeError("SKU not found in dim_product")

        el_row = query_one("""
            SELECT beta_price, beta_promo, beta_ad_spend
            FROM mart.scenario_elasticity
            WHERE product_key = %s;
        """, (prod_row["product_key"],))

        if el_row:
            beta_price = float(el_row["beta_price"])
            beta_promo = float(el_row["beta_promo"])
            beta_ad = float(el_row["beta_ad_spend"])
        else:
            beta_price, beta_promo, beta_ad = -0.85, 0.75, 0.18

        price_factor = 1 + (price_delta / 100.0) * beta_price
        promo_factor = 1 + promo_depth * beta_promo
        ad_factor = 1 + ad_spend * beta_ad

        fc = round(baseline * price_factor * promo_factor * ad_factor, 2)
        margin = round(fc * 0.32, 2)

        return jsonify({"forecast": fc, "margin": margin, "sku": sku_code})

    except Exception as e:
        print(">>> [api_whatif] DB error, fallback simple elastic:", repr(e))

        price_factor = 1 - (price_delta / 100.0) * 0.85
        promo_factor = 1 + promo_depth * 0.75
        ad_factor = 1 + ad_spend * 0.18

        fc = round(baseline * price_factor * promo_factor * ad_factor, 2)
        margin = round(fc * 0.32, 2)

        return jsonify({"forecast": fc, "margin": margin, "sku": sku_code})


@app.get("/api/campaign/impact")
def api_campaign():
    """
    Campaign impact:
    - Lấy summary từ mart.campaign_impact (abs_lift, rel_lift, p_value, roi, reasons)
    - Time series observed/counterfactual: nếu JSON trong DB không phải numeric → random fallback.
    """
    try:
        row = query_one("""
            SELECT name, sku, start_date, end_date,
                   abs_lift, rel_lift, p_value, roi,
                   observed_ts, counterfactual_ts, reasons
            FROM mart.campaign_impact
            ORDER BY start_date DESC
            LIMIT 1;
        """)

        if not row:
            raise RuntimeError("No rows in mart.campaign_impact")

        # parse JSONB nếu cần
        obs_raw = row["observed_ts"]
        cf_raw = row["counterfactual_ts"]
        reasons_raw = row["reasons"]

        # psycopg2 nhiều khi đã convert JSONB thành list, nếu là str thì load
        if isinstance(obs_raw, str):
            try:
                observed = json.loads(obs_raw)
            except Exception:
                observed = None
        else:
            observed = obs_raw

        if isinstance(cf_raw, str):
            try:
                counterfactual = json.loads(cf_raw)
            except Exception:
                counterfactual = None
        else:
            counterfactual = cf_raw

        if isinstance(reasons_raw, str):
            try:
                reasons = json.loads(reasons_raw)
            except Exception:
                reasons = []
        else:
            reasons = reasons_raw or []

        # nếu observed/counterfactual không phải numeric series → random fallback
        n_points = 7
        if not (isinstance(observed, list) and isinstance(counterfactual, list) and
                len(observed) == len(counterfactual) and
                all(isinstance(x, (int, float)) for x in observed if x is not None) and
                all(isinstance(x, (int, float)) for x in counterfactual if x is not None)):
            days = [(row["start_date"] + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n_points)]
            observed = [random.randint(95, 165) for _ in days]
            counterfactual = [max(65, v - random.randint(8, 25)) for v in observed]
        else:
            n_points = len(observed)
            days = [(row["start_date"] + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n_points)]

        abs_lift = float(row["abs_lift"]) if row["abs_lift"] is not None else (sum(observed) - sum(counterfactual))
        rel_lift = float(row["rel_lift"]) if row["rel_lift"] is not None else abs_lift / max(1, sum(counterfactual))
        p_value = float(row["p_value"]) if row["p_value"] is not None else random.uniform(0.001, 0.05)
        roi = float(row["roi"]) if row["roi"] is not None else random.uniform(1.2, 3.8)

        return jsonify({
            "days": days,
            "observed": observed,
            "counterfactual": counterfactual,
            "cards": {
                "abs_lift": abs_lift,
                "rel_lift": round(rel_lift * 100, 2),
                "ci_95": [round(abs_lift * 0.88), round(abs_lift * 1.12)],
                "p_value": round(p_value, 4),
                "roi": round(roi, 2)
            },
            "reasons": reasons or [
                "Deep retailer discount",
                "Strong digital marketing",
                "Bundle with free inspection"
            ],
            "name": row["name"],
            "sku": row["sku"]
        })

    except Exception as e:
        print(">>> [api_campaign] DB error, fallback random:", repr(e))
        days = [(datetime.today() - timedelta(days=14)) + timedelta(days=i) for i in range(28)]
        days = [d.strftime("%Y-%m-%d") for d in days]

        observed = [random.randint(95, 165) for _ in days]
        counterfactual = [max(65, v - random.randint(8, 25)) for v in observed]

        abs_lift = sum(observed) - sum(counterfactual)
        rel_lift = abs_lift / max(1, sum(counterfactual))

        return jsonify({
            "days": days,
            "observed": observed,
            "counterfactual": counterfactual,
            "cards": {
                "abs_lift": abs_lift,
                "rel_lift": round(rel_lift * 100, 2),
                "ci_95": [round(abs_lift * 0.88), round(abs_lift * 1.12)],
                "p_value": round(random.uniform(0.001, 0.05), 4),
                "roi": round(random.uniform(1.2, 3.8), 2)
            },
            "reasons": [
                "Strong promotional depth (30% off)",
                "Aligned with regional holiday (Tet/Songkran)",
                "High digital ad recall rate",
                "Positive weather conditions"
            ]
        })


@app.post("/api/inventory/recommend")
def api_inventory_rec():
    """
    Inventory: tính on-the-fly, chưa cần bảng log trong DB.
    """
    body = request.json or {}
    service_level = float(body.get("service_level", 0.95))
    lead_time = int(body.get("lead_time", 7))
    on_hand = int(body.get("on_hand", 100))
    on_order = int(body.get("on_order", 40))
    moq = int(body.get("moq", 24))

    demand_p50 = 130
    demand_p90 = 165

    z_score = 1.96 if service_level >= 0.95 else (1.65 if service_level >= 0.90 else 1.28)
    safety_stock = round((demand_p90 - demand_p50) * z_score * 0.12)
    base_stock = demand_p50 + safety_stock

    po_recommend = max(0, base_stock - on_hand - on_order)
    if po_recommend > 0 and (po_recommend % moq) != 0:
        po_recommend = ((po_recommend // moq) + 1) * moq

    return jsonify({
        "base_stock": base_stock,
        "safety_stock": safety_stock,
        "po_recommend": po_recommend,
        "reason": f"Based on P50={demand_p50}, P90={demand_p90}, service level={service_level}, lead_time={lead_time}"
    })


# ============= D. DATA, MONITORING, MODEL APIs =============

@app.get("/api/data/exogenous")
def api_exog():
    """Lấy dữ liệu từ feature.ts_features_weekly, map sang format cũ."""
    try:
        rows = query_all("""
            SELECT week_start,
                   pmi, gdp_growth, cpi,
                   gas_price, gtrends_score,
                   total_new_vehicle_sales,
                   new_ice_and_hybrid_sales,
                   bev_penetration_rate,
                   total_ice_and_hybrid_on_road,
                   own_price_aftermarket,
                   comp_price_aftermarket,
                   promo_depth,
                   weather_event_flag,
                   holiday_flag
            FROM feature.ts_features_weekly
            ORDER BY week_start;
        """)

        if not rows:
            raise RuntimeError("No rows in feature.ts_features_weekly")

        result = []
        for r in rows:
            ds = r["week_start"].strftime("%Y-%m-%d")
            weather = "stormy" if r["weather_event_flag"] else "sunny"
            result.append({
                "ds": ds,
                "pmi": float(r["pmi"]),
                "gdp_growth": float(r["gdp_growth"]),
                "cpi": float(r["cpi"]),
                "gas_price": float(r["gas_price"]),
                "gtrends_score": float(r["gtrends_score"]),
                "total_new_vehicle_sales": float(r["total_new_vehicle_sales"]),
                "new_ice_and_hybrid_sales": float(r["new_ice_and_hybrid_sales"]),
                "bev_penetration_rate": float(r["bev_penetration_rate"]),
                "total_ice_and_hybrid_on_road": float(r["total_ice_and_hybrid_on_road"]),
                "own_price_aftermarket": float(r["own_price_aftermarket"]),
                "comp_price_aftermarket": float(r["comp_price_aftermarket"]),
                "promo_depth": float(r["promo_depth"]),
                "weather_event_flag": bool(r["weather_event_flag"]),
                "holiday_flag": bool(r["holiday_flag"]),
                # legacy fields
                "price_idx": round(float(r["own_price_aftermarket"]) / float(r["comp_price_aftermarket"]), 3)
                if r["comp_price_aftermarket"] not in (0, None) else 1.0,
                "weather": weather,
                "search": int(r["gtrends_score"]),
                "competitor_price": float(r["comp_price_aftermarket"])
            })

        return jsonify({"rows": result})

    except Exception as e:
        print(">>> [api_exog] DB error, fallback random:", repr(e))
        rows = []
        base_date = datetime.today() - timedelta(days=30)

        for i in range(30):
            current_date = base_date + timedelta(days=i)
            rows.append({
                "ds": current_date.strftime("%Y-%m-%d"),
                "pmi": round(random.uniform(47.5, 53.5), 1),
                "gdp_growth": round(random.uniform(3.5, 6.1), 1),
                "cpi": round(random.uniform(2.5, 4.2), 1),
                "gas_price": round(random.uniform(23000, 26000), 0),
                "gtrends_score": random.randint(35, 85),
                "total_new_vehicle_sales": round(random.uniform(25000, 38000), 0),
                "new_ice_and_hybrid_sales": round(random.uniform(18000, 30000), 0),
                "bev_penetration_rate": round(random.uniform(0.02, 0.45), 3),
                "total_ice_and_hybrid_on_road": random.randint(3800000, 4200000),
                "own_price_aftermarket": random.randint(109000, 112000),
                "comp_price_aftermarket": random.randint(108500, 111500),
                "promo_depth": round(random.uniform(0, 0.15), 2),
                "weather_event_flag": random.randint(0, 1) if random.random() < 0.03 else 0,
                "holiday_flag": random.randint(0, 1) if random.random() < 0.08 else 0,
                "price_idx": round(random.uniform(0.88, 1.25), 2),
                "weather": random.choice(["sunny", "rainy", "cloudy", "stormy"]),
                "search": random.randint(55, 165),
                "competitor_price": round(random.uniform(0.85, 1.15), 2)
            })

        return jsonify({"rows": rows})


@app.get("/api/market/intelligence")
def api_market_intelligence():
    """
    Market Intelligence:
    - Price: mart.market_price_region
    - Weather: mart.market_weather_region
    - Port: mart.port_congestion
    - Warehouse: mart.warehouse_status
    - sku_insights: mock (chưa có bảng riêng)
    """
    skus = request.args.get("skus", "").split(",") if request.args.get("skus") else []

    # static geo mapping
    port_geo = {
        "Cat Lai": (10.7769, 106.7009),
        "Laem Chabang": (13.09, 100.89),
        "Tanjung Priok": (-6.104, 106.88),
        "Manila": (14.5995, 120.9842),
        "Port Klang": (3.1390, 101.6869),
        "Singapore Port": (1.3521, 103.8198),
    }
    region_geo = {
        "Vietnam": (21.0285, 105.8542),
        "Thailand": (13.7563, 100.5018),
        "Indonesia": (-6.2088, 106.8456),
        "Philippines": (14.5995, 120.9842),
        "Malaysia": (3.1390, 101.6869),
        "Singapore": (1.3521, 103.8198),
    }

    try:
        # ----- Price data -----
        price_rows = query_all("""
            SELECT region, sku, avg_price, competitor_price, price_trend, market_share
            FROM mart.market_price_region
            WHERE as_of_date = (
                SELECT MAX(as_of_date) FROM mart.market_price_region AS sub
                WHERE sub.region = mart.market_price_region.region
            );
        """)

        price_data = {}
        for r in price_rows:
            region = r["region"]
            price_data[region] = {
                "avg_price": float(r["avg_price"]),
                "competitor_price": float(r["competitor_price"]),
                "price_trend": r["price_trend"],
                "market_share": float(r["market_share"])
            }

        if not price_data:
            raise RuntimeError("No rows in mart.market_price_region")

        # ----- Weather data -----
        weather_rows = query_all("""
            SELECT region, condition, temperature, humidity, impact_score
            FROM mart.market_weather_region
            WHERE as_of_date = (
                SELECT MAX(as_of_date) FROM mart.market_weather_region AS sub
                WHERE sub.region = mart.market_weather_region.region
            );
        """)

        weather_data = {}
        for r in weather_rows:
            weather_data[r["region"]] = {
                "condition": r["condition"],
                "temperature": float(r["temperature"]),
                "humidity": float(r["humidity"]),
                "impact_score": float(r["impact_score"])
            }

        # ----- Port logistics -----
        port_rows = query_all("""
            SELECT name, region, congestion_pct
            FROM mart.port_congestion
            WHERE as_of_date = (SELECT MAX(as_of_date) FROM mart.port_congestion);
        """)

        port_data = []
        for r in port_rows:
            lat, lng = port_geo.get(r["name"], region_geo.get(r["region"], (0.0, 0.0)))
            port_data.append({
                "name": r["name"],
                "region": r["region"],
                "lat": lat,
                "lng": lng,
                "congestion": float(r["congestion_pct"]),
                "delay_days": random.randint(0, 7)
            })

        # ----- Warehouse / inventory -----
        wh_rows = query_all("""
            SELECT region, capacity, current_stock
            FROM mart.warehouse_status
            WHERE as_of_date = (SELECT MAX(as_of_date) FROM mart.warehouse_status);
        """)

        warehouse_data = []
        for r in wh_rows:
            lat, lng = region_geo.get(r["region"], (0.0, 0.0))
            warehouse_data.append({
                "name": f"Denso Warehouse {r['region']}",
                "region": r["region"],
                "lat": lat,
                "lng": lng,
                "capacity": float(r["capacity"]),
                "current_stock": float(r["current_stock"])
            })

        # ----- sku_insights (mock) -----
        sku_insights = {}
        if skus:
            for sku_code in skus:
                sku_obj = next((s for s in DENSO_SKUS if s["code"] == sku_code), None)
                if sku_obj:
                    sku_insights[sku_code] = {
                        "name": sku_obj["name"],
                        "avg_price_usd": round(random.uniform(5.0, 35.0), 2),
                        "demand_trend": random.choice(["rising", "stable", "declining"]),
                        "stock_level": random.choice(["high", "medium", "low"]),
                        "competitor_count": random.randint(3, 12),
                        "market_leader": random.choice([True, False])
                    }

        return jsonify({
            "price_data": price_data,
            "weather_data": weather_data,
            "port_data": port_data,
            "warehouse_data": warehouse_data,
            "sku_insights": sku_insights,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        print(">>> [api_market_intelligence] DB error, fallback random:", repr(e))

        # fallback: dùng logic random cũ
        price_data = {}
        for region in REGIONS:
            price_data[region] = {
                "avg_price": round(random.uniform(8.5, 25.0), 2),
                "competitor_price": round(random.uniform(9.0, 26.0), 2),
                "price_trend": random.choice(["up", "down", "stable"]),
                "market_share": round(random.uniform(15, 45), 1)
            }

        weather_conditions = ["sunny", "rainy", "cloudy", "stormy", "hazy"]
        weather_data = {}
        for region in REGIONS:
            weather_data[region] = {
                "condition": random.choice(weather_conditions),
                "temperature": round(random.uniform(22, 36), 1),
                "humidity": round(random.uniform(60, 95), 0),
                "impact_score": round(random.uniform(0.6, 1.4), 2)
            }

        port_data = [
            {"name": "Port of Ho Chi Minh", "region": "Vietnam", "lat": 10.7769, "lng": 106.7009, "congestion": random.randint(20, 85), "delay_days": random.randint(0, 5)},
            {"name": "Port of Bangkok", "region": "Thailand", "lat": 13.7563, "lng": 100.5018, "congestion": random.randint(15, 75), "delay_days": random.randint(0, 4)},
            {"name": "Port of Jakarta", "region": "Indonesia", "lat": -6.2088, "lng": 106.8456, "congestion": random.randint(30, 90), "delay_days": random.randint(1, 7)},
            {"name": "Port of Manila", "region": "Philippines", "lat": 14.5995, "lng": 120.9842, "congestion": random.randint(25, 80), "delay_days": random.randint(0, 6)},
            {"name": "Port Klang", "region": "Malaysia", "lat": 3.1390, "lng": 101.6869, "congestion": random.randint(10, 60), "delay_days": random.randint(0, 3)},
            {"name": "Port of Singapore", "region": "Singapore", "lat": 1.3521, "lng": 103.8198, "congestion": random.randint(5, 45), "delay_days": random.randint(0, 2)}
        ]

        warehouse_data = [
            {"name": "Denso Warehouse Hanoi", "region": "Vietnam", "lat": 21.0285, "lng": 105.8542, "capacity": 85000, "current_stock": random.randint(50000, 80000)},
            {"name": "Denso Warehouse Ho Chi Minh", "region": "Vietnam", "lat": 10.8231, "lng": 106.6297, "capacity": 120000, "current_stock": random.randint(80000, 115000)},
            {"name": "Denso Warehouse Bangkok", "region": "Thailand", "lat": 13.7563, "lng": 100.5018, "capacity": 150000, "current_stock": random.randint(100000, 145000)},
            {"name": "Denso Warehouse Jakarta", "region": "Indonesia", "lat": -6.2088, "lng": 106.8456, "capacity": 95000, "current_stock": random.randint(60000, 90000)},
            {"name": "Denso Warehouse Manila", "region": "Philippines", "lat": 14.5995, "lng": 120.9842, "capacity": 75000, "current_stock": random.randint(45000, 70000)},
            {"name": "Denso Warehouse Kuala Lumpur", "region": "Malaysia", "lat": 3.1390, "lng": 101.6869, "capacity": 110000, "current_stock": random.randint(70000, 105000)},
            {"name": "Denso Hub Singapore", "region": "Singapore", "lat": 1.3521, "lng": 103.8198, "capacity": 200000, "current_stock": random.randint(150000, 195000)}
        ]

        sku_insights = {}
        if skus:
            for sku_code in skus:
                sku_obj = next((s for s in DENSO_SKUS if s["code"] == sku_code), None)
                if sku_obj:
                    sku_insights[sku_code] = {
                        "name": sku_obj["name"],
                        "avg_price_usd": round(random.uniform(5.0, 35.0), 2),
                        "demand_trend": random.choice(["rising", "stable", "declining"]),
                        "stock_level": random.choice(["high", "medium", "low"]),
                        "competitor_count": random.randint(3, 12),
                        "market_leader": random.choice([True, False])
                    }

        return jsonify({
            "price_data": price_data,
            "weather_data": weather_data,
            "port_data": port_data,
            "warehouse_data": warehouse_data,
            "sku_insights": sku_insights,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })


@app.get("/api/monitoring")
def api_monitoring():
    """
    Monitoring:
    - drift: mart.data_drift_features
    - rolling: mart.model_metrics_rolling
    - coverage: mart.coverage_by_sku
    - error_hz: mart.error_horizon
    """
    try:
        # ---- Drift ----
        drift_rows = query_all("""
            SELECT feature_name, ks_stat, psi, status, feature_type, source
            FROM mart.data_drift_features
            ORDER BY feature_name;
        """)

        drift = [
            {
                "feature": r["feature_name"],
                "type": r["feature_type"],
                "source": r["source"],
                "ks": float(r["ks_stat"]),
                "psi": float(r["psi"])
            }
            for r in drift_rows
        ]

        # ---- Rolling metrics ----
        roll_rows = query_all("""
            SELECT week, smape, mae
            FROM mart.model_metrics_rolling
            ORDER BY week;
        """)

        rolling = [
            {
                "week": r["week"],
                "sMAPE": float(r["smape"]),
                "MAE": float(r["mae"])
            }
            for r in roll_rows
        ]

        # ---- Coverage ----
        cov_rows = query_all("""
            SELECT p.sku, c.channel, c.coverage_pct
            FROM mart.coverage_by_sku c
            JOIN dim.dim_product p ON p.product_key = c.product_key;
        """)

        coverage = [
            {
                "sku": r["sku"],
                "channel": r["channel"],
                "coverage": float(r["coverage_pct"])
            }
            for r in cov_rows
        ]

        # ---- Error by horizon ----
        err_rows = query_all("""
            SELECT horizon_days, mape
            FROM mart.error_horizon
            ORDER BY horizon_days;
        """)

        error_hz = [
            {
                "horizon": int(r["horizon_days"]),
                "err": float(r["mape"])
            }
            for r in err_rows
        ]

        return jsonify({
            "drift": drift,
            "rolling": rolling,
            "coverage": coverage,
            "error_hz": error_hz
        })

    except Exception as e:
        print(">>> [api_monitoring] DB error, fallback random:", repr(e))

        real_features = [
            {"feature": "pmi", "type": "Economic", "source": "GSO / S&P Global"},
            {"feature": "gdp_growth", "type": "Economic", "source": "GSO"},
            {"feature": "cpi", "type": "Economic", "source": "GSO"},
            {"feature": "gas_price", "type": "Demand", "source": "Ministry of Industry"},
            {"feature": "gtrends_score", "type": "Demand", "source": "Google Trends"},
        ]

        drift = []
        for f in real_features:
            ks = round(random.uniform(0.02, 0.35), 3)
            psi = round(random.uniform(0.01, 0.31), 3)
            drift.append({
                "feature": f["feature"],
                "type": f["type"],
                "source": f["source"],
                "ks": ks,
                "psi": psi
            })

        rolling = [
            {"week": f"W{i}", "sMAPE": round(random.uniform(7, 17), 2), "MAE": round(random.uniform(10, 32), 2)}
            for i in range(1, 9)
        ]

        coverage = [
            {"sku": random.choice([s["code"] for s in DENSO_SKUS]), "channel": random.choice(CHANNELS),
             "coverage": round(random.uniform(72, 98), 1)}
            for _ in range(25)
        ]

        error_hz = [
            {"horizon": h, "err": round(random.uniform(5, 20), 1)}
            for h in [1, 7, 14, 28]
        ]

        return jsonify({
            "drift": drift,
            "rolling": rolling,
            "coverage": coverage,
            "error_hz": error_hz
        })


@app.get("/api/models/registry")
def api_registry():
    """
    Model registry:
    - models: mart.model_registry
    - metrics: mart.model_metrics_over_time
    """
    try:
        model_rows = query_all("""
            SELECT name, version, trained_at, dataset, params, is_champion
            FROM mart.model_registry
            ORDER BY trained_at;
        """)

        models = []
        for r in model_rows:
            models.append({
                "name": r["name"],
                "version": r["version"],
                "trained_at": r["trained_at"].strftime("%Y-%m-%d") if r["trained_at"] else None,
                "dataset": r["dataset"],
                "params": r["params"],
                "is_champion": bool(r["is_champion"])
            })

        metric_rows = query_all("""
            SELECT model_name, version, period, smape, mae
            FROM mart.model_metrics_over_time
            ORDER BY period;
        """)

        metrics = []
        for r in metric_rows:
            metrics.append({
                "name": f"{r['model_name']}@{r['version']}",
                "sMAPE": float(r["smape"]),
                "MAE": float(r["mae"]),
                "Pinball": None,
                "Coverage": None,
                "date": r["period"]
            })

        if not models:
            raise RuntimeError("No rows in mart.model_registry")

        return jsonify({"models": models, "metrics": metrics})

    except Exception as e:
        print(">>> [api_registry] DB error, fallback random:", repr(e))

        models = [
            {"name": "Prophet", "version": "1.3", "trained_at": "2025-10-15", "dataset": "ds2025w42",
             "params": {"seasonality": "auto", "growth": "linear"}},
            {"name": "LGBM", "version": "1.0", "trained_at": "2025-10-18", "dataset": "ds2025w42",
             "params": {"max_depth": 8, "learning_rate": 0.05}},
            {"name": "TFT", "version": "2.2", "trained_at": "2025-10-20", "dataset": "ds2025w43",
             "params": {"hidden": 256, "attention_heads": 4}},
        ]

        metrics = [
            {"name": f"{m['name']}@{m['version']}",
             "sMAPE": round(random.uniform(7, 16), 2),
             "MAE": round(random.uniform(10, 32), 2),
             "Pinball": round(random.uniform(0.05, 0.14), 3),
             "Coverage": round(random.uniform(78, 96), 1),
             "date": "2025-10-22"}
            for m in models
        ]

        return jsonify({"models": models, "metrics": metrics})


@app.post("/api/models/set_champion")
def api_set_champion():
    """
    Cập nhật champion model cho SKU:
    body: { "sku": "K20PR-U", "model": "xgboost_sparkplug", "version": "v1" }
    - insert vào mart.model_champion_per_sku
    """
    body = request.json or {}
    sku_code = body.get("sku")
    model_name = body.get("model")
    version = body.get("version", "v1")

    if not sku_code or not model_name:
        return jsonify({"ok": False, "message": "sku and model are required"}), 400

    try:
        prod_row = query_one("""
            SELECT product_key
            FROM dim.dim_product
            WHERE sku = %s;
        """, (sku_code,))

        if not prod_row:
            return jsonify({"ok": False, "message": f"SKU {sku_code} not found"}), 404

        execute_sql("""
            INSERT INTO mart.model_champion_per_sku (product_key, model_name, version, effective_from)
            VALUES (%s, %s, %s, %s);
        """, (prod_row["product_key"], model_name, version, datetime.today().date()))

        return jsonify({"ok": True, "message": f"Champion set: {sku_code} -> {model_name}@{version}"})

    except Exception as e:
        print(">>> [api_set_champion] DB error:", repr(e))
        return jsonify({"ok": False, "message": "DB error when setting champion"}), 500


# =====================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
