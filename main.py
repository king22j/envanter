import os
import time
import requests
import json

# GitHub Secret'tan verileri al
STEAM_API_KEY = os.environ.get("STEAM_API_KEY")
raw_steam_id = os.environ.get("STEAM_ID")

# ID Güvenlik Kontrolü ve Temizliği
if raw_steam_id:
    STEAM_ID = raw_steam_id.strip() # Boşlukları temizle
else:
    STEAM_ID = None

APP_ID = 730  # CS2
CONTEXT_ID = 2

def get_inventory():
    if not STEAM_ID:
        print("KRİTİK HATA: STEAM_ID değişkeni boş! GitHub Secrets ayarlarını kontrol et.")
        return None
    
    # ID'nin doğru görünüp görünmediğini kontrol edelim (güvenlik için ilk 3 ve son 3 hanesi)
    masked_id = f"{STEAM_ID[:3]}...{STEAM_ID[-3:]}"
    print(f"Hedef ID: {masked_id} (Uzunluk: {len(STEAM_ID)})")

    # Tarayıcı taklidi yapan başlıklar
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://steamcommunity.com/profiles/{STEAM_ID}/inventory",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # YÖNTEM 1: Standart Inventory API
    url_v1 = f"https://steamcommunity.com/inventory/{STEAM_ID}/{APP_ID}/{CONTEXT_ID}?l=turkish&count=5000"
    
    print(f"Yöntem 1 deneniyor (Inventory API)...")
    try:
        response = requests.get(url_v1, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return parse_inventory(response.json())
        else:
            print(f"Yöntem 1 Başarısız. Kod: {response.status_code}")
            if response.status_code == 400:
                print("  -> Hata 400: İstek hatalı. URL veya ID formatı bozuk olabilir.")
    except Exception as e:
        print(f"Yöntem 1 Hatası: {e}")

    # YÖNTEM 2: Eski JSON Endpoint (Yedek)
    print("Yöntem 2 deneniyor (Eski Profil API)...")
    url_v2 = f"https://steamcommunity.com/profiles/{STEAM_ID}/inventory/json/{APP_ID}/{CONTEXT_ID}"
    
    try:
        response = requests.get(url_v2, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return parse_inventory_v2(data)
        
        print(f"Yöntem 2 de başarısız. Kod: {response.status_code}")
        print(f"Dönen Mesaj: {response.text[:100]}...") # Hatanın ilk 100 karakteri
        
    except Exception as e:
        print(f"Yöntem 2 Hatası: {e}")

    return None

def parse_inventory(data):
    """Yeni API formatını işler"""
    if not data or 'assets' not in data:
        return []
    
    descriptions = {f"{d['classid']}_{d['instanceid']}": d for d in data.get('descriptions', [])}
    items = []
    
    for asset in data['assets']:
        key = f"{asset['classid']}_{asset['instanceid']}"
        if key in descriptions:
            desc = descriptions[key]
            if desc.get('marketable') == 1:
                items.append(desc['market_hash_name'])
    return items

def parse_inventory_v2(data):
    """Eski API formatını işler"""
    items = []
    rg_descriptions = data.get("rgDescriptions", {})
    rg_inventory = data.get("rgInventory", {})
    
    for item_id, item_data in rg_inventory.items():
        class_id = item_data.get("classid")
        instance_id = item_data.get("instanceid")
        key = f"{class_id}_{instance_id}"
        
        if key in rg_descriptions:
            desc = rg_descriptions[key]
            if desc.get("marketable") == 1:
                items.append(desc["market_hash_name"])
    return items

def get_price(market_hash_name):
    # Fiyat çekme fonksiyonu (Değişmedi)
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {'country': 'TR', 'currency': 34, 'appid': APP_ID, 'market_hash_name': market_hash_name}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, params=params, headers=headers)
        data = res.json()
        if 'lowest_price' in data: return data['lowest_price']
    except:
        pass
    return "Bulunamadı"

def main():
    items = get_inventory()
    
    if items:
        print(f"\nBAŞARILI! Toplam {len(items)} satılabilir eşya bulundu.\n")
        print(f"{'ITEM ADI':<50} | {'FİYAT'}")
        print("-" * 65)
        
        for item in items[:5]: # Test için ilk 5
            price = get_price(item)
            print(f"{item:<50} | {price}")
            time.sleep(3)
    else:
        print("\nSONUÇ: İki yöntem de başarısız oldu.")
        print("Lütfen GitHub Secrets kısmında 'STEAM_ID'nin başında/sonunda boşluk olmadığından emin ol.")

if __name__ == "__main__":
    main()
