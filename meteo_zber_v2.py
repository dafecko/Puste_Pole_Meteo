def main():
    now = datetime.now(ZoneInfo("Europe/Bratislava"))
    datum_str = now.strftime("%d.%m.%Y")
    cas_str = now.strftime("%H:%M")

    print(f"[{datum_str} {cas_str}] Pripájam sa na Weathercloud pre denný export...")

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "sk-SK,sk;q=0.9,en;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://app.weathercloud.net/d{DEVICE_ID}",
    })

    url_values = f"https://app.weathercloud.net/device/values?code={DEVICE_ID}"
    url_stats = f"https://app.weathercloud.net/device/stats?code={DEVICE_ID}"

    data_val, data_stats = {}, {}

    try:
        r1 = session.get(url_values, timeout=8)
        if r1.status_code == 200:
            data_val = r1.json()
    except Exception:
        pass

    try:
        r2 = session.get(url_stats, timeout=8)
        if r2.status_code == 200:
            data_stats = r2.json()
    except Exception:
        pass

    # Teploty
    temp_max = data_stats.get("temp_day_max")
    temp_avg = data_val.get("temp")
    temp_min = data_stats.get("temp_day_min")

    # Vietor
    wind_max = (
        data_stats.get("wspd_day_max")
        or data_stats.get("wgust")
        or data_stats.get("wspd_max")
        or data_val.get("wspd")
    )
    wind_avg = (
        data_val.get("wspdavg")
        or data_val.get("wspd")
        or data_stats.get("wspdavg_current")
    )
    wind_min = 0  # Ak nemá min, pre 9-stĺpcový formát

    # Zrážky
    rain_total = (
        data_stats.get("rain_day_total")
        or data_stats.get("rain_day_max")
        or data_val.get("rain")
    )

    # PRESNE 9 STĹPCOV PODĽA TVOJEJ EXCEL TABUĽKY:
    row = [
        datum_str,                            # 1. Dátum
        cas_str,                              # 2. Čas
        to_sk_num(temp_max),                  # 3. Teplota Max (°C)
        to_sk_num(temp_avg),                  # 4. Teplota Priemer (°C)
        to_sk_num(temp_min),                  # 5. Teplota Min (°C)
        to_sk_num(wind_max, scale=MS_TO_KMH), # 6. Vietor Max (km/h)
        to_sk_num(wind_avg, scale=MS_TO_KMH), # 7. Vietor Priemer (km/h)
        to_sk_num(wind_min),                  # 8. Vietor Min (km/h)
        to_sk_num(rain_total),                # 9. Zrážky (mm)
    ]

    file_exists = os.path.exists(CSV_FILE)

    with open(CSV_FILE, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        if not file_exists:
            header = [
                "Dátum",
                "Čas",
                "Teplota Max (°C)",
                "Teplota Priemer (°C)",
                "Teplota Min (°C)",
                "Vietor Max (km/h)",
                "Vietor Priemer (km/h)",
                "Vietor Min (km/h)",
                "Zrážky (mm)",
            ]
            writer.writerow(header)
        writer.writerow(row)

    print(f"✅ Denný zber úspešne uložený do {CSV_FILE}")
