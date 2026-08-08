import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

# --- KONŠTANTY ---
DEVICE_ID = "8797717349"
CSV_FILE = "meteo_puste_pole_v2.csv"
MS_TO_KMH = 3.6  # Prepočet m/s na km/h


def parse_wc_val(val):
  """Prevedie hodnotu z Weathercloud API na číslo.

  Vráti None ak hodnota chýba.
  """
  if val is None or val == "":
    return None
  try:
    return float(val)
  except (ValueError, TypeError):
    return None


def format_sk_num(val, scale=1.0, is_temp=False):
  """Formátuje číslo pre slovenský Excel s čiarkou.

  Weathercloud posiela niektoré hodnoty v desatinách (napr. 220 pre 22.0°C).
  """
  if val is None:
    return "-"

  num = float(val)

  # Ak Weathercloud posiela hodnotu v desatinách (napr. teplota 220 -> 22.0)
  if is_temp and abs(num) > 50:
    num = num / 10.0
  elif not is_temp and num > 100:
    num = num / 10.0

  num = num * scale
  return f"{num:.1f}".replace(".", ",")


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
      "X-Requested-With": "XMLHttpRequest",
      "Referer": f"https://app.weathercloud.net/d{DEVICE_ID}",
      "Connection": "close",
  })

  url_values = f"https://app.weathercloud.net/device/values?code={DEVICE_ID}"
  url_stats = f"https://app.weathercloud.net/device/stats?code={DEVICE_ID}"

  data_val, data_stats = {}, {}

  try:
    r1 = session.get(url_values, timeout=5)
    if r1.status_code == 200:
      data_val = r1.json()
  except Exception as e:
    print(f"⚠️ Values chyba: {e}")

  try:
    r2 = session.get(url_stats, timeout=5)
    if r2.status_code == 200:
      data_stats = r2.json()
  except Exception as e:
    print(f"⚠️ Stats chyba: {e}")

  if not data_val and not data_stats:
    raise RuntimeError("❌ Nepodarilo sa získať žiadne dáta z Weathercloud API.")

  # Teploty
  temp_max = parse_wc_val(
      data_stats.get("temp_day_max") or data_stats.get("temp_max")
  )
  temp_avg = parse_wc_val(data_val.get("temp"))
  temp_min = parse_wc_val(
      data_stats.get("temp_day_min") or data_stats.get("temp_min")
  )

  # Vietor
  raw_w_max = parse_wc_val(
      data_stats.get("wspd_day_max")
      or data_stats.get("wgust")
      or data_stats.get("wspd_max")
      or data_val.get("wspd")
  )
  raw_w_avg = parse_wc_val(
      data_val.get("wspdavg")
      or data_val.get("wspd")
      or data_stats.get("wspdavg_current")
  )

  # Ak je vietor v desatinách m/s, upravíme na m/s
  w_max_ms = (
      (raw_w_max / 10.0)
      if (raw_w_max is not None and raw_w_max > 50)
      else raw_w_max
  )
  w_avg_ms = (
      (raw_w_avg / 10.0)
      if (raw_w_avg is not None and raw_w_avg > 50)
      else raw_w_avg
  )

  # Zrážky
  raw_rain = parse_wc_val(
      data_stats.get("rain_day_total")
      or data_stats.get("rain_day_max")
      or data_val.get("rain")
  )
  rain_val = (
      (raw_rain / 10.0)
      if (raw_rain is not None and raw_rain > 100)
      else raw_rain
  )

  # 9 stĺpcov
  row = [
      datum_str,
      cas_str,
      format_sk_num(temp_max, is_temp=True),
      format_sk_num(temp_avg, is_temp=True),
      format_sk_num(temp_min, is_temp=True),
      format_sk_num(w_max_ms, scale=MS_TO_KMH),
      format_sk_num(w_avg_ms, scale=MS_TO_KMH),
      "0,0",  # Vietor Min
      format_sk_num(rain_val),
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
