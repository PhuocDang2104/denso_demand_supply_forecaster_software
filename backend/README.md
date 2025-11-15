# DENSO Forecast Suite – Backend

Python/Flask backend cho **DENSO Forecast Suite v3**:  
- Dashboard KPI & fan chart theo SKU / region / channel  
- Forecast chi tiết + Prophet components + SHAP  
- Scenario planning (what-if), campaign impact, inventory policy  
- Market intelligence (price, weather, port, warehouse)  
- Monitoring (data/model drift, coverage, rolling metrics)  
- Model registry & champion selection per SKU  

---

## 1. Tech stack

- **Python**: 3.10+ (khuyến nghị 3.11)
- **Framework**: Flask
- **WSGI server**: Gunicorn (cho production)
- **Database**: PostgreSQL (schema `dim`, `feature`, `mart`)
- **Driver**: `psycopg2` / `psycopg2-binary`

---

## 2. Cấu trúc thư mục

```text
backend/
  run.py                     # WSGI entrypoint: app = create_app()
  Dockerfile                 # Docker build cho backend
  README.md                  # Tài liệu này

  denso_app/
    __init__.py              # create_app(), register blueprints, index route
    config.py                # DB_CONFIG đọc từ biến môi trường
    db.py                    # query_all, query_one, execute_sql (psycopg2)

    core/
      __init__.py
      constants.py           # ROLES, DENSO_SKUS, REGIONS, CHANNELS

    api/
      __init__.py            # Đăng ký routes theo từng nhóm A/B/C/D
      dashboard.py           # A. Dashboard APIs
      forecast.py            # B. Forecast APIs
      scenario.py            # C1. Scenario (what-if) APIs
      campaign.py            # C2. Campaign impact APIs
      inventory.py           # C3. Inventory recommendation APIs
      data_api.py            # D1. Exogenous features APIs
      market_intel.py        # D2. Market intelligence (price/weather/port/WH)
      monitoring.py          # D3. Monitoring APIs
      models_registry.py     # D4. Model registry & champion APIs

    templates/
      index.html             # Frontend HTML 

    static/
      css/
        style.css            # CSS chính 
      js/
        main.js              # JS chính 
