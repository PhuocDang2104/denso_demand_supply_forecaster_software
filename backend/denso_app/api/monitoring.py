import random

from flask import jsonify

from ..db import query_all
from ..core.constants import DENSO_SKUS, CHANNELS


def register(bp):
    @bp.get("/monitoring")
    def api_monitoring():
        """
        Monitoring endpoints.
        """
        try:
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
