import random
from datetime import datetime, timedelta

from flask import request, jsonify

from ..db import query_all, query_one
from ..core.constants import DENSO_SKUS, CHANNELS


def register(bp):
    @bp.get("/dashboard")
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
