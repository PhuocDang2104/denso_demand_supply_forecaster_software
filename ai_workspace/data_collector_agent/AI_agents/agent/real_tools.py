# C:\Users\Lenovo\AI_LLM_Agent\agent\real_tools.py

import json
from langchain.tools import tool

# THAY ĐỔI: Định nghĩa 3 file data
ARTICLE_DATA_FILE = "market_data.json"
WEATHER_DATA_FILE = "weather_data.json"
VAMA_DATA_FILE = "vama_data.json" # <-- FILE MỚI

@tool
def get_latest_market_intelligence_report() -> str:
    """
    THAY ĐỔI: Chú thích cho AI biết là tool này lấy cả tin tức, thời tiết VÀ VAMA
    Use this single tool to get ALL available raw text content. This includes:
    1. News articles (market data, logistics, etc.)
    2. Weather reports (storm warnings, temperatures).
    3. VAMA sales report (raw text extracted from PDF tables).
    You (the Agent) must read this combined text and extract all relevant information.
    """
    print(f"\n--- TOOL CALLED: get_latest_market_intelligence_report() ---")
    
    combined_content = ""
    
    # --- KHỐI 1: Đọc file tin tức (market_data.json) ---
    try:
        with open(ARTICLE_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data:
            combined_content += "--- START OF NEWS ARTICLES ---\n"
            for i, article in enumerate(data):
                # (code gộp tin tức giữ nguyên)
                combined_content += f"\n--- ARTICLE {i+1} ---\n"
                combined_content += f"TITLE: {article.get('title', 'No Title')}\n"
                combined_content += f"CONTENT:\n{article.get('raw_text_content', 'No Content')}\n"
            combined_content += "--- END OF NEWS ARTICLES ---\n"
        else:
            combined_content += "--- No news articles found. ---\n"
            
    except FileNotFoundError:
        combined_content += f"--- ERROR: News data file not found ({ARTICLE_DATA_FILE}). ---\n"
    except Exception as e:
        combined_content += f"--- ERROR reading news data: {e} ---\n"

    # --- KHỐI 2: Đọc file thời tiết (weather_data.json) ---
    try:
        with open(WEATHER_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data:
            combined_content += "\n--- START OF WEATHER REPORTS ---\n"
            weather_text = json.dumps(data, indent=2, ensure_ascii=False)
            combined_content += weather_text
            combined_content += "\n--- END OF WEATHER REPORTS ---\n"
        else:
            combined_content += "--- No weather reports found. ---\n"

    except FileNotFoundError:
        combined_content += f"--- ERROR: Weather data file not found ({WEATHER_DATA_FILE}). ---\n"
    except Exception as e:
        combined_content += f"--- ERROR reading weather data: {e} ---\n"

    # --- KHỐI 3 (MỚI): Đọc file VAMA (vama_data.json) ---
    try:
        with open(VAMA_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data and data.get('extracted_text'):
            combined_content += "\n--- START OF VAMA SALES REPORT (Raw PDF Text) ---\n"
            combined_content += f"REPORT TITLE: {data.get('report_title')}\n"
            combined_content += data['extracted_text']
            combined_content += "\n--- END OF VAMA SALES REPORT ---\n"
        else:
            combined_content += "--- No VAMA sales data found. ---\n"

    except FileNotFoundError:
        combined_content += f"--- ERROR: VAMA data file not found ({VAMA_DATA_FILE}). ---\n"
    except Exception as e:
        combined_content += f"--- ERROR reading VAMA data: {e} ---\n"

    return combined_content

# Cập nhật danh sách tool (vẫn chỉ 1 tool)
all_tools = [get_latest_market_intelligence_report]