
# backend/jobs/fetch_weather.py

import os
import requests
from datetime import date

from ..db import execute_sql

REGION_COORDS = {
    "Vietnam": (21.0285, 105.8542),      # Hanoi
    "Thailand": (13.7563, 100.5018),     # Bangkok
    "Indonesia": (-6.2088, 106.8456),    # Jakarta
    "Philippines": (14.5995, 120.9842),  # Manila
    "Malaysia": (3.1390, 101.6869),      # Kuala Lumpur
    "Singapore": (1.3521, 103.8198),     # Singapore
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def map_weather_code_to_condition(code: int) -> str:
    """
    Map weather_code của Open-Meteo sang condition string đơn giản
    để khớp với UI hiện tại: sunny / rainy / cloudy / stormy / hazy
    """
    # code list: https://open-meteo.com/en/docs
    if code in (0, 1):
        return "sunny"
    if code in (2, 3, 45, 48):
        return "cloudy"
    if code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return "rainy"
    if code in (71, 73, 75, 95, 96, 99):
        return "stormy"
    return "hazy"


def compute_impact_score(condition: str, temp: float, humidity: float) -> float:
    """
    Dummy logic: bạn chỉnh theo business:
    - sunny, nhiệt độ vừa phải → >1 (khuyến khích nhu cầu)
    - stormy / rainy nặng → <1 (giảm nhu cầu)
    """
    base = 1.0

    if condition == "sunny":
        base += 0.15
    elif condition == "cloudy":
        base += 0.05
    elif condition == "rainy":
        base -= 0.15
    elif condition == "stormy":
        base -= 0.25

    # Ví dụ humidity quá cao cũng giảm
    if humidity > 85:
        base -= 0.05

    return round(max(0.5, min(1.5, base)), 2)


def fetch_weather_for_region(region: str, lat: float, lon: float):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "timezone": "Asia/Bangkok",  # timezone khu vực
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    current = data.get("current", {})
    temp = float(current.get("temperature_2m"))
    humidity = float(current.get("relative_humidity_2m"))
    weather_code = int(current.get("weather_code"))

    condition = map_weather_code_to_condition(weather_code)
    impact_score = compute_impact_score(condition, temp, humidity)

    return condition, temp, humidity, impact_score


def upsert_weather_row(region, condition, temp, humidity, impact_score, as_of):
    sql = """
        INSERT INTO mart.market_weather_region
            (region, condition, temperature, humidity, impact_score, as_of_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (region) DO UPDATE
        SET condition   = EXCLUDED.condition,
            temperature = EXCLUDED.temperature,
            humidity    = EXCLUDED.humidity,
            impact_score= EXCLUDED.impact_score,
            as_of_date  = EXCLUDED.as_of_date;
    """
    execute_sql(sql, (region, condition, temp, humidity, impact_score, as_of))


def main():
    today = date.today()

    for region, (lat, lon) in REGION_COORDS.items():
        try:
            condition, temp, humidity, impact = fetch_weather_for_region(region, lat, lon)
            print(f"[{region}] {condition}, {temp}°C, {humidity}%, impact={impact}")
            upsert_weather_row(region, condition, temp, humidity, impact, today)
        except Exception as e:
            print(f"Error fetching weather for {region}: {e}")


if __name__ == "__main__":
    main()
