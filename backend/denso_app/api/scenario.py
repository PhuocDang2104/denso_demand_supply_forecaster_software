import random
from datetime import datetime

from flask import request, jsonify

from ..db import query_one
from ..core.constants import DENSO_SKUS


def register(bp):
    @bp.post("/scenario/whatif")
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
