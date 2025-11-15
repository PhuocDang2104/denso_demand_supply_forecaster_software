# C:\Users\Lenovo\AI_LLM_Agent\collectors\weather_collector.py

import os
import json
import datetime
from dotenv import load_dotenv
from pyowm.owm import OWM



load_dotenv()
DATA_FILE_PATH = "weather_data.json" # File data thời tiết mới
CITIES_TO_MONITOR = ['Hanoi', 'Ho Chi Minh City', 'Danang', 'Haiphong'] 

def collect_and_save_weather():
    """
    Sử dụng OWM One Call API để lấy thời tiết HIỆN TẠI
    và DỰ BÁO 7 NGÀY TỚI, tập trung vào cảnh báo bão.
    """
    print(f"\n--- Running OWM Weather Collector (Forecast Mode) @ {datetime.datetime.now()} ---")
    
    try:
        api_key = os.getenv("OWM_API_KEY")
        if not api_key:
            print("ERROR: OWM_API_KEY not found in .env file.")
            return

        owm = OWM(api_key)
        mgr = owm.weather_manager()
        geocoding_mgr = owm.geocoding_manager() 

        weather_reports = []
        
        for city in CITIES_TO_MONITOR:
            print(f"  -> Fetching forecast for {city}, VN")
            
            # 1. Lấy tọa độ (lat/lon) từ tên thành phố (Bắt buộc cho One Call API)
            try:
                location = geocoding_mgr.geocode(f"{city},VN")[0] # Lấy kết quả đầu tiên
                lat, lon = location.lat, location.lon
            except Exception as geo_e:
                print(f"  [Error] Could not find geocode for {city}: {geo_e}")
                continue # Bỏ qua thành phố này nếu không tìm thấy

            # 2. Gọi One Call API (lấy hiện tại, hàng giờ, 7 ngày)
            # 'exclude='minutely,hourly'' -> Bỏ qua dự báo từng phút và từng giờ
            one_call = mgr.one_call(lat=lat, lon=lon, exclude='minutely,hourly')

            # 3. Xử lý DỰ BÁO 7 NGÀY TỚI (Nơi chúng ta tìm bão)
            forecasts = []
            storm_detected = False
            
            if one_call.forecast_daily:
                for daily_weather in one_call.forecast_daily:
                    forecast_date = daily_weather.reference_time('date')
                    status = daily_weather.detailed_status.lower()
                    temp_max = daily_weather.temperature('celsius')['max']
                    
                    # Kiểm tra các từ khóa bão (tiếng Anh)
                    storm_keywords = ['storm', 'thunderstorm', 'cyclone', 'typhoon', 'hurricane']
                    is_storm = any(keyword in status for keyword in storm_keywords)
                    
                    if is_storm:
                        storm_detected = True # Đánh dấu có bão trong 7 ngày tới
                        print(f"  [!!!] UPCOMING STORM WARNING for {city} on {forecast_date.strftime('%Y-%m-%d')}: {status}")

                    forecasts.append({
                        "date": forecast_date.strftime('%Y-%m-%d'),
                        "max_temp": f"{temp_max}°C",
                        "condition": status,
                        "is_storm": is_storm
                    })

            # 4. Lấy thời tiết HIỆN TẠI (từ cùng lệnh gọi API)
            current_temp = one_call.current.temperature('celsius')['temp']
            current_status = one_call.current.detailed_status.lower()

            # 5. Gộp thành 1 báo cáo cho thành phố này
            report = {
                "city": city,
                "current_temp": f"{current_temp}°C",
                "current_condition": current_status,
                "7_day_storm_warning": storm_detected,
                "daily_forecast": forecasts # Thêm dự báo chi tiết
            }
            weather_reports.append(report)

        # Lưu vào file JSON thời tiết
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(weather_reports, f, ensure_ascii=False, indent=4)
            
        print(f"SUCCESS: Saved {len(weather_reports)} full weather reports (current + 7-day forecast) to {DATA_FILE_PATH}")

    except Exception as e:
        print(f"ERROR during weather data collection: {e}")

if __name__ == "__main__":
    collect_and_save_weather()