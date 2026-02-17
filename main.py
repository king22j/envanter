import os
import time
import requests
import json
import urllib.parse
from collections import Counter

# AYARLAR
STEAM_ID = os.environ.get("STEAM_ID")
if STEAM_ID:
    STEAM_ID = STEAM_ID.strip()

APP_ID = 730  # CS2
CONTEXT_ID = 2
BATCH_SIZE = 100

def get_full_inventory():
    """Tüm envanteri çeker ve item isimlerini listeler."""
    if not STEAM_ID:
        print("HATA: STEAM_ID yok!")
        return []

    print(f"ID: {STEAM_ID} envanteri taranıyor...")
    
    all_items = []
    start_assetid = None
    more_items = True
    page = 1

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://steamcommunity.com/profiles/{STEAM_ID}/inventory",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    while more_items:
        url = f"https://steamcommunity.com/inventory/{STEAM_ID}/{APP_ID}/{CONTEXT_ID}?l=turkish&count={BATCH_SIZE}"
        if start_assetid:
            url += f"&start_assetid={start_assetid}"
            
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Envanter çekilemedi (Hata: {response.status_code})")
                break
                
            data = response.json()
            if not data or 'assets' not in data:
                break

            descriptions = {f"{d['classid']}_{d['instanceid']}": d for d in data.get('descriptions', [])}
            
            for asset in data['assets']:
                key = f"{asset['classid']}_{asset['instanceid']}"
                if key in descriptions:
                    desc = descriptions[key]
                    if desc.get('marketable') == 1:
                        all_items.append(desc['market_hash_name'])
            
            more_items = data.get('more_items', 0) == 1
            start_assetid = data.get('last_assetid')
            page += 1
            time.sleep(1) # Sayfa geçişi beklemesi

        except Exception as e:
            print(f"Hata: {e}")
            break

    return all_items

def get_price(market_hash_name):
    """Fiyat çeker. URL encoding yaparak hataları azaltır."""
    # İsimdeki özel karakterleri (™ | boşluk) URL formatına çevir
    encoded_name = urllib.parse.quote(market_hash_name)
    
    url = f"https://steamcommunity.com/market/priceoverview/?country=TR&currency=34&appid={APP_ID}&market_hash_name={encoded_name}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://steamcommunity.com/market/",
        "Accept": "application/json" 
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code == 429:
            print(f"   ⚠️ Hızlı istek engeli (429). 10sn bekleniyor...")
            time.sleep(10)
            return get_price(market_hash_name) # Tekrar dene

        data = res.json()
        
        # lowest_price yoksa median_price dene
        price_raw = data.get('lowest_price') or data.get('median_price')
        
        if price_raw:
            # "15,40 TL" -> 15.40 Float çevirimi
            # Önce "TL" ve boşlukları sil
            clean_str = price_raw.replace("TL", "").replace("USD", "").strip()
            # Binlik ayracı (.) varsa sil, ondalık ayracı (,) varsa nokta yap
            # Örnek: 1.250,50 -> 1250.50
            if "," in clean_str:
                clean_str = clean_str.replace(".", "").replace(",", ".")
            
            try:
                return float(clean_str), price_raw
            except:
                return 0.0, price_raw # Çeviremezse string olarak kalsın
                
    except Exception as e:
        pass
        
    return 0.0, "Çekilemedi"

def main():
    # 1. Envanteri Çek
    items = get_full_inventory()
    if not items:
        print("Envanter boş veya erişilemedi.")
        return

    # 2. İtemleri Grupla (Örn: 50 tane Kasa -> 1 tane Kasa x 50)
    # Counter, listeyi sayar ve sözlük yapar: {'Kasa': 50, 'Skin': 1}
    item_counts = Counter(items)
    unique_items = list(item_counts.keys())
    
    print(f"\nToplam {len(items)} adet item bulundu.")
    print(f"Gruplandıktan sonra {len(unique_items)} benzersiz item sorgulanacak.\n")
    
    total_inventory_value = 0.0
    
    # Tablo Başlığı
    print(f"{'ADET':<5} | {'ITEM ADI':<50} | {'BİRİM':<12} | {'TOPLAM'}")
    print("-" * 85)
    
    # 3. Fiyatları Sorgula (Sadece benzersiz itemler için)
    for name in unique_items:
        count = item_counts[name]
        
        # Fiyatı çek
        unit_val, unit_str = get_price(name)
        
        # Toplamı hesapla
        line_total = unit_val * count
        total_inventory_value += line_total
        
        # Ekrana bas
        if unit_val > 0:
            print(f"{count:<5} | {name:<50} | {unit_str:<12} | {line_total:.2f} TL")
        else:
            print(f"{count:<5} | {name:<50} | {'Yok':<12} | -")
            
        # Bekleme süresi (Steam Ban Yememek İçin)
        # Önceki kodda 3 saniyeydi, şimdi grupladığımız için istek azaldı ama yine de 
        # güvenli olsun diye 3 saniye tutuyoruz.
        time.sleep(3)

    print("-" * 85)
    print(f"GENEL TOPLAM TAHMİNİ DEĞER: {total_inventory_value:.2f} TL")

if __name__ == "__main__":
    main()
