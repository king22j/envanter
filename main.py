import os
import time
import requests
import json

# Şifreleri ve ID'yi sistemden (GitHub Secrets veya .env) çekiyoruz
STEAM_API_KEY = os.environ.get("STEAM_API_KEY")
STEAM_ID = os.environ.get("STEAM_ID")

# Sabitler (CS2 için 730)
APP_ID = 730
CONTEXT_ID = 2

def get_inventory():
    """Steam envanterini çeker."""
    if not STEAM_ID:
        print("HATA: STEAM_ID bulunamadı!")
        return None

    print(f"ID: {STEAM_ID} için envanter taranıyor...")
    
    # Steam Inventory Endpoint
    url = f"https://steamcommunity.com/inventory/{STEAM_ID}/{APP_ID}/{CONTEXT_ID}?l=turkish&count=5000"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 403:
            print("HATA: Profilin veya envanterin gizli! Lütfen 'Herkese Açık' yap.")
            return None
        if response.status_code == 429:
            print("HATA: Çok fazla istek atıldı (Rate Limit).")
            return None
            
        data = response.json()
        
        if not data or 'assets' not in data:
            print("Envanter boş veya okunamadı.")
            return None

        # Varlıkları ve tanımları eşleştirme
        descriptions = {f"{d['classid']}_{d['instanceid']}": d for d in data['descriptions']}
        inventory_items = []

        for asset in data['assets']:
            key = f"{asset['classid']}_{asset['instanceid']}"
            if key in descriptions:
                desc = descriptions[key]
                # Sadece satılabilir itemleri al
                if desc.get('marketable') == 1:
                    inventory_items.append(desc['market_hash_name'])

        return inventory_items

    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        return None

def get_price(market_hash_name):
    """Itemin en düşük fiyatını çeker."""
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        'country': 'TR',
        'currency': 34, # 34 = TL
        'appid': APP_ID,
        'market_hash_name': market_hash_name
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data and 'lowest_price' in data:
            return data['lowest_price']
        return "Fiyat Yok"
    except:
        return "Hata"

def main():
    if not STEAM_API_KEY:
        print("UYARI: STEAM_API_KEY girilmemiş (Bazı özellikler kısıtlı olabilir).")

    items = get_inventory()
    
    if items:
        print(f"\nToplam {len(items)} satılabilir eşya bulundu. Fiyatlar çekiliyor...\n")
        print(f"{'ITEM ADI':<60} | {'FİYAT'}")
        print("-" * 75)
        
        # GitHub Action süresi dolmasın diye örnek olarak ilk 10 itemi çekiyoruz.
        # Hepsini çekmek istersen [:10] kısmını sil.
        for item_name in items[:10]:
            price = get_price(item_name)
            print(f"{item_name:<60} | {price}")
            
            # Steam API banlamaması için bekleme süresi
            time.sleep(3)
    else:
        print("İşlem başarısız oldu.")

if __name__ == "__main__":
    main()
