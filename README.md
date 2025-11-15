# DENSO BYTECO – Forecasting & Market Intelligence Suite

Hệ thống dự báo nhu cầu – rủi ro cung ứng – market intelligence – news agent – logistics dashboard cho DENSO APAC.

Toàn bộ kiến trúc gồm:  
1) Backend API (Flask)  
2) AI Workspace (Forecasting + Data Collector Agent)  
3) PostgreSQL Data Lake & Mart Layer qua Docker  
<br>

---
## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN
---



```text
DENSO_BYTECO/
├─ docker-compose.yml
├─ requirements.txt
├─ .env.example                 # biến môi trường (DB_HOST, OPENAI_KEY, ...)
├─ README.md
├─ schema.sql
├─ seed_data.sql
├─ seed_alter_v3.sql
│
├─ backend/                     # Flask + API
│  ├─ run.py                    # điểm vào dev: from denso_app import create_app
│  └─ denso_app/
│     ├─ __init__.py            # create_app(), register_blueprints()
│     ├─ config.py              # class BaseConfig, DevConfig, ProdConfig
│     ├─ db.py                  # hàm query_all/query_one/execute_sql dùng lại
│     ├─ core/                  # constant, helper chung
│     │  ├─ __init__.py
│     │  └─ constants.py        # DENSO_SKUS, REGIONS, CHANNELS,...
│     │  
│     ├─ api/                   # tách các route hiện tại trong app.py thành module
│     │  ├─ __init__.py         # register Blueprint
│     │  ├─ dashboard.py        # /api/dashboard
│     │  ├─ forecast.py         # /api/forecast/* (sku, backtest)
│     │  ├─ scenario.py         # /api/scenario/whatif
│     │  ├─ campaign.py         # /api/campaign/impact
│     │  ├─ inventory.py        # /api/inventory/recommend
│     │  ├─ data.py             # /api/data/exogenous
│     │  ├─ market_intel.py     # /api/market/intelligence + news_agent
│     │  ├─ monitoring.py       # /api/monitoring
│     │  └─ models_registry.py  # /api/models/*
│     ├─ services/              # logic nghiệp vụ phức tạp tách khỏi layer API
│     │  ├─ __init__.py
│     │  ├─ forecast_service.py 
│     │  ├─ scenario_service.py
│     │  ├─ inventory_service.py
│     │  └─ market_intel_service.py
│     ├─ templates/
│     │  └─ index.html
│     └─ static/
│        ├─ css/
│        │  └─ style.css
│        └─ js/
│           └─ main.js
│
├─ ai_workspace/                          # toàn bộ phần ML + AI Agent (Bước 1–3)
│  ├─ prophet_forecaster/       # AI của Bảo - Prophet Forecaster
│  │  ├─ data/
│  │  │  ├─ raw/                # dữ liệu thô trước xử lý
│  │  │  │  ├─ supply_semiconductor_raw.csv
│  │  │  │  └─ demand_ev_inverter_raw.csv
│  │  │  └─ processed/          # dữ liệu đã clean để train / infer
│  │  │     ├─ supply_semiconductor.csv
│  │  │     └─ demand_ev_inverter.csv
│  │  ├─ models/                # file model sau khi train (.pkl, .joblib, ...)
│  │  │  ├─ xgb_supply_risk.pkl
│  │  │  └─ prophet_demand.pkl
│  │  ├─ pipelines/             # script train + infer + ghi forecast vào DB
│  │  │  ├─ train_supply_risk.py
│  │  │  ├─ train_demand_forecast.py
│  │  │  └─ generate_forecasts.py   # ghi kết quả vào schema mart.*
│  │  └─ notebooks/             # Jupyter thử nghiệm (không dùng production)
│  │
│  └─ data_collector_agent/     # AI của Khiêm - data scraping --> storage --> GPT 3.5
│     ├─ AI_LLM_Agent/
│     │  ├─ agent/
│     │  │  ├─ __init__.py
│     │  │  ├─ main_agent.py    # orchestration: gọi collectors + tools + LLM
│     │  │  ├─ prompts.py       # hệ thống prompt / template báo cáo
│     │  │  └─ real_tools.py    # hàm gọi DB, market_intel API, ghi vào mart.*
│     │  ├─ collectors/         # các collector chuyên biệt
│     │  │  ├─ article_collector.py   # crawl báo / tin supply chain, logistics
│     │  │  ├─ vama_collector.py      # lấy dữ liệu VAMA / thị trường ô tô VN
│     │  │  └─ weather_collector.py   # lấy dữ liệu thời tiết / cảnh báo thiên tai
│     │  └─ reports/            # output JSON/text trước khi đẩy về DB
│     │     ├─ market_data.json
│     │     ├─ vama_data.json
│     │     └─ ...
│     ├─ run_demo.py            # script chạy agent LLM gpt để ra conclusion
│     ├─ scheduler.py           # chạy scraping để xuất storage
│     └─ .env                   # env riêng cho agent (NEWS_API_KEY, OPENAI_API_KEY,...)
│
├─ infra/                       # hạ tầng triển khai
│  ├─ alembic/                  # nếu sau này dùng migration
│  ├─ k8s/                      # yaml nếu deploy k8s
│  └─ nginx/                    # config nginx reverse proxy (optional)
│
└─ tests/
   ├─ __init__.py
   ├─ test_api_dashboard.py
   ├─ test_inventory.py
   └─ test_ml_pipelines.py
```


