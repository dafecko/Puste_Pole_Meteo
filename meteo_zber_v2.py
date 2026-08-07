import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

# --- KONŠTANTY ---
# Tvoje presné Device ID z Weathercloud (z URL: d8797717349)
DEVICE_ID = "8797717349"
CSV_FILE = "meteo_puste_pole_v2.csv"
MS_TO_KMH = 3.6  # Prepočet m/s na km/h (ak Weathercloud posiela m/s)


def to_sk_num(val, scale=1.0):
  """Prevedie číslo na slovenský formát s čiarkou.

  Ak je hodnota None, vráti '0,0'.
  """
  if val is None:
    return "0,0"
  try:
    num = float(val) * scale
    return f"{num:.1f}".replace(".", ",")
  except (ValueError, TypeError):
    return "0,0"


def main():
  now = datetime.now(ZoneInfo("Europe/Bratislava"))
  datum_str = now.strftime("%d.%m.%Y")
  cas_str = now.strftime("%H:%M")

  print(
      f"[{datum_str} {cas_str}] Pripájam sa na Weathercloud pre denný export"
      f" (Device: {DEVICE_ID})..."
  )

  session = requests.Session()
  session.headers.update({
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
      ),
      "Accept": "application/json, text/javascript, */*; q=0.01",
      "Accept-Language": "sk-SK,sk;q=0.9,en-US;q=0.8,en;q=0.7",
      "X-Requested-With": "XMLHttpRequest",
      "Referer": f"https://app.weathercloud.net/d{DEVICE_ID}",
      "Connection": "close",  # Ukončí spojenie okamžite, zabráni viseniu na GitHube
  })

  url_values = f"https://app.weathercloud.net/device/values?code={DEVICE_ID}"
  url_stats = f"https://app.weathercloud.net/device/stats?code={DEVICE_ID}"

  data_val, data_stats = {}, {}

  # 1. Stiahnutie aktuálnych hodnôt (Values) s tvrdým limitom 5s
  try:
    r1 = session.get(url_values, timeout=5)
    if r1.status_code == 200:
      data_val = r1.json()
    else:
      print(f"⚠️ Weathercloud values vrátil status code: {r1.status_code}")
  except Exception as e:
    print(f"❌ Chyba pri spájaní s Weathercloud values: {e}")

  # 2. Stiahnutie denných štatistík (Stats) s tvrdým limitom 5s
  try:
    r2 = session.get(url_stats, timeout=5)
    if r2.status_code == 200:
      data_stats = r2.json()
    else:
      print(f"⚠️ Weathercloud stats vrátil status code: {r2.status_code}")
  except Exception as e:
    print(f"❌ Chyba pri spájaní s Weathercloud stats: {e}")

  # KONTROLA: Ak Weathercloud neposlal žiadne dáta, vyhodiť chybu (aby zber nečakal 1 hodinu)
  if not data_val and not data_stats:
    raise RuntimeError(
        "❌ Nepodarilo sa získať žiadne dáta z Weathercloud (možné blokovanie IP"
        " adresy GitHubu alebo neplatné Device ID)."
    )

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

  # PRESNE 9 STĹPCOV PODĽA EXCEL TABUĽKY:
  row = [
      datum_str,  # 1. Dátum
      cas_str,  # 2. Čas
      to_sk_num(temp_max),  # 3. Teplota Max (°C)
      to_sk_num(temp_avg),  # 4. Teplota Priemer (°C)
      to_sk_num(temp_min),  # 5. Teplota Min (°C)
      to_sk_num(wind_max, scale=MS_TO_KMH),  # 6. Vietor Max (km/h)
      to_sk_num(wind_avg, scale=MS_TO_KMH),  # 7. Vietor Priemer (km/h)
      to_sk_num(wind_min),  # 8. Vietor Min (km/h)
      to_sk_num(rain_total),  # 9. Zrážky (mm)
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


if __name__ == "__main__":
  main()
