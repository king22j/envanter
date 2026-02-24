import os
import time
import requests
import urllib.parse
from collections import Counter

# =====================
# AYARLAR
# =====================
STEAM_ID = os.environ.get("STEAM_ID")
if STEAM_ID:
    STEAM_ID = STEAM_ID.strip()

APP_ID = 730
CONTEXT_ID = 2


# =====================
# ENVANTER ÇEKME
# =====================
def get_full_inventory():
    if not STEAM_ID:
        print("HATA: STEAM_ID yok!")
        return []

    print(f"--- Envanter Taranıyor: {STEAM_ID} ---")

    all_items = []
    start_assetid = None
    more_items = True

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    while more_items:
        url = f"https://steamcommunity.com/inventory/{STEAM_ID}/{APP_ID}/{CONTEXT_ID}?l=english&count=100"
        if start_assetid:
            url += f"&start_assetid={start_assetid}"

        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                break

            data = res.json()
            if not data or "assets" not in data:
                break

            descriptions = {
                f"{d['classid']}_{d['instanceid']}": d
                for d in data.get("descriptions", [])
            }

            for asset in data["assets"]:
                key = f"{asset['classid']}_{asset['instanceid']}"
                if key in descriptions:
                    desc = descriptions[key]
                    if desc.get("marketable") == 1:
                        all_items.append(desc["market_hash_name"])

            more_items = data.get("more_items", 0) == 1
            start_assetid = data.get("last_assetid")

            time.sleep(0.5)

        except Exception:
            break

    return all_items


# =====================
# STEAM MARKET USD FİYAT
# =====================
def get_market_price_usd(item_name):
    encoded_name = urllib.parse.quote(item_name)

    url = (
        f"https://steamcommunity.com/market/priceoverview/"
        f"?appid=730"
        f"&currency=1"   # 1 = USD
        f"&market_hash_name={encoded_name}"
    )

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        if data.get("success") and "lowest_price" in data:
            price_str = data["lowest_price"]

            # "$12.34" -> 12.34
            price_str = (
                price_str.replace("$", "")
                .replace(",", "")
                .strip()
            )

            return float(price_str)

    except Exception:
        pass

    return 0.0


# =====================
# MAIN
# =====================
def main():
    items = get_full_inventory()
    if not items:
        print("Envanter boş veya gizli.")
        return

    item_counts = Counter(items)
    unique_items = list(item_counts.keys())

    print(f"\n✅ {len(items)} item bulundu.")
    print(f"⚡ Fiyatlandırma başlıyor ({len(unique_items)} çeşit)...\n")

    total_value = 0.0
    found_count = 0

    print(f"{'ADET':<5} | {'ITEM ADI':<50} | {'BİRİM ($)':<12} | {'TOPLAM ($)'}")
    print("-" * 90)

    for name in unique_items:
        count = item_counts[name]

        unit_price = get_market_price_usd(name)
        if unit_price > 0:
            found_count += 1

        line_total = unit_price * count
        total_value += line_total

        price_display = f"{unit_price:.2f}" if unit_price > 0 else "---"
        total_display = f"{line_total:.2f}" if line_total > 0 else "---"

        print(f"{count:<5} | {name[:50]:<50} | {price_display:<12} | {total_display}")

        time.sleep(1)  # rate limit yememek için

    print("-" * 90)
    print(f"💰 GENEL TOPLAM DEĞER: {total_value:.2f} $")
    print(f"📊 {len(unique_items)} çeşit itemden {found_count} tanesinin fiyatı bulundu.")


if __name__ == "__main__":
    main()