<br>

---
## 🗄 1. HƯỚNG DẪN SỬ DỤNG POSTGRESQL QUA DOCKER
---

SYSTEM: PostgreSQL 16 + pgAdmin 4 (UI)

------------------------------------
1.1 Khởi động database
------------------------------------
Tại thư mục dự án:
```
docker compose up -d
```
Kiểm tra:
```
docker ps
```
------------------------------------
1.2 Truy cập PostgreSQL
------------------------------------

Cách 1 – từ host:
```

psql -h localhost -p 5432 -U denso -d denso_forecast
# password: admin
```
Cách 2 – từ trong terminal vscode:
```
docker exec -it denso_db_local psql -U denso -d denso_forecast
```
------------------------------------
1.3 Nạp schema + seed data
------------------------------------
```
psql -h localhost -p 5432 -U denso -d denso_forecast -f schema.sql
psql -h localhost -p 5432 -U denso -d denso_forecast -f seed_data.sql
psql -h localhost -p 5432 -U denso -d denso_forecast -f seed_alter_v3.sql
```
------------------------------------
1.4 Truy cập pgAdmin (GUI)
------------------------------------

Tải về pgAdmin4 về

Thêm server mới:
- Name: denso_local
- Host: db
- Port: 5432
- Database: denso_forecast
- User: denso
- Pass: admin

------------------------------------
1.5 Config Flask kết nối Postgres
------------------------------------

Trong file .env:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=denso_forecast
DB_USER=denso
DB_PASSWORD=admin
```
Nếu backend chạy trong container → DB_HOST=db.

<br>

---
## 2. LUỒNG DỮ LIỆU HỆ THỐNG
---

Collector Agent  
    → mart.market_news_storage  
    → mart.market_news_summary  
    → Backend API  
    → Dashboard (Market Intelligence News)

Prophet / XGBoost Pipeline  
    → generate_forecasts.py  
    → mart.demand_forecast_weekly  
    → /api/forecast → UI (SKU Forecast)

Public Data (NOAA/IEA/VAMA/Google Trends)  
    → Collector Agent scheduler  
    → Storage mart.*

<br>

---
## 3. KẾT LUẬN
---

- Cấu trúc project theo chuẩn enterprise.
- Backend + Service Layer rõ ràng.
- AI Workspace gồm Forecast engine + Data Collector Agent.
- PostgreSQL làm nguồn dữ liệu trung tâm.
- Docker-compose giúp setup DB/pgAdmin trong 10 giây.
- Dễ mở rộng sang cloud, CI/CD, Kubernetes.