import requests
import json
import time
import re

def fetch_live_data():
    base_url = "https://sv2.hoiquan2.live"
    # Đây là link API ẩn chứa danh sách trận đấu của Hội Quán
    api_url = "https://api.hoiquan2.live/api/matches/live"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": base_url,
        "Origin": base_url,
        "Accept": "application/json"
    }

    channels = []
    try:
        # 1. Gửi yêu cầu thẳng đến API dữ liệu
        res = requests.get(api_url, headers=headers, timeout=15)
        data = res.json() # Chuyển dữ liệu về dạng danh sách

        # 2. Duyệt qua từng trận đấu trong dữ liệu trả về
        for match in data.get('data', []):
            match_name = match.get('name', 'Trận đấu không tên')
            slug = match.get('slug', '')
            match_id = match.get('id', '')
            
            # Tạo link trang trận đấu để làm Referer
            match_page = f"{base_url}/truc-tiep/bong-da/{slug}/{match_id}"
            
            # Lấy link stream (Thường nằm trong trường 'stream_url' hoặc phải vào trang con)
            # Nếu API trả về link stream luôn:
            stream_url = match.get('stream_url')
            
            # Nếu không có link stream trong API, ta vào trang con lấy (dùng lại logic cũ)
            if not stream_url:
                try:
                    time.sleep(1)
                    m_res = requests.get(match_page, headers=headers, timeout=10)
                    m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                    if m3u8_links:
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
        print(f"Lỗi API: {e}")

    # --- XUẤT FILE JSON (SportsTV) ---
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
        json.dump({"name": f"LIVE {time.strftime('%H:%M')}", "groups": [{"group_name": "BÓNG ĐÁ", "channels": json_channels}]}, f, ensure_ascii=False, indent=2)

    # --- XUẤT FILE M3U (Monplayer) ---
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f'#EXTINF:-1, {ch["name"]}\n{ch["link"]}|Referer={ch["referer"]}&User-Agent={headers["User-Agent"]}\n')

if __name__ == "__main__":
    fetch_live_data()
