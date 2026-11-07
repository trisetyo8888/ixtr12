import requests
import json
import re

# ================= CONFIGURATION =================
PORTAL_URL = "http://vod.supremetv.live/c/"  # Ubah dengan URL portal Anda (tanpa /c/)
MAC_ADDRESS = "00:1A:79:00:44:B8"            # Ubah dengan MAC Address Anda
OUTPUT_FILE = "playlist.m3u"
# =================================================

def get_token(portal_url, mac):
    """Mendapatkan token akses (handshake) dari portal"""
    url = f"{portal_url}/stalker_portal/server/load.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3",
        "Cookie": f"mac={mac}"
    }
    params = {
        "type": "stb",
        "action": "handshake",
        "js": "true"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()
        return data.get("js", {}).get("token")
    except Exception as e:
        print(f"[-] Gagal mendapatkan token: {e}")
        return None

def get_live_channels(portal_url, mac, token):
    """Hanya mengambil data Live TV (mengabaikan VOD/Series)"""
    url = f"{portal_url}/stalker_portal/server/load.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3",
        "Authorization": f"Bearer {token}",
        "Cookie": f"mac={mac}"
    }
    
    # type=itv membatasi API agar HANYA mengembalikan Live TV / Siaran Langsung
    params = {
        "type": "itv", 
        "action": "get_all_channels",
        "force_ch_link_check": "0",
        "fav": "0",
        "sortby": "number",
        "hd": "0"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        return response.json().get("js", {}).get("data", [])
    except Exception as e:
        print(f"[-] Gagal mengambil data Live TV: {e}")
        return []

def get_stream_link(portal_url, mac, token, cmd):
    """Mendapatkan link streaming asli dari perintah internal portal"""
    url = f"{portal_url}/stalker_portal/server/load.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3",
        "Authorization": f"Bearer {token}",
        "Cookie": f"mac={mac}"
    }
    params = {
        "type": "itv",
        "action": "create_link",
        "cmd": cmd,
        "forced_storage": "0",
        "download": "0"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        return response.json().get("js", {}).get("cmd", "")
    except:
        return ""

def main():
    print("[*] Memulai proses ekstraksi...")
    token = get_token(PORTAL_URL, MAC_ADDRESS)
    
    if not token:
        print("[-] Proses dihentikan karena token tidak ditemukan.")
        return

    print("[+] Token berhasil didapatkan. Mengambil daftar Live TV...")
    channels = get_live_channels(PORTAL_URL, MAC_ADDRESS, token)
    
    if not channels:
        print("[-] Tidak ada saluran Live TV yang ditemukan.")
        return

    print(f"[+] Menemukan {len(channels)} saluran Live TV. Memulai pembuatan file M3U...")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for ch in channels:
            name = ch.get("name")
            cmd = ch.get("cmd")
            category = ch.get("tv_genre_name", "Live TV")
            
            # Bersihkan tautan internal portal menjadi tautan streaming langsung
            clean_cmd = cmd.replace("ffrt ", "").replace("ffmpeg ", "")
            stream_url = get_stream_link(PORTAL_URL, MAC_ADDRESS, token, clean_cmd)
            
            if stream_url:
                # Menghapus format internal localhost jika ada
                if "localhost" in stream_url:
                    stream_url = re.sub(r'http://localhost:\d+/', '', stream_url)
                
                f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{category}", {name}\n')
                f.write(f'{stream_url}\n')
                print(f"[+] Ditambahkan: {name} ({category})")
                
    print(f"\n[🚀] Selesai! File bersih dari VOD dan disimpan sebagai: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
