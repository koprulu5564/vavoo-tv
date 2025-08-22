import requests
import json
import re
from collections import defaultdict
import unicodedata
import os

def sanitize_tvg_id(name):
    # Türkçe karakterleri dönüştür
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    
    # Özel karakterleri ve parantez içeriğini kaldır
    name = re.sub(r'\s*\([^)]*\)', '', name).strip()
    
    # Küçük harfe çevir ve boşlukları tire ile değiştir
    name = name.lower().replace(' ', '-')
    
    # Geçersiz karakterleri kaldır
    name = re.sub(r'[^a-z0-9-]', '', name)
    
    return name

def fetch_data():
    primary_url = "https://vavoo.to/channels"
    proxy_url = "https://api.codetabs.com/v1/proxy/?quest="
    
    try:
        response = requests.get(primary_url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    try:
        response = requests.get(proxy_url + primary_url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    return None

def generate_m3u_playlists():
    data = fetch_data()
    if not data:
        print("Veri alınamadı")
        return
    
    # Ülkelere göre kanalları grupla
    channels_by_country = defaultdict(list)
    
    for channel in data:
        country = channel.get('country', 'Unknown')
        channels_by_country[country].append(channel)
    
    # Tüm kanalları içeren m3u
    generate_m3u_file("all", data, "Tüm Kanallar")
    
    # Her ülke için ayrı m3u
    for country, channels in channels_by_country.items():
        filename = country.lower().replace(' ', '-')
        generate_m3u_file(filename, channels, country)

def generate_m3u_file(filename, channels, group_title):
    if not channels:
        return
        
    m3u_content = '#EXTM3U\n'
    
    for channel in channels:
        channel_id = channel.get('id', '')
        channel_name = channel.get('name', 'Unknown')
        country = channel.get('country', 'Unknown')
        
        # Parantez içeriğini temizle (sadece görünen isim için)
        display_name = re.sub(r'\s*\([^)]*\)', '', channel_name).strip()
        
        # TVG ID oluştur
        tvg_id = sanitize_tvg_id(channel_name)
        
        # Stream URL
        stream_url = f"https://vavoo.to/play/{channel_id}/index.m3u8"
        
        # M3U entry
        m3u_content += f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{display_name}" tvg-country="{country}" group-title="{group_title}",{display_name}\n'
        m3u_content += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5)\n'
        m3u_content += f'#EXTVLCOPT:http-referer=https://vavoo.to/\n'
        m3u_content += f'{stream_url}\n\n'
    
    # Dosyaya yaz
    with open(f"{filename}.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    print(f"{filename}.m3u oluşturuldu ({len(channels)} kanal)")

if __name__ == "__main__":
    generate_m3u_playlists()
