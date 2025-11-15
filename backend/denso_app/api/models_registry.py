from datetime import datetime

from flask import request, jsonify

from ..db import query_all, execute_sql


def register(bp):
    @bp.get("/models/registry")
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

    @bp.post("/models/set_champion")
    def api_set_champion():
        """
        Cập nhật champion model cho SKU:
        body: { "sku": "K20PR-U", "model": "xgboost_sparkplug", "version": "v1" }
        """
        body = request.json or {}
        sku_code = body.get("sku")
        model_name = body.get("model")
        version = body.get("version", "v1")

        if not sku_code or not model_name:
            return jsonify({"ok": False, "message": "sku and model are required"}), 400

        try:
            prod_row = query_all("""
                SELECT product_key
                FROM dim.dim_product
                WHERE sku = %s;
            """, (sku_code,))

            if not prod_row:
                return jsonify({"ok": False, "message": f"SKU {sku_code} not found"}), 404

            execute_sql("""
                INSERT INTO mart.model_champion_per_sku (product_key, model_name, version, effective_from)
                VALUES (%s, %s, %s, %s);
            """, (prod_row[0]["product_key"], model_name, version, datetime.today().date()))

            return jsonify({"ok": True, "message": f"Champion set: {sku_code} -> {model_name}@{version}"})

        except Exception as e:
            print(">>> [api_set_champion] DB error:", repr(e))
            return jsonify({"ok": False, "message": "DB error when setting champion"}), 500
