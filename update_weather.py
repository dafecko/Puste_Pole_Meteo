import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import requests

# Konštanty
DEVICE_ID = "8797717349"
URL_VALUES = f"https://app.weathercloud.net/device/values?code={DEVICE_ID}"
CSV_FILE = "meteo_aktualne.csv"


def deg_to_slovak_word(deg):
  """Prevedie stupne na slovný názov svetovej strany v slovenčine."""
  if pd.isna(deg) or deg == "-" or deg == "" or deg is None:
    return "-"

  deg_str = (
      str(deg)
      .replace("°", "")
      .replace("º", "")
      .replace("deg", "")
      .strip()
  )
  try:
    d = float(deg_str)
  except ValueError:
    return deg_str

  d = d % 360

  if 348.75 <= d or d < 11.25:
    return "Sever"
  elif 11.25 <= d < 33.75:
    return "Severo-severovýchod"
  elif 33.75 <= d < 56.25:
    return "Severovýchod"
  elif 56.25 <= d < 78.75:
    return "Východo-severovýchod"
  elif 78.75 <= d < 101.25:
    return "Východ"
  elif 101.25 <= d < 123.75:
    return "Východo-juhovýchod"
  elif 123.75 <= d < 146.25:
    return "Juhovýchod"
  elif 146.25 <= d < 168.75:
    return "Juho-juhovýchod"
  elif 168.75 <= d < 191.25:
    return "Juh"
  elif 191.25 <= d < 213.75:
    return "Juho-juhozápad"
  elif 213.75 <= d < 236.25:
    return "Juhozápad"
  elif 236.25 <= d < 258.75:
    return "Západno-juhozápad"
  elif 258.75 <= d < 281.25:
    return "Západ"
  elif 281.25 <= d < 303.75:
    return "Západno-severozápad"
  elif 303.75 <= d < 326.25:
    return "Severozápad"
  elif 326.25 <= d < 348.75:
    return "Severo-severozápad"
  return "Sever"


def parse_wc_val(val, scale=1.0):
  """Prevedie hodnotu z Weathercloud API na správne číslo."""
  if val is None or val == "":
    return 0.0
  try:
    return round(float(val) * scale, 1)
  except (ValueError, TypeError):
    return 0.0


def scrape_weather():
  print("Sťahujem aktuálne meteorologické údaje z Weathercloud API...")

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

  data_val = {}
  try:
    response = session.get(URL_VALUES, timeout=5)
    if response.status_code == 200:
      data_val = response.json()
    else:
      print(f"⚠️ Weathercloud vrátil status code: {response.status_code}")
  except Exception as e:
    print(f"❌ Chyba pri spájaní s API: {e}")

  if not data_val:
    raise RuntimeError(
        "❌ Nepodarilo sa získať žiadne dáta z Weathercloud API."
    )

  # Weathercloud posiela hodnoty v desatinách (napr. 220 = 22.0°C, 10160 = 1016.0 hPa)
  # Ak posiela celú hodnotu (napr. 22), scale=0.1 ju zmenila na 2.2.
  # Upravujeme podmienkovo:
  
  raw_temp = parse_wc_val(data_val.get("temp"))
  teplota = round(raw_temp / 10.0, 1) if abs(raw_temp) > 50 else raw_temp

  raw_chill = parse_wc_val(data_val.get("chill"))
  chill_val = round(raw_chill / 10.0, 1) if abs(raw_chill) > 50 else raw_chill

  raw_heat = parse_wc_val(data_val.get("heat"))
  heat_val = round(raw_heat / 10.0, 1) if abs(raw_heat) > 50 else raw_heat

  raw_dew = parse_wc_val(data_val.get("dew"))
  dew_val = round(raw_dew / 10.0, 1) if abs(raw_dew) > 50 else raw_dew

  vlhkost = parse_wc_val(data_val.get("hum"))

  # Tlak (ak je okolo 10000, delíme 10, ak je okolo 100, násobíme 10)
  raw_bar = parse_wc_val(data_val.get("bar"))
  if raw_bar > 5000:
    tlak = round(raw_bar / 10.0, 1)
  elif raw_bar < 500:
    tlak = round(raw_bar * 10.0, 1)
  else:
    tlak = raw_bar

  # Zrážky & UV
  raw_rain = parse_wc_val(data_val.get("rain"))
  zrazky = round(raw_rain / 10.0, 1) if raw_rain > 100 else raw_rain
  
  raw_uvi = parse_wc_val(data_val.get("uvi"))
  uv_val = round(raw_uvi / 10.0, 1) if raw_uvi > 20 else raw_uvi

  # Vietor (m/s prepočet na km/h)
  raw_wind = parse_wc_val(data_val.get("wspd"))
  w_ms = raw_wind / 10.0 if raw_wind > 50 else raw_wind
  w_val = round(w_ms * 3.6, 1)

  smer_deg = data_val.get("wdir")
  smer_str = deg_to_slovak_word(smer_deg)

  teraz = datetime.datetime.now(ZoneInfo("Europe/Bratislava"))

  data = [{
      "Dátum": teraz.strftime("%d.%m.%Y"),
      "Čas": teraz.strftime("%H:%M"),
      "Teplota (°C)": teplota,
      "Wind Chill (°C)": chill_val,
      "Heat Index (°C)": heat_val,
      "Rosný bod (°C)": dew_val,
      "Vlhkosť (%)": vlhkost,
      "Tlak (hPa)": tlak,
      "Zrážky (mm)": zrazky,
      "Vietor (km/h)": w_val,
      "Smer vetra": smer_str,
      "UV index": uv_val,
  }]

  df = pd.DataFrame(data)
  df.to_csv(
      CSV_FILE, sep=";", decimal=",", index=False, encoding="utf-8-sig"
  )
  print(
      f"✅ Hotovo! Dáta úspešne uložené do {CSV_FILE} (Teplota: {teplota}°C, Tlak:"
      f" {tlak} hPa)"
  )


if __name__ == "__main__":
  scrape_weather()
