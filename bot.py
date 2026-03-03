import requests
import re
import json
import time

def fetch_live_data():
    base_url = "https://sv2.hoiquan2.live"
    home_url = f"{base_url}/trang-chu"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": base_url
    }

    channels = []
    try:
        # 1. Lấy danh sách trận đấu ở trang chủ
        response = requests.get(home_url, headers=headers, timeout=15)
        # Tìm các đường dẫn có dạng /truc-tiep/...
        matches = re.findall(r'/truc-tiep/[^"\'>\s]+', response.text)
        matches = list(dict.fromkeys(matches)) # Loại bỏ trùng

        for path in matches:
            match_url = f"{base_url}{path}"
            try:
                # 2. Vào từng trận lấy link stream m3u8
                m_res = requests.get(match_url, headers=headers, timeout=10)
                # Tìm link m3u8 có chứa wsSession (token)
                m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                
                if m3u8_links:
                    # Lấy link dài nhất vì thường chứa đầy đủ token bảo mật nhất
                    final_link = max(m3u8_links, key=len)
                    # Tách tên trận đấu từ URL
                    name_raw = path.split('/')[-1].replace('-', ' ').title()
                    
                    channels.append({
                        "name": f"⚽ {name_raw}",
                        "link": final_link,
                        "headers": {
                            "User-Agent": headers["User-Agent"],
                            "Referer": base_url,
                            "Origin": base_url
                        }
                    })
            except:
                continue
    except Exception as e:
        print(f"Error fetching: {e}")

    # Nếu không có trận nào đang live, thêm kênh K+ dự phòng
    if not channels:
        channels = [{"name": "📺 Hệ thống đang cập nhật trận đấu...", "link": "https://tftv0gr3uomttgr31hcjt8rzdncbafi1g1hdcgyhdrpjqci1gq3mpcfhgg3dq.100ycdn.com/live/kplus_sport1/playlist.m3u8"}]

    # 3. Xuất file JSON
    result = {
        "name": f"SportsTV LIVE - {time.strftime('%H:%M %d/%m')}",
        "groups": [{"group_name": "TRỰC TIẾP BÓNG ĐÁ", "channels": channels}]
    }

    with open("live.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fetch_live_data()
