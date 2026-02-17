import os
import time
import requests
import json

# GitHub Secret'tan veya direkt buraya yazarak test edebilirsin
STEAM_API_KEY = os.environ.get("STEAM_API_KEY")
STEAM_ID = os.environ.get("STEAM_ID")

# APP_ID AYARI
# 730 = CS2 (Counter-Strike 2)
# 252490 = Rust
# 570 = Dota 2
# Eğer CS2 oynamıyorsan burayı değiştirmelisin!
APP_ID = 730 
CONTEXT_ID = 2

def get_inventory():
    if not STEAM_ID:
        print("HATA: STEAM_ID girilmemiş!")
        return None

    print(f"ID: {STEAM_ID} için envanter taranıyor (AppID: {APP_ID})...")
    
    url = f"https://steamcommunity.com/inventory/{STEAM_ID}/{APP_ID}/{CONTEXT_ID}?l=turkish&count=5000"
    
    # İŞTE ÇÖZÜM BURASI: Tarayıcı taklidi yapıyoruz
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://steamcommunity.com/profiles/{STEAM_ID}/inventory"
    }
    
    try:
        # headers parametresini ekledik
        response = requests.get(url, headers=headers)
        
        # Hata ayıklama için durum kodunu yazdıralım
        print(f"Steam Cevap Kodu: {response.status_code}")
        
        if response.status_code == 403:
            print("HATA 403: Erişim reddedildi. Gizlilik ayarları veya IP banı.")
            return None
        if response.status_code == 429:
            print("HATA 429: Çok fazla istek! (Rate Limit).")
            return None
            
        data = response.json()
        
        # Eğer cevap boşsa veya assets yoksa
        if not data:
            print("Steam boş veri döndürdü (null).")
            return None
            
        if 'assets' not in data:
            print("Envanter verisi alındı ama içinde eşya (assets) yok.")
            print(f"Gelen Veri Başlığı: {list(data.keys())}") # Hatanın sebebini görmek için
            # Eğer 'total_inventory_count': 0 geliyorsa o oyunda itemin yoktur.
            return None

        descriptions = {f"{d['classid']}_{d['instanceid']}": d for d in data['descriptions']}
        inventory_items = []

        for asset in data['assets']:
            key = f"{asset['classid']}_{asset['instanceid']}"
            if key in descriptions:
                desc = descriptions[key]
                if desc.get('marketable') == 1:
                    inventory_items.append(desc['market_hash_name'])

        return inventory_items

    except Exception as e:
        print(f"Kod hatası: {e}")
        return None

def get_price(market_hash_name):
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        'country': 'TR',
        'currency': 34,
        'appid': APP_ID,
        'market_hash_name': market_hash_name
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        if data and 'lowest_price' in data:
            return data['lowest_price']
        return "Fiyat Yok"
    except:
        return "Hata"

def main():
    items = get_inventory()
    
    if items:
        print(f"\nToplam {len(items)} satılabilir eşya bulundu. Fiyatlar çekiliyor...\n")
        print(f"{'ITEM ADI':<60} | {'FİYAT'}")
        print("-" * 75)
        
        for item_name in items[:5]: # Test için sadece ilk 5'i
            price = get_price(item_name)
            print(f"{item_name:<60} | {price}")
            time.sleep(3)
    else:
        print("\nÇÖZÜM ÖNERİLERİ:")
        print("1. CS2 (AppID 730) envanterin boş olabilir mi? Başka oyun mu deniyorsun?")
        print("2. Steam profilindeki gizlilik ayarlarında 'Envanter' -> 'Herkese Açık' mı?")
        print("3. 'Steam Guard' yeni aktif edildiyse 7-15 gün kısıtlama olabilir.")

if __name__ == "__main__":
    main()
