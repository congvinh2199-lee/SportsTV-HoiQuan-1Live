import cloudscraper
import re
import json
import time

def fetch_live_data():
    # Tạo scraper để vượt qua Cloudflare
    scraper = cloudscraper.create_scraper()
    base_url = "https://sv2.hoiquan2.live"
    scan_url = f"{base_url}/truc-tiep/bong-da"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": base_url
    }

    channels = []
    try:
        # Bước 1: Vượt tường lửa lấy nội dung trang danh sách
        response = scraper.get(scan_url, headers=headers, timeout=20)
        html_content = response.text
        
        # Bước 2: Tìm link trận đấu
        matches = re.findall(r'/(?:truc-tiep|xem-truc-tiep)/[\w\-\./]+', html_content)
        unique_paths = list(dict.fromkeys(matches))

        for path in unique_paths:
            if path.count('/') < 3: continue
            
            match_url = f"{base_url}{path}"
            try:
                time.sleep(2) # Nghỉ 2 giây để tránh bị phát hiện
                m_res = scraper.get(match_url, headers=headers, timeout=15)
                
                # Tìm link m3u8
                m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                
                if m3u8_links:
                    final_link = max(m3u8_links, key=len)
                    name_raw = path.split('/')[-1].split('.')[0].replace('-', ' ').title()
                    
                    channels.append({
                        "name": f"⚽ {name_raw}",
                        "link": final_link,
                        "origin_page": match_url
                    })
            except:
                continue

    except Exception as e:
        print(f"Lỗi hệ thống: {e}")

    # Ghi file JSON cho SportsTV
    json_channels = []
    for ch in channels:
        json_channels.append({
            "name": ch["name"],
            "link": ch["link"],
            "headers": {
                "User-Agent": headers["User-Agent"],
                "Referer": ch["origin_page"]
            }
        })
    
    with open("live.json", "w", encoding="utf-8") as f:
        json.dump({"name": f"LIVE {time.strftime('%H:%M')}", "groups": [{"group_name": "TRỰC TIẾP", "channels": json_channels}]}, f, ensure_ascii=False, indent=2)

    # Ghi file M3U cho Monplayer
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f'#EXTINF:-1, {ch["name"]}\n{ch["link"]}|Referer={ch["origin_page"]}&User-Agent={headers["User-Agent"]}\n')

if __name__ == "__main__":
    fetch_live_data()
