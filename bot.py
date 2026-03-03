import requests
import re
import json
import time

def fetch_live_data():
    base_url = "https://sv2.hoiquan2.live"
    # Quét cả trang chủ và trang danh mục để không sót trận
    urls_to_scan = [
        f"{base_url}/trang-chu",
        f"{base_url}/truc-tiep/bong-da"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": base_url
    }

    channels = []
    # Dùng set để tránh trùng lặp link
    found_paths = set()

    try:
        # 1. Quét tìm link các trận đấu
        for url in urls_to_scan:
            try:
                res = requests.get(url, headers=headers, timeout=15)
                # Quét tất cả các chuỗi có định dạng /truc-tiep/tên-trận-đấu
                matches = re.findall(r'/(?:truc-tiep|xem-truc-tiep)/[\w\-\./]+', res.text)
                for p in matches:
                    # Làm sạch link (loại bỏ dấu nháy hoặc ký tự thừa)
                    clean_path = p.split('"')[0].split("'")[0].split(">")[0]
                    if clean_path.count('/') >= 3:
                        found_paths.add(clean_path)
            except:
                continue
        
        print(f"Phát hiện {len(found_paths)} trận đấu đang diễn ra...")

        # 2. Vào từng link trận đấu để lấy link stream m3u8
        for path in found_paths:
            match_url = f"{base_url}{path}"
            try:
                time.sleep(1) # Tránh bị server chặn do truy cập quá nhanh
                m_res = requests.get(match_url, headers=headers, timeout=10)
                
                # Tìm link .m3u8 (thường nằm trong script phát video)
                m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                
                if m3u8_links:
                    # Lấy link dài nhất vì thường chứa token xác thực đầy đủ
                    final_link = max(m3u8_links, key=len)
                    
                    # Tách tên trận đấu từ URL cho đẹp
                    name_parts = path.strip('/').split('/')
                    name_raw = name_parts[-1].split('.')[0].replace('-', ' ').title()
                    
                    channels.append({
                        "name": f"⚽ {name_raw}",
                        "link": final_link,
                        "origin_page": match_url
                    })
            except:
                continue

    except Exception as e:
        print(f"Lỗi quá trình quét: {e}")

    # --- XUẤT FILE 1: live.json (Cho SportsTV) ---
    json_channels = []
    for ch in channels:
        json_channels.append({
            "name": ch["name"],
            "link": ch["link"],
            "headers": {
                "User-Agent": headers["User-Agent"],
                "Referer": ch["origin_page"] # Quan trọng: Giả lập Referer đúng trang trận đấu
            }
        })

    with open("live.json", "w", encoding="utf-8") as f:
        json.dump({
            "name": f"HỘI QUÁN LIVE - {time.strftime('%H:%M')}", 
            "groups": [{"group_name": "TRỰC TIẾP", "channels": json_channels}]
        }, f, ensure_ascii=False, indent=2)

    # --- XUẤT FILE 2: list.m3u (Cho Monplayer) ---
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f'#EXTINF:-1, {ch["name"]}\n')
            # Thêm Referer trực tiếp vào link cho các app hỗ trợ chuẩn này
            f.write(f'{ch["link"]}|Referer={ch["origin_page"]}&User-Agent={headers["User-Agent"]}\n')

if __name__ == "__main__":
    fetch_live_data()
