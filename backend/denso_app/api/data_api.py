import random
from datetime import datetime, timedelta

from flask import jsonify

from ..db import query_all


def register(bp):
    @bp.get("/data/exogenous")
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
