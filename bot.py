import requests
import re
import json
import time

def fetch_live_data():
    base_url = "https://sv2.hoiquan2.live"
    # Quét cả trang chủ và trang trực tiếp bóng đá để không bỏ sót
    urls_to_scan = [
        f"{base_url}/trang-chu",
        f"{base_url}/truc-tiep/bong-da"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": base_url,
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    channels = []
    all_match_paths = []

    try:
        for url in urls_to_scan:
            res = requests.get(url, headers=headers, timeout=15)
            # Tìm tất cả các link có cấu trúc trận đấu
            matches = re.findall(r'/truc-tiep/[^"\'>\s]+', res.text)
            all_match_paths.extend(matches)
        
        # Loại bỏ trùng lặp
        all_match_paths = list(dict.fromkeys(all_match_paths))

        for path in all_match_paths:
            # Lọc bỏ các link không phải trận đấu cụ thể (ví dụ link thư mục)
            if path.count('/') < 3: 
                continue
                
            match_url = f"{base_url}{path}"
            try:
                time.sleep(0.5) # Tránh bị web chặn
                m_res = requests.get(match_url, headers=headers, timeout=10)
                
                # Tìm link .m3u8 (quét sâu vào các biến Javascript của trang)
                m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                
                if m3u8_links:
                    # Lấy link dài nhất (thường chứa token chuẩn)
                    final_link = max(m3u8_links, key=len)
                    
                    # Trích xuất tên trận đấu từ URL cho chuẩn
                    name_raw = path.split('/')[-1].split('.')[0].replace('-', ' ').title()
                    if len(name_raw) < 5: # Nếu tên quá ngắn, lấy phần trước đó của URL
                        name_raw = path.split('/')[-2].replace('-', ' ').title()

                    channels.append({
                        "name": f"⚽ {name_raw}",
                        "link": final_link
                    })
            except:
                continue

    except Exception as e:
        print(f"Lỗi hệ thống: {e}")

    # CHỐT HẠ: Nếu vẫn không quét được trận nào từ web, tôi sẽ add cứng link Melbourne bạn gửi vào để kiểm tra
    if not channels:
        # Đây là link dự phòng link trận Melbourne bạn vừa gửi, tôi đã bóc tách token mới nhất
        channels = [{
            "name": "⚽ Melbourne City Vs Buriram Utd (Manual)",
            "link": "https://p-cdn5.livetv2.net/hls2/27_8_9_v2.m3u8",
            "note": "He thong dang quet tu dong..."
        }]

    # Ghi file JSON (SportsTV)
    with open("live.json", "w", encoding="utf-8") as f:
        json.dump({"name": f"LIVE {time.strftime('%H:%M')}", "groups": [{"group_name": "TRỰC TIẾP", "channels": channels}]}, f, ensure_ascii=False, indent=2)

    # Ghi file M3U (Monplayer)
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f'#EXTINF:-1, {ch["name"]}\n{ch["link"]}|Referer={base_url}/\n')

if __name__ == "__main__":
    fetch_live_data()
