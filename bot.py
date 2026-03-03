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
        # 1. Lấy trang chủ
        response = requests.get(home_url, headers=headers, timeout=15)
        
        # 2. Tìm TẤT CẢ các link có chữ "truc-tiep" (không phân biệt giải đấu)
        # Regex cực mạnh để bắt mọi định dạng link trận đấu
        matches = re.findall(r'/truc-tiep/[^"\'>\s]+', response.text)
        matches = list(dict.fromkeys(matches)) # Xóa link trùng

        print(f"Tìm thấy {len(matches)} trận đấu tiềm năng...")

        for path in matches:
            # Chỉ lấy các link liên quan đến bóng đá/thể thao
            if not any(word in path for word in ["bong-da", "the-thao", "sea-games", "cup"]):
                continue
                
            match_url = f"{base_url}{path}"
            try:
                # 3. Vào từng trận bóc tách link m3u8
                m_res = requests.get(match_url, headers=headers, timeout=10)
                # Tìm link stream thật (thường chứa wsSession hoặc token)
                m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                
                if m3u8_links:
                    final_link = max(m3u8_links, key=len) # Link dài nhất thường là link chuẩn
                    
                    # Tự động trích xuất tên trận đấu từ đường dẫn URL
                    raw_name = path.split('/')[-1].split('.')[0].replace('-', ' ').title()
                    
                    channels.append({
                        "name": f"⚽ {raw_name}",
                        "link": final_link
                    })
                    print(f"Thành công: {raw_name}")
            except:
                continue
    except Exception as e:
        print(f"Lỗi quét: {e}")

    # Nếu hoàn toàn không có trận nào đang đá
    if not channels:
        channels = [{"name": "📺 Chờ trận đấu tiếp theo...", "link": "https://tftv0gr3uomttgr31hcjt8rzdncbafi1g1hdcgyhdrpjqci1gq3mpcfhgg3dq.100ycdn.com/live/kplus_sport1/playlist.m3u8"}]

    # Ghi file JSON cho SportsTV
    with open("live.json", "w", encoding="utf-8") as f:
        json.dump({"name": f"LIVE {time.strftime('%H:%M')}", "groups": [{"group_name": "BÓNG ĐÁ", "channels": channels}]}, f, ensure_ascii=False, indent=2)

    # Ghi file M3U cho Monplayer
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f'#EXTINF:-1, {ch["name"]}\n{ch["link"]}|Referer={base_url}/\n')

if __name__ == "__main__":
    fetch_live_data()
