import requests
import re
import json
import time

def fetch_live_data():
    base_url = "https://sv2.hoiquan2.live"
    # Quét đồng thời trang chủ và trang chuyên mục bóng đá
    urls_to_scan = [
        f"{base_url}/trang-chu",
        f"{base_url}/truc-tiep/bong-da"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": base_url,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }

    channels = []
    found_paths = []

    try:
        # 1. Tìm tất cả các link trận đấu tiềm năng
        for scan_url in urls_to_scan:
            try:
                res = requests.get(scan_url, headers=headers, timeout=15)
                # Regex siêu mạnh để bắt mọi link chứa từ khóa truc-tiep
                matches = re.findall(r'/[^"\'>\s]*truc-tiep[^"\'>\s]*', res.text)
                found_paths.extend(matches)
            except:
                continue
        
        # Loại bỏ trùng lặp và làm sạch danh sách
        unique_paths = list(dict.fromkeys(found_paths))

        for path in unique_paths:
            # Chỉ lấy các link có chiều sâu (tránh link menu chung chung)
            if path.count('/') < 3 or any(x in path for x in ['.css', '.js', '.png']):
                continue
                
            match_url = f"{base_url}{path}"
            try:
                time.sleep(0.5) # Nghỉ ngắn để không bị server chặn
                m_res = requests.get(match_url, headers=headers, timeout=10)
                
                # Tìm link stream m3u8 trong mã nguồn (kể cả trong script)
                m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                
                if m3u8_links:
                    # Ưu tiên lấy link có token wsSession hoặc dài nhất
                    final_link = max(m3u8_links, key=len)
                    
                    # Trích xuất tên trận đấu từ URL cho đẹp
                    name_raw = path.split('/')[-1].split('.')[0].replace('-', ' ').title()
                    if len(name_raw) < 5:
                        name_raw = path.split('/')[-2].replace('-', ' ').title()

                    channels.append({
                        "name": f"⚽ {name_raw}",
                        "link": final_link
                    })
            except:
                continue

    except Exception as e:
        print(f"Lỗi: {e}")

    # CHẾ ĐỘ DỰ PHÒNG: Nếu web trống trơn, lấy link trận Melbourne bạn gửi làm mẫu
    if not channels:
        channels = [{
            "name": "⚽ Melbourne City Vs Buriram Utd (Live)",
            "link": "https://p-cdn5.livetv2.net/hls2/27_8_9_v2.m3u8"
        }]

    # --- XUẤT FILE 1: live.json (Dành cho SportsTV) ---
    json_data = {
        "name": f"VINH LIVE - {time.strftime('%H:%M %d/%m')}",
        "groups": [
            {
                "group_name": "TRỰC TIẾP BÓNG ĐÁ",
                "channels": channels
            }
        ]
    }
    with open("live.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # --- XUẤT FILE 2: list.m3u (Dành cho Monplayer) ---
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            # Thêm Referer trực tiếp vào link cho Monplayer dễ đọc
            f.write(f'#EXTINF:-1, {ch["name"]}\n')
            f.write(f'{ch["link"]}|Referer={base_url}/\n')

if __name__ == "__main__":
    fetch_live_data()
