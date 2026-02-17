import os
import time
import requests
import json
from collections import Counter

# AYARLAR
STEAM_ID = os.environ.get("STEAM_ID")
if STEAM_ID:
    STEAM_ID = STEAM_ID.strip()

APP_ID = 730
CONTEXT_ID = 2

def get_full_inventory():
    """Envanter listesini Steam'den çeker."""
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
        url = f"https://steamcommunity.com/inventory/{STEAM_ID}/{APP_ID}/{CONTEXT_ID}?l=turkish&count=100"
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

def get_price_database():
    """
    TÜM CS2 itemlerinin fiyatlarını TEK SEFERDE indirir.
    Böylece tek tek sorgu atıp engellenmeyiz.
    """
    print("🌍 Küresel fiyat veritabanı indiriliyor (Bu işlem 5-10sn sürebilir)...")
    
    # Bu URL tüm itemleri JSON olarak verir.
    # currency=TRY desteklemeyebilir, o yüzden USD çekip kurla çarpacağız.
    url = "http://csgobackpack.net/api/GetItemsList/v2/"
    
    try:
        r = requests.get(url, timeout=30)
        data = r.json()
        
        if data.get('success'):
            return data.get('items_list', {})
    except Exception as e:
        print(f"Veritabanı indirilemedi: {e}")
    
    return {}

def get_currency_rate():
    """USD -> TRY Kurunu çeker (Yaklaşık değer)"""
    try:
        # Basit bir API'den kur çekelim veya sabit verelim (API patlarsa diye)
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        data = r.json()
        return data['rates']['TRY']
    except:
        return 34.0 # API çalışmazsa manuel kur (Güncelleyebilirsin)

def main():
    # 1. Envanteri Çek
    items = get_full_inventory()
    if not items:
        print("Envanter boş veya gizli.")
        return

    # 2. Fiyat Veritabanını İndir
    price_db = get_price_database()
    usd_to_try = get_currency_rate()
    print(f"💲 Güncel Dolar Kuru: {usd_to_try:.2f} TL")

    # 3. İtemleri Grupla
    item_counts = Counter(items)
    unique_items = list(item_counts.keys())
    
    print(f"\n✅ {len(items)} item bulundu.")
    print(f"⚡ Yerel Fiyatlandırma başlıyor ({len(unique_items)} çeşit)...\n")
    
    total_value = 0.0
    found_count = 0
    
    print(f"{'ADET':<5} | {'ITEM ADI':<50} | {'BİRİM (TL)':<12} | {'TOPLAM'}")
    print("-" * 85)
    
    for name in unique_items:
        count = item_counts[name]
        unit_price = 0.0
        
        # Veritabanında ismi ara
        if name in price_db:
            item_data = price_db[name]
            # Fiyat verisi bazen 'price', bazen farklı yerde olabilir
            # CSGOBackpack yapısı: item -> price -> 24_hours -> average
            try:
                price_info = item_data.get('price', {})
                # Son 24 saat ortalamasını al, yoksa 7 günü dene, yoksa 30 günü
                p_raw = price_info.get('24_hours', {}).get('average') or \
                        price_info.get('7_days', {}).get('average') or \
                        price_info.get('30_days', {}).get('average') or 0
                
                if p_raw != 0:
                    unit_price = float(p_raw) * usd_to_try
                    found_count += 1
            except:
                pass
        
        line_total = unit_price * count
        total_value += line_total
        
        price_display = f"{unit_price:.2f}" if unit_price > 0 else "---"
        total_display = f"{line_total:.2f}" if line_total > 0 else "---"
        
        # Sadece fiyatı bulunanları veya önemlileri gösterelim (liste çok uzamasın diye)
        # Hepsini görmek istersen if koşulunu kaldır.
        print(f"{count:<5} | {name[:50]:<50} | {price_display:<12} | {total_display}")

    print("-" * 85)
    print(f"💰 GENEL TOPLAM DEĞER: {total_value:.2f} TL")
    print(f"📊 {len(unique_items)} çeşit itemden {found_count} tanesinin fiyatı bulundu.")
    
    if found_count == 0:
        print("\n⚠️ Hâlâ fiyat yoksa, CSGOBackpack API geçici olarak kapalıdır.")
        print("⚠️ Kodu KENDİ BİLGİSAYARINDA (Localhost) çalıştırmayı dene.")

if __name__ == "__main__":
    main()
