import requests
import re
import json
import time

def fetch_live_data():
    # Sử dụng Session để giữ Cookie, giúp vượt qua kiểm tra của web
    session = requests.Session()
    base_url = "https://sv2.hoiquan2.live"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "Referer": "https://www.google.com/"
    }

    channels = []
    found_paths = set()

    try:
        # Bước 1: Truy cập trang chủ để lấy Cookie hợp lệ
        session.get(base_url, headers=headers, timeout=15)
        
        # Bước 2: Quét trang danh mục bóng đá
        scan_url = f"{base_url}/truc-tiep/bong-da"
        res = session.get(scan_url, headers=headers, timeout=15)
        
        # Regex tìm link trận đấu (quét cả định dạng cũ và mới)
        matches = re.findall(r'/(?:truc-tiep|xem-truc-tiep)/[\w\-\./]+', res.text)
        for p in matches:
            clean_path = p.split('"')[0].split("'")[0].split(">")[0]
            if clean_path.count('/') >= 3:
                found_paths.add(clean_path)

        # Bước 3: Vào từng trận đấu để bóc tách link m3u8
        for path in found_paths:
            match_url = f"{base_url}{path}"
            try:
                # Nghỉ 2 giây để web không nghi ngờ là máy quét
                time.sleep(2)
                m_res = session.get(match_url, headers=headers, timeout=10)
                
                # Tìm link .m3u8
                m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                
                if m3u8_links:
                    final_link = max(m3u8_links, key=len)
                    name_raw = path.strip('/').split('/')[-1].split('.')[0].replace('-', ' ').title()
                    
                    channels.append({
                        "name": f"⚽ {name_raw}",
                        "link": final_link,
                        "origin_page": match_url
                    })
            except:
                continue

    except Exception as e:
        print(f"Lỗi: {e}")

    # Ghi file JSON cho SportsTV
    json_channels = [{"name": ch["name"], "link": ch["link"], "headers": {"User-Agent": headers["User-Agent"], "Referer": ch["origin_page"]}} for ch in channels]
    
    with open("live.json", "w", encoding="utf-8") as f:
        json.dump({"name": f"LIVE {time.strftime('%H:%M')}", "groups": [{"group_name": "TRỰC TIẾP", "channels": json_channels}]}, f, ensure_ascii=False, indent=2)

    # Ghi file M3U cho Monplayer
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f'#EXTINF:-1, {ch["name"]}\n{ch["link"]}|Referer={ch["origin_page"]}&User-Agent={headers["User-Agent"]}\n')

if __name__ == "__main__":
    fetch_live_data()
