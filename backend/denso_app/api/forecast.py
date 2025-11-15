import random
from datetime import datetime, timedelta

from flask import request, jsonify

from ..db import query_all, query_one
from ..core.constants import DENSO_SKUS


def register(bp):
    @bp.get("/forecast/sku")
    def api_forecast_sku():
        """
        Chi tiết forecast cho từng SKU.
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

    @bp.get("/forecast/backtest")
    def api_backtest():
        """
        Leaderboard backtest.
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
