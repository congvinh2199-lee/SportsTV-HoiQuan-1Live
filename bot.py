import requests
import json
import time
import re
import subprocess
import base64

class HoiQuanCrawler:
    def __init__(self):
        self.host = "https://sv2.hoiquan2.live"
        self.api_host = "https://api.hoiquan2.live"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": self.host + "/",
            "Origin": self.host,
            "Accept": "*/*"
        }

    def get_matches(self):
        print(f"[{time.strftime('%H:%M:%S')}] Đang quét danh sách trận đấu...")
        try:
            # Tham khảo logic plugin: Lấy data từ khối __NEXT_DATA__
            res = self.session.get(f"{self.host}/trang-chu", headers=self.headers, timeout=15)
            pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
            json_str = re.search(pattern, res.text).group(1)
            data = json.loads(json_str)
            
            # Tìm danh sách trận đấu trong cấu trúc Next.js props
            matches = []
            queries = data.get('props', {}).get('pageProps', {}).get('dehydratedState', {}).get('queries', [])
            for q in queries:
                state_data = q.get('state', {}).get('data', [])
                if isinstance(state_data, list):
                    for item in state_data:
                        if 'slug' in item and 'id' in item:
                            matches.append(item)
            return matches
        except Exception as e:
            print(f"Lỗi lấy danh sách: {e}")
            return []

    def get_stream_link(self, match):
        match_url = f"{self.host}/truc-tiep/{match['sport_type']}/{match['slug']}/{match['id']}"
        print(f"--- Đang phân tích: {match.get('name', match['slug'])}")
        
        try:
            # Logic quan trọng: Trang web thường fetch link từ 1 endpoint ẩn 
            # hoặc nhúng Base64 vào script.
            res = self.session.get(match_url, headers=self.headers, timeout=10)
            
            # 1. Tìm link m3u8 trực tiếp bằng regex mạnh
            m3u8 = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', res.text)
            if m3u8:
                return m3u8.group(1)
            
            # 2. Dự phòng: Tìm chuỗi Base64 (nếu link bị mã hóa như một số plugin dev-kit xử lý)
            b64_match = re.search(r'source["\']:\s*["\'](aHR0c[a-zA-Z0-9+/=]+)["\']', res.text)
            if b64_match:
                return base64.b64decode(b64_match.group(1)).decode('utf-8')
                
            return None
        except:
            return None

def run_bot():
    crawler = HoiQuanCrawler()
    matches = crawler.get_matches()
    
    if not matches:
        print("Không tìm thấy trận nào. Có thể cần cập nhật Headers.")
        return

    channels = []
    for m in matches:
        link = crawler.get_stream_link(m)
        if link:
            name = m.get('name', m['slug'].replace('-', ' ').title())
            icon = "🏸" if "cau-long" in m['sport_type'] else "⚽"
            channels.append({
                "name": f"{icon} {name}",
                "link": link,
                "headers": {"User-Agent": crawler.headers["User-Agent"], "Referer": crawler.host + "/"}
            })
            print(f"✅ Đã lấy link!")

    # Xuất file và Push GitHub
    output = {"name": f"HQ-DevKit {time.strftime('%H:%M')}", "groups": [{"group_name": "LIVE", "channels": channels}]}
    with open("live.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Tổng kết: {len(channels)} link. Đang đồng bộ...")
    try:
        subprocess.run(["git", "add", "live.json"], check=True)
        subprocess.run(["git", "commit", "-m", f"DevKit Sync {time.strftime('%H:%M')}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 ĐÃ CẬP NHẬT LÊN GITHUB!")
    except:
        pass

if __name__ == "__main__":
    run_bot()
