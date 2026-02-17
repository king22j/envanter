import os
import time
import requests
import json

# AYARLAR
STEAM_ID = os.environ.get("STEAM_ID")
if STEAM_ID:
    STEAM_ID = STEAM_ID.strip()

APP_ID = 730  # CS2
CONTEXT_ID = 2
BATCH_SIZE = 100  # Tek seferde istenecek item sayısı (Güvenli sınır: 100)

def get_full_inventory():
    """
    Sayfalama (Pagination) yaparak tüm envanteri çeker.
    """
    if not STEAM_ID:
        print("HATA: STEAM_ID yok!")
        return []

    print(f"ID: {STEAM_ID} için envanter taranıyor (Her istekte {BATCH_SIZE} item)...")
    
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
        
        # Eğer önceki sayfadan devam ediyorsak 'start_assetid' ekle
        if start_assetid:
            url += f"&start_assetid={start_assetid}"
            
        try:
            print(f"Sayfa {page} çekiliyor...", end=" ")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"HATA (Kod: {response.status_code}) - Döngü durduruluyor.")
                break
                
            data = response.json()
            
            if not data or 'assets' not in data:
                print("Veri bitti veya boş.")
                break

            # Varlıkları ve Tanımları İşle
            descriptions = {f"{d['classid']}_{d['instanceid']}": d for d in data.get('descriptions', [])}
            
            current_batch = []
            for asset in data['assets']:
                key = f"{asset['classid']}_{asset['instanceid']}"
                if key in descriptions:
                    desc = descriptions[key]
                    # Sadece satılabilir (marketable) olanları listeye ekle
                    if desc.get('marketable') == 1:
                        current_batch.append(desc['market_hash_name'])
            
            all_items.extend(current_batch)
            print(f"✅ {len(current_batch)} yeni item eklendi.")

            # Sayfalama Kontrolü
            more_items = data.get('more_items', 0) == 1
            start_assetid = data.get('last_assetid')
            
            page += 1
            time.sleep(2) # Steam'i yormamak için kısa bekleme

        except Exception as e:
            print(f"\nBağlantı koptu: {e}")
            break

    return all_items

def get_price(market_hash_name):
    """
    Fiyat çeker. Hata alırsa '0' döner.
    """
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {'country': 'TR', 'currency': 34, 'appid': APP_ID, 'market_hash_name': market_hash_name}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(url, params=params, headers=headers, timeout=5)
        if res.status_code == 429:
            print("(Rate Limit - 30sn Bekleniyor...)")
            time.sleep(30)
            return get_price(market_hash_name) # Tekrar dene
            
        data = res.json()
        if 'lowest_price' in data:
            # Örnek: "15,40 TL" -> 15.40 (Float) çevirimi
            price_str = data['lowest_price'].replace("TL", "").replace(".", "").replace(",", ".").strip()
            return float(price_str), data['lowest_price']
    except:
        pass
    return 0.0, "Yok"

def main():
    items = get_full_inventory()
    
    if not items:
        print("Envanter boş veya çekilemedi.")
        return

    print(f"\nToplam {len(items)} satılabilir item bulundu. Fiyatlandırma başlıyor...\n")
    print("NOT: Çok fazla item varsa bu işlem uzun sürebilir (her item için 3 saniye).")
    
    total_value = 0.0
    report_lines = []

    # Tablo Başlığı
    header = f"{'ITEM ADI':<50} | {'FİYAT'}"
    print(header)
    print("-" * 65)
    report_lines.append(header)
    report_lines.append("-" * 65)

    # ÖNEMLİ: Github Action süresi dolmasın diye örnek olarak ilk 20 itemi tarıyoruz.
    # Tüm envanter için [:20] kısmını silip sadece 'items' yazmalısın.
    for i, item_name in enumerate(items[:20], 1): 
        val, val_str = get_price(item_name)
        total_value += val
        
        line = f"{i}. {item_name:<46} | {val_str}"
        print(line)
        report_lines.append(line)
        
        time.sleep(3) # Steam Market API ban yememek için bekleme

    # Toplam Sonuç
    footer = "\n" + "-" * 65
    summary = f"TOPLAM TAHMİNİ DEĞER: {total_value:.2f} TL"
    
    print(footer)
    print(summary)
    report_lines.append(footer)
    report_lines.append(summary)
    
    # Raporu Dosyaya Kaydet (Github Artifacts için)
    with open("envanter_raporu.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

if __name__ == "__main__":
    main()
