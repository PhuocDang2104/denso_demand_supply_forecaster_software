from flask import request, jsonify


def register(bp):
    @bp.post("/inventory/recommend")
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
