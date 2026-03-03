import cloudscraper
import json
import time
import re

def fetch_live_data():
    # Khởi tạo bộ vượt tường lửa Cloudflare
    scraper = cloudscraper.create_scraper()
    base_url = "https://sv2.hoiquan2.live"
    # API chứa danh sách các trận đấu đang phát
    api_url = "https://api.hoiquan2.live/api/matches/live"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": base_url,
        "Origin": base_url,
        "Accept": "application/json"
    }

    channels = []
    try:
        # 1. Truy cập API để lấy danh sách trận đấu
        res = scraper.get(api_url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"Không thể kết nối API (Lỗi {res.status_code})")
            return
            
        data = res.json()

        # 2. Duyệt qua từng trận đấu
        for match in data.get('data', []):
            match_name = match.get('name', 'Trận đấu đang diễn ra')
            slug = match.get('slug', '')
            match_id = match.get('id', '')
            match_page = f"{base_url}/truc-tiep/bong-da/{slug}/{match_id}"
            
            # Ưu tiên lấy link stream trực tiếp từ API
            stream_url = match.get('stream_url')
            
            # Nếu API không có link, truy cập trang chi tiết để bóc tách m3u8
            if not stream_url:
                try:
                    time.sleep(1.5) # Nghỉ để tránh bị quét
                    m_res = scraper.get(match_page, headers=headers, timeout=10)
                    m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                    if m3u8_links:
                        # Chọn link dài nhất thường là link chuẩn có Token
                        stream_url = max(m3u8_links, key=len)
                except:
                    continue

            if stream_url:
                channels.append({
                    "name": f"⚽ {match_name}",
                    "link": stream_url,
                    "referer": match_page
                })

    except Exception as e:
        print(f"Lỗi hệ thống: {e}")

    # --- XUẤT FILE JSON (Dùng cho SportsTV) ---
    json_channels = []
    for ch in channels:
        json_channels.append({
            "name": ch["name"],
            "link": ch["link"],
            "headers": {
                "User-Agent": headers["User-Agent"],
                "Referer": ch["referer"]
            }
        })
    
    with open("live.json", "w", encoding="utf-8") as f:
        json.dump({
            "name": f"HỘI QUÁN LIVE - {time.strftime('%H:%M')}", 
            "groups": [{"group_name": "BÓNG ĐÁ TRỰC TIẾP", "channels": json_channels}]
        }, f, ensure_ascii=False, indent=2)

    # --- XUẤT FILE M3U (Dùng cho Monplayer/OTT Navigator) ---
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f'#EXTINF:-1, {ch["name"]}\n')
            f.write(f'{ch["link"]}|Referer={ch["referer"]}&User-Agent={headers["User-Agent"]}\n')

if __name__ == "__main__":
    fetch_live_data()
