import os
import time
import requests
import urllib.parse
from collections import Counter

# AYARLAR
STEAM_ID = os.environ.get("STEAM_ID")
if STEAM_ID:
    STEAM_ID = STEAM_ID.strip()

APP_ID = 730
CONTEXT_ID = 2
BATCH_SIZE = 100

def get_full_inventory():
    """Envanter listesini Steam'den çeker (Bu kısım zaten çalışıyordu)."""
    if not STEAM_ID:
        print("HATA: STEAM_ID yok!")
        return []

    print(f"--- Envanter Taranıyor: {STEAM_ID} ---")
    
    all_items = []
    start_assetid = None
    more_items = True
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    while more_items:
        url = f"https://steamcommunity.com/inventory/{STEAM_ID}/{APP_ID}/{CONTEXT_ID}?l=turkish&count={BATCH_SIZE}"
        if start_assetid:
            url += f"&start_assetid={start_assetid}"
            
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200: break
            
            data = res.json()
            if not data or 'assets' not in data: break

            descriptions = {f"{d['classid']}_{d['instanceid']}": d for d in data.get('descriptions', [])}
            
            for asset in data['assets']:
                key = f"{asset['classid']}_{asset['instanceid']}"
                if key in descriptions:
                    desc = descriptions[key]
                    if desc.get('marketable') == 1:
                        all_items.append(desc['market_hash_name'])
            
            more_items = data.get('more_items', 0) == 1
            start_assetid = data.get('last_assetid')
            time.sleep(0.5)

        except:
            break

    return all_items

def get_price_fast(item_name):
    """
    Steam yerine CSGOBackpack API kullanır.
    Daha hızlıdır ve GitHub IP'sini engellemez.
    """
    # İsimdeki özel karakterleri URL uyumlu hale getir
    encoded_name = urllib.parse.quote(item_name)
    
    # CSGOBackpack API (TRY para birimi ile)
    url = f"http://csgobackpack.net/api/GetItemPrice/?currency=TRY&id={encoded_name}&time=7"

    try:
        # Timeout'u kısa tutuyoruz, cevap vermezse geçsin
        r = requests.get(url, timeout=5)
        data = r.json()
        
        if data.get('success'):
            # API bazen 'average_price', bazen 'median_price' döner
            price_str = data.get('average_price', "0")
            if price_str == "0":
                 price_str = data.get('median_price', "0")
            
            # "15.42" gibi gelir, floata çevirelim
            return float(price_str)
            
    except Exception as e:
        pass
    
    return 0.0

def main():
    start_time = time.time()
    items = get_full_inventory()
    
    if not items:
        print("Envanter boş veya gizli.")
        return

    # İtemleri Grupla
    item_counts = Counter(items)
    unique_items = list(item_counts.keys())
    
    print(f"\n✅ {len(items)} item bulundu.")
    print(f"⚡ Fiyatlandırma başlıyor ({len(unique_items)} çeşit)... HIZLI MOD AKTİF\n")
    
    total_value = 0.0
    
    print(f"{'ADET':<5} | {'ITEM ADI':<50} | {'BİRİM (TL)':<12} | {'TOPLAM'}")
    print("-" * 85)
    
    for name in unique_items:
        count = item_counts[name]
        
        # Fiyat çek (Dış Kaynak)
        unit_price = get_price_fast(name)
        
        line_total = unit_price * count
        total_value += line_total
        
        price_display = f"{unit_price:.2f}" if unit_price > 0 else "---"
        total_display = f"{line_total:.2f}" if line_total > 0 else "---"
        
        print(f"{count:<5} | {name[:50]:<50} | {price_display:<12} | {total_display}")
        
        # ÇOK KISA BEKLEME (Steam olmadığı için 0.2sn yeter)
        time.sleep(0.2)

    elapsed = time.time() - start_time
    print("-" * 85)
    print(f"⏱️  İşlem Süresi: {elapsed:.1f} saniye")
    print(f"💰 GENEL TOPLAM DEĞER: {total_value:.2f} TL")

if __name__ == "__main__":
    main()
