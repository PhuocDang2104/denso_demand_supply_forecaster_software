# C:\Users\Lenovo\AI_LLM_Agent\scheduler.py

from apscheduler.schedulers.blocking import BlockingScheduler
from collectors.article_collector import collect_and_save_articles
from collectors.weather_collector import collect_and_save_weather
from collectors.vama_collector import scrape_and_process_vama # <-- IMPORT MỚI

import datetime

scheduler = BlockingScheduler(timezone="Asia/Ho_Chi_Minh")

def combined_collection_job():
    """
    Chạy TẤT CẢ các job thu thập dữ liệu
    """
    print("------------------------------------------------------------------")
    print(f"RUNNING COMBINED JOB @ {datetime.datetime.now()}")
    
    # 1. Chạy job thu thập tin tức
    try:
        collect_and_save_articles()
    except Exception as e:
        print(f"[Scheduler Error] Article collector failed: {e}")
    
    # 2. Chạy job thu thập thời tiết
    try:
        collect_and_save_weather()
    except Exception as e:
        print(f"[Scheduler Error] Weather collector failed: {e}")
        
    # 3. CHẠY JOB VAMA (MỚI)
    try:
        scrape_and_process_vama()
    except Exception as e:
        print(f"[Scheduler Error] VAMA collector failed: {e}")
    
    print("------------------------------------------------------------------")

print("--- Starting Combined Collection Scheduler ---")
print("The collection job is scheduled to run every 2 hours.")
print("Press Ctrl+C to exit.")

scheduler.add_job(
    combined_collection_job, # <-- THAY ĐỔI: Gọi hàm tổng hợp
    'interval', 
    hours=24,
    id='combined_collector_job',
    next_run_time=datetime.datetime.now() # Chạy ngay lần đầu tiên
)

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    print("Scheduler stopped.")
    pass