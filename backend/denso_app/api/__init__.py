from flask import Blueprint, render_template, request

from ..core.constants import ROLES


def register_blueprints(app):
    # =========================
    # 1. WEB (HTML) BLUEPRINT
    # =========================
    web_bp = Blueprint("web", __name__)

    @web_bp.route("/")
    def index():
        role = request.args.get("role", "viewer").lower()
        if role not in ROLES:
            role = "viewer"
        return render_template("index.html", role=role, roles=ROLES)

    # =========================
    # 2. API BLUEPRINT (JSON)
    # =========================
    # Tất cả API đều sẽ có prefix "/api" khi register ở dưới.
    api_bp = Blueprint("api", __name__)

    # Import các module API theo domain
    from . import (
        dashboard,
        forecast,
        scenario,
        campaign,
        inventory,
        data_api,
        market_intel,
        monitoring,
        models_registry,
    )

    # ============= A. DASHBOARD APIs =============
    dashboard.register(api_bp)

    # ============= B. FORECAST APIs ==============
    forecast.register(api_bp)

    # ============= C. SCENARIO / CAMPAIGN / INVENTORY APIs ============
    scenario.register(api_bp)
    campaign.register(api_bp)
    inventory.register(api_bp)

    # ============= D. DATA / MONITORING / MODEL APIs ==================
    data_api.register(api_bp)
    market_intel.register(api_bp)
    monitoring.register(api_bp)
    models_registry.register(api_bp)

    # Đăng ký vào app chính
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
