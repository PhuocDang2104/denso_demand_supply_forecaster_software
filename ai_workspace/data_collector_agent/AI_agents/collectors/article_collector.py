# C:\Users\Lenovo\AI_LLM_Agent\collectors\article_collector.py

import os
import requests
import json
import datetime
from dotenv import load_dotenv
from newsapi import NewsApiClient
from bs4 import BeautifulSoup

# --- CÀI ĐẶT ---
load_dotenv()
DATA_FILE_PATH = "market_data.json"
CHAR_LIMIT_PER_ARTICLE = 4000 

# --- MODULE 1: BỘ TRÍCH XUẤT (SCRAPER) - ĐÃ NÂNG CẤP ---
def scrape_article_content(url: str) -> str:
    """Truy cập URL và trích xuất TẤT CẢ văn bản."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # THAY ĐỔI QUAN TRỌNG: Lấy TẤT CẢ văn bản, không lọc thẻ <p>
        
        # 1. Xóa các thẻ rác (script, style, menu, footer...)
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.extract() # Xóa thẻ này khỏi soup

        # 2. Lấy tất cả văn bản còn lại, nối bằng dấu xuống dòng
        article_text = soup.get_text(separator='\n', strip=True)
        
        
        return article_text
    
    except requests.exceptions.RequestException as e:
        # Nếu là lỗi timeout (như BBC), bỏ qua
        if 'Read timed out' in str(e):
            print(f"  [Scraper Warning] Timed out (Bot detection?): {url}")
        else:
            print(f"  [Scraper Warning] Failed to retrieve URL {url}: {e}")
        return ""
    except Exception as e:
        print(f"  [Scraper Warning] Failed to parse content from {url}: {e}")
        return ""

# --- MODULE 2: BỘ THU THẬP (COLLECTOR) ---

def collect_and_save_articles():
    print(f"\n--- Running NewsAPI Collector @ {datetime.datetime.now()} ---")
    
    try:
        api_key = os.getenv("NEWS_API_KEY")
        if not api_key:
            print("ERROR: NEWS_API_KEY not found in .env file.")
            return

        newsapi = NewsApiClient(api_key=api_key)

        queries = [
            '("thị trường phụ tùng ô tô" OR "linh kiện ô tô" OR bugi OR "ô tô") AND Việt Nam',
            '(logistics OR "chuỗi cung ứng" OR "gián đoạn" OR "xuất nhập khẩu") AND Việt Nam',
            '("thiên tai" OR bão OR "lũ lụt" OR "sạt lở") AND Việt Nam'
        ]
        
        today = datetime.date.today()
        # THAY ĐỔI: Lấy 1 tháng để test (như bạn nói)
        one_month_ago = (today - datetime.timedelta(days=30)).isoformat()
        today_iso = today.isoformat()
        
        collected_articles = []
        urls_seen = set() 

        for query in queries:
            print(f"Executing query: {query}")
            response = newsapi.get_everything(
                q=query,
                from_param=one_month_ago, # Lấy 1 tháng
                to=today_iso,
                sort_by='relevancy'
            )
            
            articles_found = response.get('articles', [])
            print(f"  -> NewsAPI found {len(articles_found)} articles (processing top 3).")

            for article in articles_found[:2]: 
                url = article.get('url')
                title = article.get('title', 'No Title')
                
                if not url or url in urls_seen:
                    continue
                
                urls_seen.add(url) 
                print(f"    -> Scraping URL: {title}")
                
                raw_content = scrape_article_content(url)
                
                if raw_content: # Bây giờ, 'raw_content' sẽ có dữ liệu
                    truncated_content = raw_content[:CHAR_LIMIT_PER_ARTICLE]
                    collected_articles.append({
                        "title": title,
                        "url": url,
                        "timestamp": article.get('publishedAt', datetime.datetime.now().isoformat()),
                        "raw_text_content": truncated_content 
                    })

        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(collected_articles, f, ensure_ascii=False, indent=4)
            
        print(f"SUCCESS: Saved {len(collected_articles)} total scraped articles to {DATA_FILE_PATH}")
        
    except Exception as e:
        print(f"ERROR during data collection: {e}")

if __name__ == "__main__":
    collect_and_save_articles()