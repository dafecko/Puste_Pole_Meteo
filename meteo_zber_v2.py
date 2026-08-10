import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

# ==========================================
# NASTAVENIA STANICE
# ==========================================
DEVICE_ID = "8797717349"
CSV_FILE = "meteo_puste_pole_v2.csv"
MS_TO_KMH = 3.6


def to_sk_num(value, scale=1.0, decimals=1):
  """Prevedie číslo alebo zoznam [timestamp, hodnota] na slovenský formát."""
  if value is None or value == "":
    return ""

  if isinstance(value, list) and len(value) >= 2:
    value = value[1]

  try:
    val_float = float(value)
    if isinstance(value, int) and abs(value) >= 100:
      val_float = val_float / 10.0
    elif isinstance(value, str) and value.isdigit() and len(value) >= 3:
      val_float = float(value) / 10.0

    val_float = val_float * scale
    return f"{val_float:.{decimals}f}".replace(".", ",")
  except (ValueError, TypeError):
    return str(value)


def main():
  now = datetime.now(ZoneInfo("Europe/Bratislava"))
  datum_str = now.strftime("%d.%m.%Y")
  cas_str = now.strftime("%H:%M")

  print(
      f"[{datum_str} {cas_str}] Pripájam sa na Weathercloud pre denný export..."
  )

  session = requests.Session()
  session.headers.update({
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
      ),
      "Accept": "application/json, text/javascript, */*; q=0.01",
      "Accept-Language": "sk-SK,sk;q=0.9,en;q=0.8",
      "X-Requested-With": "XMLHttpRequest",
      "Referer": f"https://app.weathercloud.net/d{DEVICE_ID}",
      "Connection": "close",
  })

  url_values = f"https://app.weathercloud.net/device/values?code={DEVICE_ID}"
  url_stats = f"https://app.weathercloud.net/device/stats?code={DEVICE_ID}"

  data_val, data_stats = {}, {}

  try:
    r1 = session.get(url_values, timeout=8)
    if r1.status_code == 200:
      data_val = r1.json()
  except Exception as e:
    print(f"⚠️ Values chyba: {e}")

  try:
    r2 = session.get(url_stats, timeout=8)
    if r2.status_code == 200:
      data_stats = r2.json()
  except Exception as e:
    print(f"⚠️ Stats chyba: {e}")

  # Teploty
  temp_max = data_stats.get("temp_day_max")
  temp_min = data_stats.get("temp_day_min")
  temp_avg = data_val.get("temp")

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
  wind_min = data_stats.get("wspd_day_min") or data_stats.get("wspd_min")

  # Zrážky
  rain_total = (
      data_stats.get("rain_day_total")
      or data_stats.get("rain_day_max")
      or data_val.get("rain")
  )

  row = [
      datum_str,
      cas_str,
      to_sk_num(temp_max),
      to_sk_num(temp_avg),
      to_sk_num(temp_min),
      to_sk_num(wind_max, scale=MS_TO_KMH),
      to_sk_num(wind_avg, scale=MS_TO_KMH),
      to_sk_num(wind_min, scale=MS_TO_KMH),
      to_sk_num(rain_total),
  ]

  csv_headers = [
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

  file_exists = os.path.exists(CSV_FILE)

  with open(CSV_FILE, mode="a", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f, delimiter=";")
    if not file_exists:
      writer.writerow(csv_headers)

    writer.writerow(row)

  print(f"✅ Uložené: Max={to_sk_num(temp_max)}, Min={to_sk_num(temp_min)}")


if __name__ == "__main__":
  main()
