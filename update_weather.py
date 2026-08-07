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


def clean_val(val, scale=1.0):
  """Vyčistí hodnotu na číslo a vynásobí ju skálovacím koeficientom."""
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

  # Extrakcia hodnôt priamo z API
  teplota = clean_val(data_val.get("temp"), scale=0.1)
  chill_val = clean_val(data_val.get("chill"), scale=0.1)
  heat_val = clean_val(data_val.get("heat"), scale=0.1)
  dew_val = clean_val(data_val.get("dew"), scale=0.1)
  vlhkost = clean_val(data_val.get("hum"))
  tlak = clean_val(data_val.get("bar"), scale=0.1)
  zrazky = clean_val(data_val.get("rain"), scale=0.1)
  uv_val = clean_val(data_val.get("uvi"))

  # Vietor (Weathercloud posiela m/s * 10, prepočet na km/h)
  w_val_ms = clean_val(data_val.get("wspd"), scale=0.1)
  w_val = round(w_val_ms * 3.6, 1)

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
      f"✅ Hotovo! Dáta úspešne uložené do {CSV_FILE} (Tlak: {tlak} hPa, Smer:"
      f" {smer_str}, Teplota: {teplota}°C)"
  )


if __name__ == "__main__":
  scrape_weather()
