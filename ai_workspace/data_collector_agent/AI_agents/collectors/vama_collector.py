# C:\Users\Lenovo\AI_LLM_Agent\collectors\vama_collector.py
    
import os
import json
import requests
from bs4 import BeautifulSoup
import pdfplumber
import datetime

# --- CÀI ĐẶT CÁC ĐƯỜNG DẪN ---
VAMA_PAGE_URL = "http://vama.org.vn/vn/bao-cao-ban-hang.html"
# --- THAY ĐỔI (1): Thêm Base URL ---
VAMA_BASE_URL = "http://vama.org.vn" 

REPORTS_DIR = "reports" 
MEMORY_FILE = "vama_last_url.txt"
OUTPUT_FILE = "vama_data.json"

def scrape_and_process_vama():
    """
    Quy trình hoàn chỉnh: Giám sát, Tải về, Đọc PDF và Lưu.
    """
    print(f"\n--- Running VAMA Collector @ {datetime.datetime.now()} ---")
    
    try:
        # --- BƯỚC 1: TÌM LINK PDF MỚI NHẤT ---
        print(f"Checking VAMA page: {VAMA_PAGE_URL}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(VAMA_PAGE_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        summary_link_tag = soup.find('a', string=lambda text: 'summary.pdf' in text.lower())
        
        if not summary_link_tag:
            print("  [Error] Could not find the 'Summary.pdf' link on the page.")
            return

        # Đây là link tương đối (ví dụ: /Data/...)
        relative_pdf_url = summary_link_tag['href'] 
        new_pdf_title = summary_link_tag.text.strip()
        
        # --- THAY ĐỔI (2): Tạo URL tuyệt đối (Absolute URL) ---
        # Nối Base URL với link tương đối để có link tải về hoàn chỉnh
        absolute_pdf_url = VAMA_BASE_URL + relative_pdf_url
        
        print(f"  Found latest report link: {new_pdf_title}")

        # --- BƯỚC 2: KIỂM TRA TRÙNG LẶP ---
        # (Chúng ta dùng link tuyệt đối để kiểm tra cho chắc)
        last_processed_url = ""
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                last_processed_url = f.read().strip()
        except FileNotFoundError:
            print("  No memory file found. Will process as new.")

        if absolute_pdf_url == last_processed_url:
            print("  [Info] This report has already been processed. No new data.")
            return

        print(f"  [NEW DATA] New report found! Processing...")

        # --- BƯỚC 3: TẢI FILE PDF MỚI ---
        # --- THAY ĐỔI (3): Dùng link tuyệt đối để tải ---
        print(f"  Downloading PDF from: {absolute_pdf_url}") 
        pdf_response = requests.get(absolute_pdf_url, headers=headers, timeout=20)
        
        os.makedirs(REPORTS_DIR, exist_ok=True) 
        local_pdf_path = os.path.join(REPORTS_DIR, "vama_latest_summary.pdf")
        with open(local_pdf_path, 'wb') as f:
            f.write(pdf_response.content)

        # --- BƯỚC 4: ĐỌC VÀ TRÍCH XUẤT PDF ---
        print(f"  Extracting text from PDF: {local_pdf_path}")
        full_pdf_text = ""
        with pdfplumber.open(local_pdf_path) as pdf:
            for page in pdf.pages:
                text_data = page.extract_text() 
                if text_data:
                    full_pdf_text += f"\n--- PAGE {page.page_number} ---\n{text_data}"

        if not full_pdf_text:
            print("  [Error] PDF file was empty or unreadable.")
            return

        # --- BƯỚC 5: LƯU DỮ LIỆU CHO AGENT ---
        vama_data = {
            "report_title": new_pdf_title,
            "report_url": absolute_pdf_url, # Lưu link tuyệt đối
            "processed_timestamp": datetime.datetime.now().isoformat(),
            "extracted_text": full_pdf_text
        }
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(vama_data, f, ensure_ascii=False, indent=4)

        print(f"SUCCESS: Saved VAMA extracted text to {OUTPUT_FILE}")

        # --- BƯỚC 6: CẬP NHẬT BỘ NHỚ ---
        # --- THAY ĐỔI (4): Lưu link tuyệt đối vào bộ nhớ ---
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            f.write(absolute_pdf_url) 

    except Exception as e:
        print(f"ERROR during VAMA data collection: {e}")

if __name__ == "__main__":
    scrape_and_process_vama()