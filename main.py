import os
import time
import requests
import json

# GitHub Secret'tan verileri al
STEAM_ID = os.environ.get("STEAM_ID")
if STEAM_ID:
    STEAM_ID = STEAM_ID.strip()

def test_inventory(app_id, context_id, name):
    print(f"\n--- TEST: {name} (AppID: {app_id}) ---")
    
    # URL Yapısı: count=75 yaparak yükü azaltıyoruz.
    url = f"https://steamcommunity.com/inventory/{STEAM_ID}/{app_id}/{context_id}?l=turkish&count=75"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://steamcommunity.com/profiles/{STEAM_ID}/inventory",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }
    
    print(f"İstek gönderiliyor: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Durum Kodu: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data and 'assets' in data:
                print(f"✅ BAŞARILI! {len(data['assets'])} adet item bulundu.")
                return data['assets']
            elif data and 'total_inventory_count' in data and data['total_inventory_count'] == 0:
                print("⚠️ Envanter erişilebilir ama BOŞ (0 item).")
                return None
            else:
                print("⚠️ Veri geldi ama format beklenmedik.")
                # Hata ayıklama için gelen verinin başını yazdıralım
                print(f"Gelen Veri Özeti: {str(data)[:200]}")
                return None
                
        elif response.status_code == 400:
            print("❌ HATA 400 (Bad Request):")
            print("  1. Bu oyun için envanterin henüz oluşmamış olabilir.")
            print("  2. Steam, GitHub IP'sini engelliyor olabilir.")
            
        elif response.status_code == 403:
            print("❌ HATA 403 (Forbidden): Profil GİZLİ veya IP Banlı.")
            
        elif response.status_code == 429:
            print("❌ HATA 429: Çok hızlı istek atıldı (Rate Limit).")
            
        # Hata varsa içeriği görelim
        if response.status_code != 200:
            try:
                print(f"Steam'den Gelen Mesaj: {response.text}")
            except:
                pass
                
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")
    
    return None

def main():
    if not STEAM_ID:
        print("HATA: STEAM_ID yok!")
        return

    # TEST 1: Steam Topluluk Eşyaları (Kartlar, vb.)
    # Bunu herkesin envanterinde en az 1 tane bir şey vardır diye deniyoruz.
    # Eğer bu çalışırsa ID ve IP sağlam demektir.
    test_inventory(753, 6, "Steam Topluluk (Kartlar)")
    
    time.sleep(2) # Bekle
    
    # TEST 2: CS2 (Counter-Strike 2)
    # Asıl istediğimiz bu.
    assets = test_inventory(730, 2, "CS2 (Counter-Strike)")

    # Eğer CS2 itemleri geldiyse fiyat çekmeyi deneyelim
    if assets:
        print("\n--- Fiyat Kontrolü (İlk 3 İtem) ---")
        # Description verisi olmadığı için sadece assets sayısını doğruladık
        # Gerçek kodda description ile birleştirmek gerekir ama şu an sorunu çözmeye odaklıyız.
        print("Envanter bağlantısı doğrulandı. Tam kodu çalıştırmak için hazırsın.")

if __name__ == "__main__":
    main()
