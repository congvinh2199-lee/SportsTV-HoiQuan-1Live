import requests
import re
import json
import time

def fetch_live_data():
    base_url = "https://sv2.hoiquan2.live"
    # Tập trung quét thẳng vào trang trực tiếp bóng đá
    scan_url = f"{base_url}/truc-tiep/bong-da"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": base_url,
        "Accept": "*/*"
    }

    channels = []
    try:
        # 1. Lấy danh sách trận đấu
        res = requests.get(scan_url, headers=headers, timeout=15)
        # Bắt các link trận đấu cụ thể
        matches = re.findall(r'/(?:truc-tiep|xem-truc-tiep)/[\w\-\./]+', res.text)
        unique_paths = list(dict.fromkeys(matches))

        for path in unique_paths:
            if path.count('/') < 3: continue
            
            match_url = f"{base_url}{path}"
            try:
                time.sleep(1)
                # 2. Truy cập vào trang trận đấu để lấy link stream
                m_res = requests.get(match_url, headers=headers, timeout=10)
                
                # Tìm link m3u8 có chứa token bảo mật (thường là link dài nhất)
                m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                
                if m3u8_links:
                    # Lọc bỏ các link quảng cáo hoặc link rác, lấy link chứa playlist hoặc m3u8 chuẩn
                    stream_link = max(m3u8_links, key=len)
                    
                    # Tên trận đấu: Lấy phần cuối của URL và làm đẹp
                    name_raw = path.split('/')[-1].split('.')[0].replace('-', ' ').title()
                    
                    channels.append({
                        "name": f"⚽ {name_raw}",
                        "link": stream_link,
                        "referer": match_url # Lưu lại referer riêng cho từng trận
                    })
            except:
                continue
    except Exception as e:
        print(f"Error: {e}")

    # Fallback nếu quét lỗi (Sử dụng 2 trận bạn vừa cung cấp)
    if not channels:
        channels = [
            {"name": "⚽ China W Vs Bangladesh W", "link": "https://p-cdn5.livetv2.net/hls2/27_8_89_v2.m3u8", "referer": "https://sv2.hoiquan2.live/"},
            {"name": "⚽ Melbourne City Vs Buriram Utd", "link": "https://p-cdn5.livetv2.net/hls2/27_8_71_v2.m3u8", "referer": "https://sv2.hoiquan2.live/"}
        ]

    # --- XUẤT FILE JSON (SportsTV) ---
    with open("live.json", "w", encoding="utf-8") as f:
        json.dump({"name": f"VINH LIVE {time.strftime('%H:%M')}", "groups": [{"group_name": "TRỰC TIẾP", "channels": channels}]}, f, ensure_ascii=False, indent=2)

    # --- XUẤT FILE M3U (Monplayer) ---
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            # Monplayer cần Referer của chính trang trận đấu đó để 'mở khóa' stream
            f.write(f'#EXTINF:-1, {ch["name"]}\n')
            f.write(f'{ch["link"]}|Referer={ch["referer"]}&User-Agent={headers["User-Agent"]}\n')

if __name__ == "__main__":
    fetch_live_data()
