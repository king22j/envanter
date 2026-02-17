import requests
import time
import os
from dotenv import load_dotenv

# .env dosyasından gizli verileri yükle
load_dotenv()

# AYARLAR
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_ID = os.getenv("STEAM_ID")
APP_ID = 730  # 730 = CS2, 252490 = Rust, 570 = Dota 2
CURRENCY = 1  # 1 = USD, 3 = Euro, 34 = TL (Bazen API TL desteklemeyebilir, USD garantidir)

def get_steam_inventory(steam_id, app_id):
    """
    Kullanıcının envanter verisini çeker.
    Steam envanter endpoint'i assets ve descriptions olarak iki parça döner.
    """
    url = f"https://steamcommunity.com/inventory/{steam_id}/{app_id}/2?l=turkish&count=5000"
    
    try:
        response = requests.get(url)
        if response.status_code == 429:
            print("Çok fazla istek gönderildi (Rate Limit). Lütfen bekleyin.")
            return None
        
        data = response.json()
        
        if not data or 'assets' not in data:
            print("Envanter boş veya gizli.")
            return None

        # Descriptionları kolay erişim için sözlüğe çeviriyoruz
        descriptions = {f"{d['classid']}_{d['instanceid']}": d for d in data['descriptions']}
        
        inventory = []
        
        for asset in data['assets']:
            key = f"{asset['classid']}_{asset['instanceid']}"
            if key in descriptions:
                desc = descriptions[key]
                
                # Sadece pazarlanabilir (satılabilir) itemleri al
                if desc.get('marketable') == 1:
                    item = {
                        'name': desc['market_hash_name'], # Pazar araması için bu isim şart
                        'type': desc.get('type', ''),
                        'classid': asset['classid']
                    }
                    inventory.append(item)
        
        return inventory

    except Exception as e:
        print(f"Hata oluştu: {e}")
        return None

def get_item_price(market_hash_name, app_id):
    """
    Tek bir itemin pazar fiyatını çeker.
    DİKKAT: Çok hızlı çalıştırılırsa IP ban yer.
    """
    url = f"https://steamcommunity.com/market/priceoverview/"
    params = {
        'country': 'TR',
        'currency': 34, # 34 = Türk Lirası
        'appid': app_id,
        'market_hash_name': market_hash_name
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'lowest_price' in data:
            return data['lowest_price']
        else:
            return "Fiyat Bulunamadı"
            
    except Exception as e:
        return None

def main():
    print(f"Steam ID: {STEAM_ID} için envanter taranıyor...")
    
    inventory = get_steam_inventory(STEAM_ID, APP_ID)
    
    if inventory:
        print(f"Toplam {len(inventory)} adet satılabilir item bulundu.\n")
        print(f"{'ITEM ADI':<50} | {'FİYAT'}")
        print("-" * 65)
        
        # Örnek olarak sadece ilk 5 itemi tarıyoruz (API Ban yememek için)
        # Hepsini taramak isterseniz inventory[:5] kısmını inventory yapın.
        for item in inventory[:5]: 
            price = get_item_price(item['name'], APP_ID)
            print(f"{item['name']:<50} | {price}")
            
            # Steam API rate limitine takılmamak için bekleme süresi
            time.sleep(3) 
    else:
        print("Envanter alınamadı.")

if __name__ == "__main__":
    main()
