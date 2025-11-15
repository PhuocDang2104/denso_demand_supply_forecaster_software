import random
from datetime import datetime

from flask import request, jsonify

from ..db import query_all
from ..core.constants import DENSO_SKUS, REGIONS


def register(bp):
    @bp.get("/market/intelligence")
    def api_market_intelligence():
        """
        Market Intelligence.
        """
        skus = request.args.get("skus", "").split(",") if request.args.get("skus") else []

        port_geo = {
            "Cat Lai": (10.7769, 106.7009),
            "Laem Chabang": (13.09, 100.89),
            "Tanjung Priok": (-6.104, 106.88),
            "Manila": (14.5995, 120.9842),
            "Port Klang": (3.1390, 101.6869),
            "Singapore Port": (1.3521, 103.8198),
        }
        region_geo = {
            "Vietnam": (21.0285, 105.8542),
            "Thailand": (13.7563, 100.5018),
            "Indonesia": (-6.2088, 106.8456),
            "Philippines": (14.5995, 120.9842),
            "Malaysia": (3.1390, 101.6869),
            "Singapore": (1.3521, 103.8198),
        }

        try:
            price_rows = query_all("""
                SELECT region, sku, avg_price, competitor_price, price_trend, market_share
                FROM mart.market_price_region
                WHERE as_of_date = (
                    SELECT MAX(as_of_date) FROM mart.market_price_region AS sub
                    WHERE sub.region = mart.market_price_region.region
                );
            """)

            price_data = {}
            for r in price_rows:
                region = r["region"]
                price_data[region] = {
                    "avg_price": float(r["avg_price"]),
                    "competitor_price": float(r["competitor_price"]),
                    "price_trend": r["price_trend"],
                    "market_share": float(r["market_share"])
                }

            if not price_data:
                raise RuntimeError("No rows in mart.market_price_region")

            weather_rows = query_all("""
                SELECT region, condition, temperature, humidity, impact_score
                FROM mart.market_weather_region
                WHERE as_of_date = (
                    SELECT MAX(as_of_date) FROM mart.market_weather_region AS sub
                    WHERE sub.region = mart.market_weather_region.region
                );
            """)

            weather_data = {}
            for r in weather_rows:
                weather_data[r["region"]] = {
                    "condition": r["condition"],
                    "temperature": float(r["temperature"]),
                    "humidity": float(r["humidity"]),
                    "impact_score": float(r["impact_score"])
                }

            port_rows = query_all("""
                SELECT name, region, congestion_pct
                FROM mart.port_congestion
                WHERE as_of_date = (SELECT MAX(as_of_date) FROM mart.port_congestion);
            """)

            port_data = []
            for r in port_rows:
                lat, lng = port_geo.get(r["name"], region_geo.get(r["region"], (0.0, 0.0)))
                port_data.append({
                    "name": r["name"],
                    "region": r["region"],
                    "lat": lat,
                    "lng": lng,
                    "congestion": float(r["congestion_pct"]),
                    "delay_days": random.randint(0, 7)
                })

            wh_rows = query_all("""
                SELECT region, capacity, current_stock
                FROM mart.warehouse_status
                WHERE as_of_date = (SELECT MAX(as_of_date) FROM mart.warehouse_status);
            """)

            warehouse_data = []
            for r in wh_rows:
                lat, lng = region_geo.get(r["region"], (0.0, 0.0))
                warehouse_data.append({
                    "name": f"Denso Warehouse {r['region']}",
                    "region": r["region"],
                    "lat": lat,
                    "lng": lng,
                    "capacity": float(r["capacity"]),
                    "current_stock": float(r["current_stock"])
                })

            sku_insights = {}
            if skus:
                for sku_code in skus:
                    sku_obj = next((s for s in DENSO_SKUS if s["code"] == sku_code), None)
                    if sku_obj:
                        sku_insights[sku_code] = {
                            "name": sku_obj["name"],
                            "avg_price_usd": round(random.uniform(5.0, 35.0), 2),
                            "demand_trend": random.choice(["rising", "stable", "declining"]),
                            "stock_level": random.choice(["high", "medium", "low"]),
                            "competitor_count": random.randint(3, 12),
                            "market_leader": random.choice([True, False])
                        }

            return jsonify({
                "price_data": price_data,
                "weather_data": weather_data,
                "port_data": port_data,
                "warehouse_data": warehouse_data,
                "sku_insights": sku_insights,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        except Exception as e:
            print(">>> [api_market_intelligence] DB error, fallback random:", repr(e))

            price_data = {}
            for region in REGIONS:
                price_data[region] = {
                    "avg_price": round(random.uniform(8.5, 25.0), 2),
                    "competitor_price": round(random.uniform(9.0, 26.0), 2),
                    "price_trend": random.choice(["up", "down", "stable"]),
                    "market_share": round(random.uniform(15, 45), 1)
                }

            weather_conditions = ["sunny", "rainy", "cloudy", "stormy", "hazy"]
            weather_data = {}
            for region in REGIONS:
                weather_data[region] = {
                    "condition": random.choice(weather_conditions),
                    "temperature": round(random.uniform(22, 36), 1),
                    "humidity": round(random.uniform(60, 95), 0),
                    "impact_score": round(random.uniform(0.6, 1.4), 2)
                }

            port_data = [
                {"name": "Port of Ho Chi Minh", "region": "Vietnam", "lat": 10.7769, "lng": 106.7009, "congestion": random.randint(20, 85), "delay_days": random.randint(0, 5)},
                {"name": "Port of Bangkok", "region": "Thailand", "lat": 13.7563, "lng": 100.5018, "congestion": random.randint(15, 75), "delay_days": random.randint(0, 4)},
                {"name": "Port of Jakarta", "region": "Indonesia", "lat": -6.2088, "lng": 106.8456, "congestion": random.randint(30, 90), "delay_days": random.randint(1, 7)},
                {"name": "Port of Manila", "region": "Philippines", "lat": 14.5995, "lng": 120.9842, "congestion": random.randint(25, 80), "delay_days": random.randint(0, 6)},
                {"name": "Port Klang", "region": "Malaysia", "lat": 3.1390, "lng": 101.6869, "congestion": random.randint(10, 60), "delay_days": random.randint(0, 3)},
                {"name": "Port of Singapore", "region": "Singapore", "lat": 1.3521, "lng": 103.8198, "congestion": random.randint(5, 45), "delay_days": random.randint(0, 2)}
            ]

            warehouse_data = [
                {"name": "Denso Warehouse Hanoi", "region": "Vietnam", "lat": 21.0285, "lng": 105.8542, "capacity": 85000, "current_stock": random.randint(50000, 80000)},
                {"name": "Denso Warehouse Ho Chi Minh", "region": "Vietnam", "lat": 10.8231, "lng": 106.6297, "capacity": 120000, "current_stock": random.randint(80000, 115000)},
                {"name": "Denso Warehouse Bangkok", "region": "Thailand", "lat": 13.7563, "lng": 100.5018, "capacity": 150000, "current_stock": random.randint(100000, 145000)},
                {"name": "Denso Warehouse Jakarta", "region": "Indonesia", "lat": -6.2088, "lng": 106.8456, "capacity": 95000, "current_stock": random.randint(60000, 90000)},
                {"name": "Denso Warehouse Manila", "region": "Philippines", "lat": 14.5995, "lng": 120.9842, "capacity": 75000, "current_stock": random.randint(45000, 70000)},
                {"name": "Denso Warehouse Kuala Lumpur", "region": "Malaysia", "lat": 3.1390, "lng": 101.6869, "capacity": 110000, "current_stock": random.randint(70000, 105000)},
                {"name": "Denso Hub Singapore", "region": "Singapore", "lat": 1.3521, "lng": 103.8198, "capacity": 200000, "current_stock": random.randint(150000, 195000)}
            ]

            sku_insights = {}
            if skus:
                for sku_code in skus:
                    sku_obj = next((s for s in DENSO_SKUS if s["code"] == sku_code), None)
                    if sku_obj:
                        sku_insights[sku_code] = {
                            "name": sku_obj["name"],
                            "avg_price_usd": round(random.uniform(5.0, 35.0), 2),
                            "demand_trend": random.choice(["rising", "stable", "declining"]),
                            "stock_level": random.choice(["high", "medium", "low"]),
                            "competitor_count": random.randint(3, 12),
                            "market_leader": random.choice([True, False])
                        }

            return jsonify({
                "price_data": price_data,
                "weather_data": weather_data,
                "port_data": port_data,
                "warehouse_data": warehouse_data,
                "sku_insights": sku_insights,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    @bp.get("/market/news_agent")
    def api_market_news_agent():
        """
        Trả về:
        - storage: các bản ghi đã scrape (sheet-like)
        - summary: báo cáo tổng hợp tiếng Việt từ agent
        """
        try:
            rows = query_all("""
                SELECT
                    title,
                    category,
                    region,
                    published_at,
                    source,
                    url,
                    headline,
                    snippet
                FROM mart.market_news_storage
                ORDER BY published_at DESC NULLS LAST, created_at DESC
                LIMIT 50;
            """)

            storage = []
            for r in rows:
                storage.append({
                    "title": r["title"],
                    "category": r.get("category") if isinstance(r, dict) else r["category"],
                    "region": r.get("region") if isinstance(r, dict) else r["region"],
                    "published_at": (
                        r["published_at"].isoformat() if r.get("published_at") else None
                    ) if isinstance(r, dict) else (
                        r["published_at"].isoformat() if r["published_at"] else None
                    ),
                    "source": r.get("source") if isinstance(r, dict) else r["source"],
                    "url": r.get("url") if isinstance(r, dict) else r["url"],
                    "headline": r.get("headline") if isinstance(r, dict) else r["headline"],
                    "snippet": r.get("snippet") if isinstance(r, dict) else r["snippet"],
                })

            # Lấy 1 summary mới nhất (summary_text + conclusion)
            summary_rows = query_all("""
                SELECT summary_text, conclusion
                FROM mart.market_news_summary
                ORDER BY as_of_date DESC, created_at DESC
                LIMIT 1;
            """)

            if summary_rows:
                summary_text = summary_rows[0]["summary_text"] or ""
                conclusion_text = summary_rows[0]["conclusion"] or ""
            else:
                summary_text = ""
                conclusion_text = ""

            return jsonify({
                "storage": storage,
                "summary": summary_text,
                "conclusion": conclusion_text,
            })

        except Exception as e:
            print(">>> [api_market_news_agent] error:", repr(e))
            # Fallback demo
            demo_full = """BÁO CÁO PHÂN TÍCH RỦI RO (OUTPUT BẰNG TIẾNG VIỆT):
        # BÁO CÁO RỦI RO CHUỖI CUNG ỨNG TẠI VIỆT NAM

        ## 1. Tin tức về Thị trường Bugi/Phụ tùng Ô tô và Ảnh hưởng đến Logistics:
        Không có thông tin cụ thể về thị trường bugi/phụ tùng ô tô gây ảnh hưởng đến logistics trong dữ liệu thu thập.

        ## 2. Tin tức về Gián đoạn Chuỗi Cung Ứng/Logistics do Thiên Tai:
        ### **CẢNH BÁO (WARNING)**
        - Miền Trung Việt Nam đang bước vào đợt mưa rất lớn từ ngày 15-17/11, có nơi mưa rất to và dông. Dự báo mưa lớn có khả năng kéo dài từ đêm 17-21/11. Nguy cơ lũ quét, sạt lở đất, ngập úng các khu vực lúa, hoa màu, và tuyến đường giao thông tại vùng núi và trũng thấp.
        - Cảnh báo cấp độ rủi ro thiên tai do mưa lớn: Cấp 2.

        ## 3. Cảnh báo Thiên Tai - Bão Sắp Tới:
        Không có thông tin cụ thể về cảnh báo bão sắp tới trong dữ liệu thu thập.

        ## 4. Tổng Kết Rủi Ro Lớn Nhất:
        - **Cảnh báo lớn nhất:** Miền Trung Việt Nam đang đối diện với đợt mưa rất lớn, có nguy cơ lũ quét, sạt lở đất, và ngập úng, gây ảnh hưởng đến chuỗi cung ứng và logistics trong khu vực.
        - **Cần theo dõi:** Phải chú ý đến tình hình thời tiết và chuẩn bị phương án phòng chống, hạn chế thiệt hại do mưa lớn và thiên tai.

        ### **KẾT LUẬN (CONCLUSION)**
        - Rủi ro lớn nhất trong thời gian tới là đợt mưa lớn ở Miền Trung Việt Nam, có khả năng gây lũ quét, sạt lở đất, và ngập úng, ảnh hưởng đến chuỗi cung ứng và logistics. Cần theo dõi sát sao và chuẩn bị phương án ứng phó kịp thời.
        """

            marker = "### **KẾT LUẬN (CONCLUSION)**"
            if marker in demo_full:
                idx = demo_full.index(marker)
                demo_summary = demo_full[:idx].rstrip()
                demo_conclusion = demo_full[idx:].lstrip()
            else:
                demo_summary = demo_full
                demo_conclusion = ""

            return jsonify({
                "storage": [],
                "summary": demo_summary,
                "conclusion": demo_conclusion,
            })