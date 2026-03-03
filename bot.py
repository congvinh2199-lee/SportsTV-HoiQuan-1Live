import requests
import re
import json
import time

def fetch_live_data():
    base_url = "https://sv2.hoiquan2.live"
    scan_url = f"{base_url}/truc-tiep/bong-da"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": base_url
    }

    channels = []
    try:
        # 1. Tự động quét danh sách trận đấu đang diễn ra
        res = requests.get(scan_url, headers=headers, timeout=15)
        # Tìm tất cả đường dẫn trận đấu
        matches = re.findall(r'/(?:truc-tiep|xem-truc-tiep)/[\w\-\./]+', res.text)
        unique_paths = list(dict.fromkeys(matches))

        for path in unique_paths:
            if path.count('/') < 3: continue
            
            match_url = f"{base_url}{path}"
            try:
                time.sleep(0.5)
                # 2. Vào từng trận để lấy link m3u8 động
                m_res = requests.get(match_url, headers=headers, timeout=10)
                m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                
                if m3u8_links:
                    final_link = max(m3u8_links, key=len)
                    name_raw = path.split('/')[-1].split('.')[0].replace('-', ' ').title()
                    
                    # 3. Đưa vào danh sách xử lý
                    channels.append({
                        "name": f"⚽ {name_raw}",
                        "link": final_link,
                        "origin_page": match_url # Giữ lại link gốc để làm Referer
                    })
            except:
                continue
    except Exception as e:
        print(f"Lỗi quét tự động: {e}")

    # Nếu hoàn toàn không có trận nào, mới hiện thông báo chờ
    if not channels:
        channels = [{"name": "📺 Chờ trận đấu tiếp theo...", "link": "https://tftv0gr3uomttgr31hcjt8rzdncbafi1g1hdcgyhdrpjqci1gq3mpcfhgg3dq.100ycdn.com/live/kplus_sport1/playlist.m3u8", "origin_page": base_url}]

    # --- XUẤT FILE JSON (Tự động gán Headers cho SportsTV) ---
    json_channels = []
    for ch in channels:
        json_channels.append({
            "name": ch["name"],
            "link": ch["link"],
            "headers": {
                "User-Agent": headers["User-Agent"],
                "Referer": ch["origin_page"] # Ép App dùng Referer đúng trang đó
            }
        })

    with open("live.json", "w", encoding="utf-8") as f:
        json.dump({"name": f"LIVE {time.strftime('%H:%M')}", "groups": [{"group_name": "BÓNG ĐÁ", "channels": json_channels}]}, f, ensure_ascii=False, indent=2)

    # --- XUẤT FILE M3U (Tự động gán Headers cho Monplayer) ---
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f'#EXTINF:-1, {ch["name"]}\n')
            f.write(f'{ch["link"]}|Referer={ch["origin_page"]}&User-Agent={headers["User-Agent"]}\n')

if __name__ == "__main__":
    fetch_live_data()
