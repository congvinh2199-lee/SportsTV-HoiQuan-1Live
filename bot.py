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
        response = requests.get(home_url, headers=headers, timeout=15)
        matches = re.findall(r'/truc-tiep/[^"\'>\s]+', response.text)
        matches = list(dict.fromkeys(matches))

        for path in matches:
            match_url = f"{base_url}{path}"
            try:
                m_res = requests.get(match_url, headers=headers, timeout=10)
                m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', m_res.text)
                
                if m3u8_links:
                    final_link = max(m3u8_links, key=len)
                    name_raw = path.split('/')[-1].replace('-', ' ').title()
                    
                    channels.append({
                        "name": f"⚽ {name_raw}",
                        "link": final_link
                    })
            except:
                continue
    except Exception as e:
        print(f"Error: {e}")

    # Nếu không có trận nào
    if not channels:
        channels = [{"name": "📺 Dang cap nhat tran dau...", "link": "https://tftv0gr3uomttgr31hcjt8rzdncbafi1g1hdcgyhdrpjqci1gq3mpcfhgg3dq.100ycdn.com/live/kplus_sport1/playlist.m3u8"}]

    # --- XUẤT FILE 1: live.json (Cho SportsTV) ---
    result_json = {
        "name": f"SportsTV LIVE - {time.strftime('%H:%M')}",
        "groups": [{"group_name": "TRỰC TIẾP", "channels": channels}]
    }
    with open("live.json", "w", encoding="utf-8") as f:
        json.dump(result_json, f, ensure_ascii=False, indent=2)

    # --- XUẤT FILE 2: list.m3u (Cho Monplayer - CHUẨN MỚI) ---
    with open("list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            # Monplayer cần Header Referer để xem được, chúng ta nhét thẳng vào link theo chuẩn M3U
            f.write(f'#EXTINF:-1, {ch["name"]}\n')
            f.write(f'{ch["link"]}|Referer={base_url}/\n')

if __name__ == "__main__":
    fetch_live_data()
