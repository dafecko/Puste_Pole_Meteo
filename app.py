import datetime
import os
from zoneinfo import ZoneInfo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# --- NASTAVENIE STRÁNCY ---
st.set_page_config(
    page_title="Meteo Web Dashboard - Pusté Pole",
    page_icon="🌤️",
    layout="wide",
)

# Vynútenie načítania čerstvých dát hneď pri prvom otvorení aplikácie
if "initialized" not in st.session_state:
  st.session_state.initialized = True
  st.rerun()

# Automatické obnovenie stránky každých 5 minút (300 000 ms)
count = st_autorefresh(interval=300000, limit=None, key="meteo_autorefresh")

# --- VLASTNÉ CSS ŠTÝLY ---
st.markdown(
    """
    <style>
    .weather-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(150, 150, 150, 0.18);
        border-radius: 14px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
        padding: 18px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        margin-bottom: 10px;
        height: 265px;
        justify-content: space-between;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .weather-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }

    /* Horizontálny scroll pás pre 24h predpoveď */
    .hourly-scroll-strip {
        display: flex;
        overflow-x: auto;
        gap: 10px;
        padding: 8px 4px 14px 4px;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
    }
    .hourly-scroll-strip::-webkit-scrollbar {
        height: 5px;
    }
    .hourly-scroll-strip::-webkit-scrollbar-thumb {
        background: rgba(150, 150, 150, 0.35);
        border-radius: 10px;
    }
    .hourly-pill-card {
        min-width: 82px;
        max-width: 82px;
        background: var(--secondary-background-color);
        border: 1px solid rgba(150, 150, 150, 0.18);
        border-radius: 16px;
        padding: 12px 6px;
        text-align: center;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    .hourly-pill-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 14px rgba(0,0,0,0.08);
        border-color: rgba(230, 126, 34, 0.4);
    }
    .hourly-pill-card.current-hour {
        background: linear-gradient(180deg, rgba(230, 126, 34, 0.12) 0%, var(--secondary-background-color) 100%);
        border: 1.5px solid #e67e22;
    }

    .card-title {
        font-size: 0.95em;
        font-weight: 700;
        opacity: 0.85;
        margin-bottom: 5px;
        height: 35px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .main-value {
        font-size: 1.6em;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-value-tooltip {
        font-size: 1.6em;
        font-weight: 800;
        margin: 0;
        cursor: help;
        letter-spacing: -0.5px;
    }
    .sub-value {
        font-size: 0.82em;
        opacity: 0.75;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Vertikálne stupnice */
    .bar-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin: 5px auto;
        height: 100px;
    }
    .bar-scale {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100px;
        font-size: 8px;
        font-weight: 700;
        opacity: 0.6;
        text-align: right;
    }
    .thermometer-box, .pressure-box, .rain-box {
        height: 100px;
        width: 16px;
        background: rgba(128, 128, 128, 0.15);
        border-radius: 8px;
        position: relative;
        overflow: hidden;
    }
    .thermometer-fill {
        position: absolute;
        bottom: 0;
        width: 100%;
        background: linear-gradient(to top, #3498db, #2ecc71, #f1c40f, #e74c3c);
        transition: height 0.5s ease;
    }
    .pressure-fill {
        position: absolute;
        bottom: 0;
        width: 100%;
        background: linear-gradient(to top, #3498db, #9b59b6);
        transition: height 0.5s ease;
    }
    .rain-fill {
        position: absolute;
        bottom: 0;
        width: 100%;
        background: linear-gradient(to top, #74b9ff, #0984e3);
        transition: height 0.5s ease;
    }

    /* Kruhové ciferníky */
    .gauge-circle {
        width: 110px;
        height: 110px;
        border-radius: 50%;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 5px auto;
        box-shadow: 0 3px 8px rgba(0,0,0,0.08);
    }
    .gauge-hum {
        background: conic-gradient(from 225deg, #e67e22 0deg, #2ecc71 135deg, #3498db 270deg, transparent 270deg);
    }
    .gauge-wind {
        background: conic-gradient(from 225deg, #2ecc71 0deg, #f1c40f 100deg, #e67e22 180deg, #e74c3c 270deg, transparent 270deg);
    }
    .gauge-uv {
        background: conic-gradient(from 225deg, #2ecc71 0deg 67.5deg, #f1c40f 67.5deg 135deg, #e67e22 135deg 180deg, #e74c3c 180deg 247.5deg, #9b59b6 247.5deg 270deg, transparent 270deg);
    }
    .gauge-inner-cover {
        position: absolute;
        width: 82px;
        height: 82px;
        background-color: var(--card-bg, #ffffff);
        border-radius: 50%;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.06);
    }
    .gauge-needle {
        position: absolute;
        bottom: 50%;
        left: 50%;
        width: 3px;
        height: 35px;
        background: #2c3e50;
        transform-origin: bottom center;
        transform: translateX(-50%) rotate(0deg);
        z-index: 3;
        border-radius: 2px;
    }
    .gauge-center-dot {
        position: absolute;
        width: 9px;
        height: 9px;
        background: #2c3e50;
        border-radius: 50%;
        z-index: 4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    .scale-val {
        position: absolute;
        font-size: 8px;
        font-weight: 700;
        opacity: 0.7;
        z-index: 5;
    }
    .s-0  { bottom: 16px; left: 14px; }
    .s-20 { top: 40px; left: 10px; }
    .s-40 { top: 12px; left: 30px; }
    .s-60 { top: 12px; right: 30px; }
    .s-80 { top: 40px; right: 10px; }
    .s-100 { bottom: 16px; right: 14px; }
    .scale-unit {
        position: absolute;
        bottom: 15px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 8px;
        font-weight: 700;
        opacity: 0.6;
        z-index: 5;
    }

    .meteo-alert-banner {
        padding: 14px 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    .alert-icon { font-size: 2.2em; line-height: 1; }
    .alert-title { font-weight: bold; font-size: 1.05em; margin-bottom: 2px; }
    .alert-desc { font-size: 0.88em; opacity: 0.95; }

    /* Výrazný ovládací panel pre filter obdobia */
    div[data-testid="stVerticalBlock"]:has(> div > [data-testid="stRadio"]) {
        background: linear-gradient(180deg, rgba(52, 152, 219, 0.05) 0%, var(--secondary-background-color) 100%);
        border: 1.5px solid rgba(52, 152, 219, 0.35);
        border-left: 6px solid #2980b9;
        border-radius: 14px;
        padding: 14px 20px 10px 20px;
        margin-bottom: 22px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
    }

    .stat-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(150, 150, 150, 0.18);
        border-radius: 12px;
        padding: 14px 8px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 110px;
        transition: transform 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
    }
    .stat-label { 
        font-size: 0.74em; 
        font-weight: 700; 
        opacity: 0.75; 
        text-transform: uppercase; 
        letter-spacing: 0.3px;
    }
    .stat-val { 
        font-size: 1.45em; 
        font-weight: 800; 
        margin: 3px 0; 
    }
    .stat-delta { 
        font-size: 0.72em; 
        font-weight: 700; 
        border-radius: 5px; 
        padding: 2px 6px; 
        display: inline-block; 
    }
    .delta-up { background: rgba(46, 204, 113, 0.15); color: #27ae60; }
    .delta-down { background: rgba(231, 76, 60, 0.15); color: #e74c3c; }

    @media (max-width: 768px) {
        .weather-card { height: auto; margin-bottom: 15px; }
        .main-value, .main-value-tooltip { font-size: 1.4em; }
        .hourly-pill-card { min-width: 76px; max-width: 76px; padding: 10px 4px; }
        .stat-card { height: auto; margin-bottom: 10px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- KONŠTANTY A SÚBORY ---
CSV_FILE = "meteo_puste_pole_v2.csv"
CSV_AKTUALNE = "meteo_aktualne.csv"
LAT, LON = 49.215, 20.900


# --- POMOCNÉ FUNKCIE ---
def deg_to_cardinal(deg):
  if pd.isna(deg) or deg == "-" or deg == "":
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
    return str(deg).upper()
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


@st.cache_data(ttl=120)
def load_data():
  if not os.path.exists(CSV_FILE):
    return None
  try:
    df = pd.read_csv(
        CSV_FILE, sep=";", decimal=",", on_bad_lines="skip", engine="python"
    )
  except Exception:
    try:
      df = pd.read_csv(
          CSV_FILE, sep=",", decimal=".", on_bad_lines="skip", engine="python"
      )
    except Exception:
      return None

  col_datum = next(
      (c for c in df.columns if "dátum" in c.lower() or "datum" in c.lower()),
      None,
  )
  col_cas = next(
      (c for c in df.columns if "čas" in c.lower() or "cas" in c.lower()), None
  )
  if not col_datum or not col_cas:
    return df

  df["DateTime"] = pd.to_datetime(
      df[col_datum].astype(str) + " " + df[col_cas].astype(str),
      dayfirst=True,
      errors="coerce",
  )
  df = df.dropna(subset=["DateTime"])

  # Chronologické triedenie s ponechaním posledného záznamu dňa
  df = df.sort_values("DateTime")
  df = df.drop_duplicates(subset=[col_datum], keep="last")

  for col in df.columns:
    if col not in [col_datum, col_cas, "DateTime", "Smer vetra"]:
      df[col] = pd.to_numeric(
          df[col].astype(str).str.replace(",", "."), errors="coerce"
      )
  return df


@st.cache_data(ttl=1800)
def fetch_weather_api_data(lat, lon):
  endpoints = [
      (
          f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
          "&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m"
          "&hourly=temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m"
          "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,sunrise,sunset"
          "&forecast_days=7&timezone=auto"
      ),
      (
          f"https://archive-api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
          "&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m"
          "&hourly=temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m"
          "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,sunrise,sunset"
          "&forecast_days=7&timezone=auto"
      ),
  ]

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept": "application/json",
  }

  for url in endpoints:
    try:
      response = requests.get(url, headers=headers, timeout=8)
      if response.status_code == 200:
        data = response.json()
        return (
            data.get("current", {}),
            data.get("daily", {}),
            data.get("hourly", {}),
        )
    except Exception:
      continue

  return {}, {}, {}


def get_weather_icon(code):
  try:
    code = int(code)
  except:
    return "🌤️"
  if code == 0:
    return "☀️"
  elif code in [1, 2]:
    return "⛅"
  elif code == 3:
    return "☁️"
  elif code in [45, 48]:
    return "🌫️"
  elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
    return "🌧️"
  elif code in [71, 73, 75, 77, 85, 86]:
    return "❄️"
  elif code in [95, 96, 99]:
    return "⛈️"
  else:
    return "🌤️"


def get_weather_description(code):
  try:
    code = int(code)
  except:
    return "Oblačno"
  if code == 0:
    return "Jasno"
  elif code in [1, 2]:
    return "Polooblačno"
  elif code == 3:
    return "Oblačno"
  elif code in [45, 48]:
    return "Hmla"
  elif code in [51, 53, 55, 56, 57]:
    return "Mrholenie"
  elif code in [61, 63, 65, 66, 67]:
    return "Dážď"
  elif code in [71, 73, 75, 77]:
    return "Sneh"
  elif code in [80, 81, 82]:
    return "Prehánky"
  elif code in [85, 86]:
    return "Snehové prehánky"
  elif code in [95, 96, 99]:
    return "Búrka"
  else:
    return "Oblačno"


def get_moon_phase_info():
  today = datetime.date.today()
  known_new_moon = datetime.date(2000, 1, 6)
  diff = (today - known_new_moon).days
  synodic_month = 29.5305877057
  phase = (diff % synodic_month) / synodic_month

  if phase < 0.03 or phase > 0.97:
    return "🌑 Nov"
  elif phase < 0.22:
    return "🌒 Dorastajúci kosák"
  elif phase < 0.28:
    return "🌓 Prvá štvrť"
  elif phase < 0.47:
    return "🌔 Dorastajúci Mesiac"
  elif phase < 0.53:
    return "🌕 Spln"
  elif phase < 0.72:
    return "🌖 Ubúdajúci Mesiac"
  elif phase < 0.78:
    return "🌗 Posledná štvrť"
  else:
    return "🌘 Ubúdajúci kosák"


# --- HLAVIČKA A INFO O STANICI ---
st.title("🌤️ Meteorologický Web Dashboard - Pusté Pole")

st.markdown(
    """
    <div style="background-color: var(--secondary-background-color); padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; font-size: 0.9em; display: flex; justify-content: space-between; flex-wrap: wrap;">
        <div>📍 <b>Lokalita:</b> Pusté Pole</div>
        <div>🚀 <b>Oficiálne spustená od:</b> 1. 7. 2026</div>
    </div>
    """,
    unsafe_allow_html=True,
)

current_api_data, forecast_data, hourly_api_data = fetch_weather_api_data(
    LAT, LON
)
curr_code = current_api_data.get("weather_code", 0) if current_api_data else 0
curr_icon = get_weather_icon(curr_code)
curr_desc = get_weather_description(curr_code)

sunrise_str, sunset_str = "--:--", "--:--"
if (
    forecast_data
    and "sunrise" in forecast_data
    and len(forecast_data["sunrise"]) > 0
):
  try:
    sunrise_str = forecast_data["sunrise"][0].split("T")[1][:5]
    sunset_str = forecast_data["sunset"][0].split("T")[1][:5]
  except:
    pass
moon_phase_str = get_moon_phase_info()

# Načítanie lokálnych aktuálnych dát
t_val, chill_val, heat_val, dew_val, h_val, p_val, w_val, r_val, uv_val = (
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
)
w_cardinal = "-"
datum_str, cas_str = "", ""
is_fallback = False

if os.path.exists(CSV_AKTUALNE):
  try:
    try:
      df_akt = pd.read_csv(
          CSV_AKTUALNE, sep=";", decimal=",", on_bad_lines="skip"
      )
    except:
      df_akt = pd.read_csv(
          CSV_AKTUALNE, sep=",", decimal=".", on_bad_lines="skip"
      )

    if not df_akt.empty:
      akt = df_akt.iloc[0]
      datum_str = str(akt.get("Dátum", akt.get("datum", "")))
      cas_str = str(akt.get("Čas", akt.get("cas", "")))

      def get_val(df_row, keywords):
        for k in keywords:
          for col in df_row.index:
            if k.lower() in str(col).lower():
              val = df_row[col]
              try:
                return float(str(val).replace(",", "."))
              except:
                return val
        return 0.0

      def get_str_val(df_row, keywords):
        for k in keywords:
          for col in df_row.index:
            if k.lower() in str(col).lower():
              return str(df_row[col])
        return "-"

      t_val = get_val(akt, ["teplota", "temp"])
      chill_val = get_val(akt, ["chill", "wind chill"])
      heat_val = get_val(akt, ["heat", "heat index"])
      dew_val = get_val(akt, ["dew", "rosný"])
      h_val = get_val(akt, ["vlhkosť", "vlhkost", "hum"])
      p_val = get_val(akt, ["tlak", "bar", "pressure"])
      w_val = get_val(akt, ["vietor", "wind", "wspd"])
      w_dir_raw = get_str_val(akt, ["smer", "wdir"])
      r_val = get_val(akt, ["zrážky", "zrazky", "rain"])
      uv_val = get_val(akt, ["uv", "uvi"])
      w_cardinal = deg_to_cardinal(w_dir_raw)
  except Exception as e:
    st.error(f"Chyba pri spracovaní CSV: {e}")

if p_val == 0.0 and h_val == 0.0:
  is_fallback = True
  if current_api_data:
    t_val = current_api_data.get("temperature_2m", 0.0)
    h_val = current_api_data.get("relative_humidity_2m", 50.0)
    w_val = current_api_data.get("wind_speed_10m", 0.0)
    r_val = current_api_data.get("precipitation", 0.0)
    p_val = 1013.0
    uv_val = 0.0
    chill_val = t_val
    heat_val = t_val
    dew_val = t_val
    w_cardinal = "Model"

if t_val <= 10.0 and chill_val != 0:
  pocitova_val = chill_val
elif t_val >= 25.0 and heat_val != 0:
  pocitova_val = heat_val
else:
  pocitova_val = (
      heat_val
      if (heat_val != 0 and heat_val != t_val)
      else (chill_val if (chill_val != 0 and chill_val != t_val) else t_val)
  )

# --- HLAVNÉ ZÁLOŽKY ---
tab_aktualne, tab_radar, tab_historia = st.tabs([
    "🌤️ Aktuálne počasie & Predpoveď",
    "📡 Živý meteoradar",
    "📊 História & Rekordy stanice",
])

with tab_aktualne:
  if datum_str or cas_str:
    st.caption(f"📅 Posledná aktualizácia zo stanice: {datum_str} o {cas_str}")

  active_warnings = []
  if is_fallback:
    active_warnings.append({
        "title": "Dočasný výpadok dát zo stanice",
        "desc": (
            "Lokálna stanica momentálne odoslala prázdne/chybné údaje. Budíky"
            " aktuálne zobrazujú záložné dáta z online meteorologického"
            " modelu."
        ),
        "color": "linear-gradient(135deg, #f39c12, #d35400)",
        "icon": "📡",
    })
  if t_val <= 3.0 and not (is_fallback and t_val == 0.0):
    active_warnings.append({
        "title": "Pozor: Hrozí prízemný mráz!",
        "desc": (
            f"Teplota klesla na {t_val:.1f} °C. Hrozí riziko poškodenia"
            " vegetácie."
        ),
        "color": "linear-gradient(135deg, #2980b9, #2c3e50)",
        "icon": "❄️",
    })
  if curr_code in [95, 96, 99]:
    active_warnings.append({
        "title": "Výstraha pred búrkou!",
        "desc": "V oblasti je detekovaná búrková činnosť. Zvýšte opatrnosť.",
        "color": "linear-gradient(135deg, #c0392b, #e74c3c)",
        "icon": "⚡",
    })
  if uv_val >= 8.0:
    active_warnings.append({
        "title": "Extrémny UV index!",
        "desc": (
            f"Aktuálna hodnota UV indexu je {uv_val:.1f}. Obmedzte pobyt na"
            " slnku bez ochrany."
        ),
        "color": "linear-gradient(135deg, #d35400, #e67e22)",
        "icon": "☀️",
    })
  if w_val >= 45.0:
    active_warnings.append({
        "title": "Výstraha: Silný vietor!",
        "desc": (
            f"Rýchlosť vetra dosahuje {w_val:.1f} km/h. Hrozí riziko pádov"
            " predmetov."
        ),
        "color": "linear-gradient(135deg, #7f8c8d, #34495e)",
        "icon": "💨",
    })

  for alert in active_warnings:
    st.markdown(
        f"""
            <div class="meteo-alert-banner" style="background: {alert['color']};">
                <div class="alert-icon">{alert['icon']}</div>
                <div>
                    <div class="alert-title">⚠️ {alert['title']}</div>
                    <div class="alert-desc">{alert['desc']}</div>
                </div>
            </div>
            """,
        unsafe_allow_html=True,
    )

  st.subheader("⚡ Aktuálny stav počasia")
  st.markdown(
      f"""
        <div style="background-color: var(--secondary-background-color); border-radius: 14px; padding: 20px; box-shadow: 0 6px 16px rgba(0,0,0,0.06); display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 15px;">
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="font-size: 3.5em;">{curr_icon}</div>
                <div>
                    <div style="font-size: 1.35em; font-weight: 800;">{curr_desc}</div>
                    <div style="font-size: 0.9em; opacity: 0.7; margin-top: 2px;">Pusté Pole • Stanica online</div>
                    <div style="font-size: 0.85em; opacity: 0.85; margin-top: 6px;">
                        🌅 Východ: <b>{sunrise_str}</b> | 🌇 Západ: <b>{sunset_str}</b> | 🌙 Fáza: <b>{moon_phase_str}</b>
                    </div>
                </div>
            </div>
            <div style="font-size: 0.9em; text-align: right; opacity: 0.9;">
                <div>Teplota: <b>{t_val:.1f} °C</b></div>
                <div>Tlak: <b>{p_val:.1f} hPa</b></div>
                <div>Vietor: <b>{w_val:.1f} km/h</b> ({w_cardinal})</div>
            </div>
        </div>
        """,
      unsafe_allow_html=True,
  )

  temp_pct = min(100, max(0, ((t_val + 20) / 70) * 100))
  press_pct = min(100, max(0, ((p_val - 950) / (1050 - 950)) * 100))
  hum_angle = (h_val / 100) * 270 - 135
  wind_angle = min(135, max(-135, (w_val / 50) * 270 - 135))
  uv_angle = min(135, max(-135, (uv_val / 12) * 270 - 135))
  rain_pct = min(100, max(0, (r_val / 50) * 100))

  hum_desc = (
      "Suchý vzduch (pod 30%)"
      if h_val < 30
      else (
          "Ideálna vlhkosť vzduchu (30% - 60%)"
          if h_val <= 60
          else "Vysoká vlhkosť / dusno (nad 60%)"
      )
  )
  press_desc = (
      f"Atmosférický tlak {p_val:.1f} hPa: Nízky tlak (tlaková níž)."
      if p_val < 1000
      else (
          f"Atmosférický tlak {p_val:.1f} hPa: Normálny / štandardný tlak."
          if p_val <= 1025
          else f"Atmosférický tlak {p_val:.1f} hPa: Vysoký tlak (tlaková výš)."
      )
  )
  uv_desc = f"UV index {uv_val:.1f}"
  rain_desc = f"Úhrn zrážok: {r_val:.1f} mm"

  col1, col2, col3, col4, col5, col6 = st.columns(6)

  with col1:
    st.markdown(
        f"""
            <div class="weather-card">
                <div class="card-title">Teplota</div>
                <div class="bar-container">
                    <div class="bar-scale"><span>50°</span><span>25°</span><span>0°</span><span>-20°</span></div>
                    <div class="thermometer-box"><div class="thermometer-fill" style="height: {temp_pct}%;"></div></div>
                </div>
                <div class="main-value">{t_val:.1f} °C</div>
                <div class="sub-value">Pocitová: {pocitova_val:.1f} °C</div>
            </div>
            """,
        unsafe_allow_html=True,
    )
  with col2:
    st.markdown(
        f"""
            <div class="weather-card">
                <div class="card-title">Vlhkosť vzduchu</div>
                <div class="gauge-circle gauge-hum">
                    <div class="gauge-inner-cover"></div>
                    <div class="scale-val s-0">0</div><div class="scale-val s-20">20</div><div class="scale-val s-40">40</div><div class="scale-val s-60">60</div><div class="scale-val s-80">80</div><div class="scale-val s-100">100</div>
                    <div class="scale-unit">%</div>
                    <div class="gauge-needle" style="transform: translateX(-50%) rotate({hum_angle}deg);"></div>
                    <div class="gauge-center-dot"></div>
                </div>
                <div class="main-value-tooltip" title="{hum_desc}">{h_val:.0f} %</div>
                <div class="sub-value">Rosný bod: {dew_val:.1f} °C</div>
            </div>
            """,
        unsafe_allow_html=True,
    )
  with col3:
    st.markdown(
        f"""
            <div class="weather-card">
                <div class="card-title">Atmosférický tlak</div>
                <div class="bar-container">
                    <div class="bar-scale"><span>1050</span><span>1020</span><span>980</span><span>950</span></div>
                    <div class="pressure-box"><div class="pressure-fill" style="height: {press_pct}%;"></div></div>
                </div>
                <div class="main-value-tooltip" title="{press_desc}">{p_val:.1f} hPa</div>
                <div class="sub-value">Barometer</div>
            </div>
            """,
        unsafe_allow_html=True,
    )
  with col4:
    st.markdown(
        f"""
            <div class="weather-card">
                <div class="card-title">Rýchlosť vetra</div>
                <div class="gauge-circle gauge-wind">
                    <div class="gauge-inner-cover"></div>
                    <div class="scale-val s-0">0</div><div class="scale-val s-20">10</div><div class="scale-val s-40">20</div><div class="scale-val s-60">30</div><div class="scale-val s-80">40</div><div class="scale-val s-100">50</div>
                    <div class="scale-unit">km/h</div>
                    <div class="gauge-needle" style="transform: translateX(-50%) rotate({wind_angle}deg);"></div>
                    <div class="gauge-center-dot"></div>
                </div>
                <div class="main-value">{w_val:.1f} km/h</div>
                <div class="sub-value">Smer: <b>{w_cardinal}</b></div>
            </div>
            """,
        unsafe_allow_html=True,
    )
  with col5:
    st.markdown(
        f"""
            <div class="weather-card">
                <div class="card-title">UV index</div>
                <div class="gauge-circle gauge-uv">
                    <div class="gauge-inner-cover"></div>
                    <div class="scale-val s-0">0</div><div class="scale-val s-20">2</div><div class="scale-val s-40">5</div><div class="scale-val s-60">7</div><div class="scale-val s-80">10</div><div class="scale-val s-100">12</div>
                    <div class="scale-unit">UV</div>
                    <div class="gauge-needle" style="transform: translateX(-50%) rotate({uv_angle}deg);"></div>
                    <div class="gauge-center-dot"></div>
                </div>
                <div class="main-value-tooltip" title="{uv_desc}">{uv_val:.1f}</div>
                <div class="sub-value">Intenzita žiarenia</div>
            </div>
            """,
        unsafe_allow_html=True,
    )
  with col6:
    st.markdown(
        f"""
            <div class="weather-card">
                <div class="card-title">Úhrn zrážok</div>
                <div class="bar-container">
                    <div class="bar-scale"><span>50</span><span>25</span><span>10</span><span>0</span></div>
                    <div class="rain-box"><div class="rain-fill" style="height: {rain_pct}%;"></div></div>
                </div>
                <div class="main-value-tooltip" title="{rain_desc}">{r_val:.1f} mm</div>
                <div class="sub-value">Zrážkomer</div>
            </div>
            """,
        unsafe_allow_html=True,
    )

  st.markdown("---")

  # --- HORIZONTÁLNA PREDPOVEĎ (24H - ELEGANTNÝ MOBILNÝ STRIP) ---
  st.subheader("⏱️ Hodinová predpoveď (najbližších 24h)")

  if hourly_api_data and "time" in hourly_api_data:
    times = hourly_api_data.get("time", [])
    temps = hourly_api_data.get("temperature_2m", [])
    probs = hourly_api_data.get("precipitation_probability", []) or [0] * len(
        times
    )
    precips = hourly_api_data.get("precipitation", []) or [0.0] * len(times)
    codes = hourly_api_data.get("weather_code", []) or [0] * len(times)
    winds = hourly_api_data.get("wind_speed_10m", []) or [0.0] * len(times)

    now_hour = datetime.datetime.now(ZoneInfo("Europe/Bratislava")).strftime(
        "%Y-%m-%dT%H:00"
    )

    start_idx = 0
    for i, t in enumerate(times):
      if str(t) >= now_hour:
        start_idx = i
        break

    times_24 = times[start_idx : start_idx + 24]
    temps_24 = temps[start_idx : start_idx + 24]
    probs_24 = probs[start_idx : start_idx + 24]
    precips_24 = precips[start_idx : start_idx + 24]
    codes_24 = codes[start_idx : start_idx + 24]
    winds_24 = winds[start_idx : start_idx + 24]

    if times_24:
      cards_html = '<div class="hourly-scroll-strip">'
      for i, (t, temp, prob, precip, code, wind_spd) in enumerate(
          zip(times_24, temps_24, probs_24, precips_24, codes_24, winds_24)
      ):
        try:
          time_str = str(t).split("T")[1][:5]
          parts = str(t).split("T")[0].split("-")
          date_str = f"{int(parts[2])}.{int(parts[1])}."
        except:
          time_str, date_str = "--:--", "--.--"

        is_first = i == 0
        card_class = (
            "hourly-pill-card current-hour" if is_first else "hourly-pill-card"
        )
        display_time = (
            "<b style='color:#e67e22;'>Teraz</b>" if is_first else time_str
        )

        h_icon = get_weather_icon(code)
        t_num = float(temp)
        p_val_num = float(precip) if precip else 0.0

        if t_num >= 20:
          temp_color = "#e67e22"
        elif t_num >= 10:
          temp_color = "#27ae60"
        else:
          temp_color = "#2980b9"

        if prob >= 20 or p_val_num > 0.0:
          rain_snippet = (
              f"<div style='background: rgba(41,128,185,0.14); color: #2980b9;"
              " border-radius: 6px; padding: 3px 2px; margin-top: 4px;'><div"
              " style='font-size: 0.68em; font-weight: 800; line-height:"
              f" 1.1;'>💧 {prob}%</div><div style='font-size: 0.62em;"
              " font-weight: 600; opacity: 0.85; margin-top: 1px;'>"
              f" {p_val_num:.1f} mm</div></div>"
          )
        else:
          rain_snippet = (
              "<div style='font-size: 0.65em; opacity: 0.4; margin-top: 8px;'>💨"
              f" {round(float(wind_spd))} km/h</div>"
          )

        cards_html += (
            f'<div class="{card_class}">'
            f"<div><div style='font-size: 0.82em; font-weight: 700;'>{display_time}</div>"
            f"<div style='font-size: 0.65em; opacity: 0.55; margin-top: 1px;'>{date_str}</div></div>"
            f"<div style='font-size: 1.85em; margin: 4px 0;'>{h_icon}</div>"
            f"<div><div style='font-size: 1.1em; font-weight: 800; color: {temp_color};'>{t_num:.0f}°</div>"
            f"{rain_snippet}</div>"
            f"</div>"
        )

      cards_html += "</div>"
      st.markdown(cards_html, unsafe_allow_html=True)
    else:
      st.info("Žiadne dáta pre najbližších 24 hodín.")
  else:
    st.info("Podrobné hodinové dáta predpovede nie sú dostupné.")

  st.markdown("---")

  # --- PREDPOVEĎ NA 7 DNÍ ---
  st.subheader("🔮 Predpoveď počasia na najbližšie dni")
  if forecast_data and "time" in forecast_data:
    days = forecast_data.get("time", [])
    t_max_f = forecast_data.get("temperature_2m_max", [])
    t_min_f = forecast_data.get("temperature_2m_min", [])
    rain_f = forecast_data.get("precipitation_sum", [])
    w_codes = forecast_data.get("weather_code", [])

    num_days = min(len(days), 7)
    if num_days > 0:
      cols = st.columns(num_days)

      sk_dni = {
          "Monday": "Pondelok",
          "Tuesday": "Utorok",
          "Wednesday": "Streda",
          "Thursday": "Štvrtok",
          "Friday": "Piatok",
          "Saturday": "Sobota",
          "Sunday": "Nedeľa",
      }

      for i in range(num_days):
        with cols[i]:
          date_obj = datetime.datetime.strptime(days[i], "%Y-%m-%d")
          nazov_dna = (
              "Dnes" if i == 0 else sk_dni.get(date_obj.strftime("%A"), "")[:3]
          )
          formatted_date = f"{date_obj.day}.{date_obj.month}."

          code_val = w_codes[i] if i < len(w_codes) else 0
          icon = get_weather_icon(code_val)
          r_sum = float(rain_f[i])

          rain_badge = (
              "<div style='font-size: 0.72em; color: #2980b9; font-weight: 700;"
              " background: rgba(41, 128, 185, 0.12); border-radius: 6px;"
              f" padding: 2px 4px; margin-top: 6px;'>💧 {r_sum:.1f} mm</div>"
              if r_sum > 0
              else (
                  "<div style='font-size: 0.72em; opacity: 0.45; margin-top:"
                  " 6px;'>bez zrážok</div>"
              )
          )

          st.markdown(
              f"""
              <div style="background-color: var(--secondary-background-color); border: 1px solid rgba(150, 150, 150, 0.18); border-radius: 12px; padding: 12px 6px; text-align: center; box-shadow: 0 3px 8px rgba(0,0,0,0.04);">
                  <div style="font-size: 0.85em; font-weight: 800; text-transform: uppercase;">{nazov_dna}</div>
                  <div style="font-size: 0.7em; opacity: 0.6; margin-bottom: 4px;">{formatted_date}</div>
                  <div style="font-size: 2.2em; margin: 4px 0;">{icon}</div>
                  <div style="display: flex; justify-content: center; align-items: baseline; gap: 6px; margin-top: 6px;">
                      <span style="font-size: 1.05em; font-weight: 800; color: #e74c3c;">{float(t_max_f[i]):.0f}°</span>
                      <span style="font-size: 0.85em; font-weight: 600; opacity: 0.5;">/</span>
                      <span style="font-size: 0.85em; font-weight: 700; color: #3498db;">{float(t_min_f[i]):.0f}°</span>
                  </div>
                  {rain_badge}
              </div>
              """,
              unsafe_allow_html=True,
          )

# --- ZÁLOŽKA: ŽIVÝ METEORADAR (POČASIE & RADAR OFICIÁLNY JS WIDGET) ---
with tab_radar:
  st.subheader("📡 Meteoradar & Oblačnosť (Počasie & Radar)")
  st.caption(
      "Živý postup zrážok, búrok a oblačnosti s predpoveďou • Pusté Pole a"
      " okolie"
  )

  pocasie_radar_code = f"""
    <div style="display: flex; justify-content: center; width: 100%;">
        <div id="weather-radar-widget" style="width: 100%; max-width: 900px; height: 580px; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.08); border: 1px solid rgba(150, 150, 150, 0.25);"></div>
    </div>
    <script type="text/javascript" src="https://api.wo-cloud.com/content/widget/v2/index.js"></script>
    <script type="text/javascript">
        _woWidget.push({{
            target: "weather-radar-widget",
            geoLat: {LAT},
            geoLon: {LON},
            geoType: "coordinates",
            lang: "sk",
            type: "radar",
            showControls: true
        }});
    </script>
    """
  components.html(pocasie_radar_code, height=600)

# --- ZÁLOŽKA: HISTÓRIA & REKORDY STANICE ---
with tab_historia:
  df = load_data()

  if df is not None and not df.empty:
    t_max_col = next(
        (c for c in df.columns if "tepl" in c.lower() and "max" in c.lower()),
        None,
    )
    t_min_col = next(
        (c for c in df.columns if "tepl" in c.lower() and "min" in c.lower()),
        None,
    )
    t_avg_col = next(
        (
            c
            for c in df.columns
            if "tepl" in c.lower()
            and ("priem" in c.lower() or "avg" in c.lower())
        ),
        None,
    )
    w_max_col = next(
        (c for c in df.columns if "viet" in c.lower() and "max" in c.lower()),
        None,
    )
    r_col = next(
        (
            c
            for c in df.columns
            if any(
                k in c.lower()
                for k in ["zráž", "zraz", "rain", "uhrn", "precipitation"]
            )
        ),
        None,
    )
    h_col = next(
        (c for c in df.columns if any(k in c.lower() for k in ["vlhk", "hum"])),
        None,
    )
    w_dir_col = next(
        (
            c
            for c in df.columns
            if any(k in c.lower() for k in ["smer", "wdir"])
        ),
        None,
    )
    w_speed_col = next(
        (
            c
            for c in df.columns
            if any(k in c.lower() for k in ["vietor", "wind", "wspd"])
        ),
        None,
    )

    # --- 1. ABSOLÚTNE REKORDY STANICE ---
    st.subheader("🏆 Absolútne rekordy stanice (od 1. 7. 2026)")
    if t_max_col and t_min_col and w_max_col and r_col:
      abs_max_t_row = df.loc[df[t_max_col].idxmax()]
      abs_min_t_row = df.loc[df[t_min_col].idxmin()]
      abs_max_w_row = df.loc[df[w_max_col].idxmax()]
      abs_max_r_row = df.loc[df[r_col].idxmax()]

      acol1, acol2, acol3, acol4 = st.columns(4)
      acol1.metric(
          "🌡️ Abs. Max Teplota",
          f"{abs_max_t_row[t_max_col]:.1f} °C",
          delta=str(
              abs_max_t_row["DateTime"].strftime("%d.%m.%Y")
              if pd.notnull(abs_max_t_row["DateTime"])
              else ""
          ),
      )
      acol2.metric(
          "❄️ Abs. Min Teplota",
          f"{abs_min_t_row[t_min_col]:.1f} °C",
          delta=str(
              abs_min_t_row["DateTime"].strftime("%d.%m.%Y")
              if pd.notnull(abs_min_t_row["DateTime"])
              else ""
          ),
      )
      acol3.metric(
          "💨 Abs. Max Vietor",
          f"{abs_max_w_row[w_max_col]:.1f} km/h",
          delta=str(
              abs_max_w_row["DateTime"].strftime("%d.%m.%Y")
              if pd.notnull(abs_max_w_row["DateTime"])
              else ""
          ),
      )
      acol4.metric(
          "🌧️ Abs. Max Zrážky",
          f"{abs_max_r_row[r_col]:.1f} mm",
          delta=str(
              abs_max_r_row["DateTime"].strftime("%d.%m.%Y")
              if pd.notnull(abs_max_r_row["DateTime"])
              else ""
          ),
      )
    else:
      st.info(
          "Niektoré stĺpce pre absolútne rekordy neboli v CSV súbore nájdené."
      )

    st.markdown("---")

    # --- 2. VÝBER OBDOBIA (VÝRAZNÝ HORIZONTÁLNY PANEL) ---
    min_d = df["DateTime"].min().date()
    max_d = df["DateTime"].max().date()
    df_filtered = df.copy()
    df_prev = pd.DataFrame()

    with st.container():
      st.markdown(
          """
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="font-size: 1.15em;">🗓️</span>
                <span style="font-weight: 800; font-size: 1.05em; letter-spacing: -0.3px;">Nastavenie zobrazeného obdobia</span>
                <span style="font-size: 0.75em; opacity: 0.65; font-weight: 600; background: rgba(150,150,150,0.15); padding: 2px 8px; border-radius: 6px;">Filter dát</span>
            </div>
            """,
          unsafe_allow_html=True,
      )

      f_col1, f_col2, f_col3 = st.columns([2.4, 1, 1])

      with f_col1:
        volba = st.radio(
            "Typ filtra:",
            [
                "Posledných 7 dní",
                "Konkrétny mesiac a rok",
                "Konkrétny rok",
                "Vlastné obdobie",
            ],
            horizontal=True,
            label_visibility="collapsed",
        )

      if volba == "Posledných 7 dní":
        datum_do = max_d
        datum_od = max_d - datetime.timedelta(days=6)
        df_filtered = df_filtered[
            (df_filtered["DateTime"].dt.date >= datum_od)
            & (df_filtered["DateTime"].dt.date <= datum_do)
        ]
        prev_datum_do = datum_od - datetime.timedelta(days=1)
        prev_datum_od = prev_datum_do - datetime.timedelta(days=6)
        df_prev = df[
            (df["DateTime"].dt.date >= prev_datum_od)
            & (df["DateTime"].dt.date <= prev_datum_do)
        ]

      elif volba == "Konkrétny mesiac a rok":
        dostupne_roky = sorted(df["DateTime"].dt.year.unique(), reverse=True)
        with f_col2:
          vybrany_rok = st.selectbox("Rok", dostupne_roky)
        with f_col3:
          vybrany_mesiac = st.selectbox(
              "Mesiac",
              list(range(1, 13)),
              index=datetime.date.today().month - 1,
              format_func=lambda x: [
                  "Január",
                  "Február",
                  "Marec",
                  "Apríl",
                  "Máj",
                  "Jún",
                  "Júl",
                  "August",
                  "September",
                  "Október",
                  "November",
                  "December",
              ][x - 1],
          )
        df_filtered = df_filtered[
            (df_filtered["DateTime"].dt.year == vybrany_rok)
            & (df_filtered["DateTime"].dt.month == vybrany_mesiac)
        ]
        prev_month = vybrany_mesiac - 1 if vybrany_mesiac > 1 else 12
        prev_year = vybrany_rok if vybrany_mesiac > 1 else vybrany_rok - 1
        df_prev = df[
            (df["DateTime"].dt.year == prev_year)
            & (df["DateTime"].dt.month == prev_month)
        ]

      elif volba == "Konkrétny rok":
        dostupne_roky = sorted(df["DateTime"].dt.year.unique(), reverse=True)
        with f_col2:
          vybrany_rok = st.selectbox("Rok", dostupne_roky)
        df_filtered = df_filtered[
            df_filtered["DateTime"].dt.year == vybrany_rok
        ]
        df_prev = df[df["DateTime"].dt.year == vybrany_rok - 1]

      elif volba == "Vlastné obdobie":
        with f_col2:
          datum_od = st.date_input("Od", min_d)
        with f_col3:
          datum_do = st.date_input("Do", max_d)
        df_filtered = df_filtered[
            (df_filtered["DateTime"].dt.date >= datum_od)
            & (df_filtered["DateTime"].dt.date <= datum_do)
        ]
        delta_dni = (datum_do - datum_od).days + 1
        prev_datum_do = datum_od - datetime.timedelta(days=1)
        prev_datum_od = prev_datum_do - datetime.timedelta(days=delta_dni - 1)
        df_prev = df[
            (df["DateTime"].dt.date >= prev_datum_od)
            & (df["DateTime"].dt.date <= prev_datum_do)
        ]

    # --- 3. ŠTATISTIKY V PREHĽADNÝCH KARTÁCH ---
    dni_pocet = len(df_filtered)
    sk_dni_koncovka = (
        "dní" if dni_pocet >= 5 else ("dni" if dni_pocet > 1 else "deň")
    )
    st.subheader(
        f"📊 Štatistiky za vybrané obdobie ({dni_pocet} {sk_dni_koncovka})"
    )

    if not df_filtered.empty:
      max_temp = (
          df_filtered[t_max_col].max()
          if t_max_col and not df_filtered[t_max_col].isna().all()
          else 0
      )
      min_temp = (
          df_filtered[t_min_col].min()
          if t_min_col and not df_filtered[t_min_col].isna().all()
          else 0
      )
      avg_temp = (
          df_filtered[t_avg_col].mean()
          if t_avg_col and not df_filtered[t_avg_col].isna().all()
          else 0
      )
      max_wind = (
          df_filtered[w_max_col].max()
          if w_max_col and not df_filtered[w_max_col].isna().all()
          else 0
      )
      total_rain = (
          df_filtered[r_col].sum()
          if r_col and not df_filtered[r_col].isna().all()
          else 0
      )
      max_rain = (
          df_filtered[r_col].max()
          if r_col and not df_filtered[r_col].isna().all()
          else 0
      )

      # Pomocná funkcia na vykreslenie odchýlky (delta)
      def render_delta(diff, unit):
        if diff is None:
          return (
              "<span style='font-size:0.7em; opacity:0.35;'>— bez porovnania"
              "</span>"
          )
        cls = "delta-down" if diff < 0 else "delta-up"
        arrow = "↓" if diff < 0 else "↑"
        return f"<span class='stat-delta {cls}'>{arrow} {diff:+.1f} {unit}</span>"

      diff_max_t = (
          (max_temp - df_prev[t_max_col].max())
          if not df_prev.empty
          and t_max_col
          and not df_prev[t_max_col].isna().all()
          else None
      )
      diff_min_t = (
          (min_temp - df_prev[t_min_col].min())
          if not df_prev.empty
          and t_min_col
          and not df_prev[t_min_col].isna().all()
          else None
      )
      diff_avg_t = (
          (avg_temp - df_prev[t_avg_col].mean())
          if not df_prev.empty
          and t_avg_col
          and not df_prev[t_avg_col].isna().all()
          else None
      )
      diff_wind = (
          (max_wind - df_prev[w_max_col].max())
          if not df_prev.empty
          and w_max_col
          and not df_prev[w_max_col].isna().all()
          else None
      )
      diff_rain = (
          (total_rain - df_prev[r_col].sum())
          if not df_prev.empty and r_col and not df_prev[r_col].isna().all()
          else None
      )

      # 6 kariet vedľa seba v jednom čistom rade
      sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)

      with sc1:
        st.markdown(
            f"""<div class="stat-card" style="border-top: 3.5px solid #e74c3c;">
                <div class="stat-label">📈 Max Teplota</div>
                <div class="stat-val" style="color:#e74c3c;">{max_temp:.1f} °C</div>
                <div>{render_delta(diff_max_t, '°C')}</div>
            </div>""",
            unsafe_allow_html=True,
        )
      with sc2:
        st.markdown(
            f"""<div class="stat-card" style="border-top: 3.5px solid #3498db;">
                <div class="stat-label">📉 Min Teplota</div>
                <div class="stat-val" style="color:#3498db;">{min_temp:.1f} °C</div>
                <div>{render_delta(diff_min_t, '°C')}</div>
            </div>""",
            unsafe_allow_html=True,
        )
      with sc3:
        st.markdown(
            f"""<div class="stat-card" style="border-top: 3.5px solid #f39c12;">
                <div class="stat-label">🌡️ Priemer</div>
                <div class="stat-val" style="color:#f39c12;">{avg_temp:.1f} °C</div>
                <div>{render_delta(diff_avg_t, '°C')}</div>
            </div>""",
            unsafe_allow_html=True,
        )
      with sc4:
        st.markdown(
            f"""<div class="stat-card" style="border-top: 3.5px solid #27ae60;">
                <div class="stat-label">💨 Max Vietor</div>
                <div class="stat-val" style="color:#27ae60;">{max_wind:.1f} <span style="font-size:0.65em;">km/h</span></div>
                <div>{render_delta(diff_wind, 'k')}</div>
            </div>""",
            unsafe_allow_html=True,
        )
      with sc5:
        st.markdown(
            f"""<div class="stat-card" style="border-top: 3.5px solid #2980b9;">
                <div class="stat-label">🌧️ Úhrn Zrážok</div>
                <div class="stat-val" style="color:#2980b9;">{total_rain:.1f} <span style="font-size:0.65em;">mm</span></div>
                <div>{render_delta(diff_rain, 'mm')}</div>
            </div>""",
            unsafe_allow_html=True,
        )
      with sc6:
        st.markdown(
            f"""<div class="stat-card" style="border-top: 3.5px solid #9b59b6;">
                <div class="stat-label">⛈️ Max Denné Zrážky</div>
                <div class="stat-val" style="color:#9b59b6;">{max_rain:.1f} <span style="font-size:0.65em;">mm</span></div>
                <div style="font-size:0.7em; opacity:0.5; font-weight:700;">denný rekord</div>
            </div>""",
            unsafe_allow_html=True,
        )

      st.markdown(
          "<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True
      )

      view_mode = st.radio(
          "Zvoliť spôsob zobrazenia údajov:",
          ["📈 Grafy", "📋 Tabuľka"],
          horizontal=True,
      )

      if view_mode == "📈 Grafy":
        chart_config = {"displayModeBar": False}
        layout_updates = dict(
            height=320,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.35,
                xanchor="center",
                x=0.5,
            ),
        )

        gcol1, gcol2 = st.columns(2)

        with gcol1:
          fig_temp = go.Figure()
          if t_max_col:
            fig_temp.add_trace(
                go.Scatter(
                    x=df_filtered["DateTime"],
                    y=df_filtered[t_max_col],
                    name="Max Teplota",
                    line=dict(color="#e74c3c", width=1.5),
                    mode="lines",
                    hovertemplate="%{name}: <b>%{y:.1f} °C</b><extra></extra>",
                )
            )
          if t_min_col:
            fig_temp.add_trace(
                go.Scatter(
                    x=df_filtered["DateTime"],
                    y=df_filtered[t_min_col],
                    name="Min Teplota",
                    line=dict(color="#3498db", width=1.5),
                    fill="tonexty",
                    fillcolor="rgba(231, 76, 60, 0.12)",
                    mode="lines",
                    hovertemplate="%{name}: <b>%{y:.1f} °C</b><extra></extra>",
                )
            )
          if t_avg_col:
            fig_temp.add_trace(
                go.Scatter(
                    x=df_filtered["DateTime"],
                    y=df_filtered[t_avg_col],
                    name="Priemer",
                    line=dict(color="#f39c12", width=2.5, dash="dot"),
                    mode="lines",
                    hovertemplate="%{name}: <b>%{y:.1f} °C</b><extra></extra>",
                )
            )
          fig_temp.update_layout(
              title="🌡️ Teplotné rozpätie a denný priemer",
              hovermode="x unified",
              **layout_updates,
          )
          st.plotly_chart(
              fig_temp,
              use_container_width=True,
              theme="streamlit",
              config=chart_config,
          )

          if r_col:
            fig_rain = go.Figure()
            fig_rain.add_trace(
                go.Bar(
                    x=df_filtered["DateTime"],
                    y=df_filtered[r_col],
                    name="Denný úhrn (mm)",
                    marker_color="#3498db",
                    hovertemplate="%{name}: <b>%{y:.1f} mm</b><extra></extra>",
                )
            )
            fig_rain.add_trace(
                go.Scatter(
                    x=df_filtered["DateTime"],
                    y=df_filtered[r_col].cumsum(),
                    name="Kumulatívne (mm)",
                    line=dict(color="#1b4f72", width=2.2),
                    yaxis="y2",
                    mode="lines",
                    hovertemplate="%{name}: <b>%{y:.1f} mm</b><extra></extra>",
                )
            )
            fig_rain.update_layout(
                title="🌧️ Denné a kumulatívne zrážky",
                yaxis=dict(title="Denné (mm)"),
                yaxis2=dict(
                    title="Kumulatívne (mm)", overlaying="y", side="right"
                ),
                hovermode="x unified",
                **layout_updates,
            )
            st.plotly_chart(
                fig_rain,
                use_container_width=True,
                theme="streamlit",
                config=chart_config,
            )

        with gcol2:
          if w_max_col:
            fig_wind = go.Figure()
            fig_wind.add_trace(
                go.Scatter(
                    x=df_filtered["DateTime"],
                    y=df_filtered[w_max_col],
                    name="Max Rýchlosť vetra",
                    line=dict(color="#f39c12", width=2),
                    hovertemplate="%{name}: <b>%{y:.1f} km/h</b><extra></extra>",
                )
            )
            fig_wind.update_layout(
                title="💨 Maximálna rýchlosť vetra",
                hovermode="x unified",
                **layout_updates,
            )
            st.plotly_chart(
                fig_wind,
                use_container_width=True,
                theme="streamlit",
                config=chart_config,
            )

          if h_col:
            fig_hum = go.Figure()
            fig_hum.add_trace(
                go.Scatter(
                    x=df_filtered["DateTime"],
                    y=df_filtered[h_col],
                    name="Vlhkosť",
                    line=dict(color="#2ecc71", width=2),
                    hovertemplate="%{name}: <b>%{y:.1f} %</b><extra></extra>",
                )
            )
            fig_hum.update_layout(
                title="💧 Vývoj vlhkosti vzduchu",
                hovermode="x unified",
                **layout_updates,
            )
            st.plotly_chart(
                fig_hum,
                use_container_width=True,
                theme="streamlit",
                config=chart_config,
            )

        # MESAČNÁ BILANCIA (Celomesačný súhrn z celej histórie databázy)
        st.markdown("---")
        st.subheader("📅 Mesačná bilancia za vybrané obdobie")

        sk_mesiace = {
            "01": "Január",
            "02": "Február",
            "03": "Marec",
            "04": "Apríl",
            "05": "Máj",
            "06": "Jún",
            "07": "Júl",
            "08": "August",
            "09": "September",
            "10": "Október",
            "11": "November",
            "12": "December",
        }

        mesiace_vo_filtri = (
            df_filtered["DateTime"].dt.strftime("%Y-%m").unique()
        )

        df_monthly_full = df[
            df["DateTime"].dt.strftime("%Y-%m").isin(mesiace_vo_filtri)
        ].copy()
        df_monthly_full["M_num"] = df_monthly_full["DateTime"].dt.strftime(
            "%m"
        )
        df_monthly_full["Y_num"] = df_monthly_full["DateTime"].dt.strftime(
            "%Y"
        )
        df_monthly_full["Mesiac_Kluc"] = (
            df_monthly_full["Y_num"] + "-" + df_monthly_full["M_num"]
        )

        agg_dict = {}
        if t_max_col:
          agg_dict["t_max"] = (t_max_col, "max")
        if t_min_col:
          agg_dict["t_min"] = (t_min_col, "min")
        if t_avg_col:
          agg_dict["t_avg"] = (t_avg_col, "mean")
        if r_col:
          agg_dict["r_sum"] = (r_col, "sum")
        if w_max_col:
          agg_dict["w_max"] = (w_max_col, "max")

        if agg_dict and not df_monthly_full.empty:
          monthly_summary = (
              df_monthly_full.groupby(
                  ["Mesiac_Kluc", "Y_num", "M_num"], as_index=False
              )
              .agg(**agg_dict)
              .sort_values("Mesiac_Kluc", ascending=False)
          )

          for _, row in monthly_summary.iterrows():
            nazov_mesiaca = f"{sk_mesiace.get(row['M_num'], '')} {row['Y_num']}"

            st.markdown(
                f"""
                <div style="background-color: var(--secondary-background-color); border: 1px solid rgba(150, 150, 150, 0.18); border-radius: 12px; padding: 16px 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.04);">
                    <div style="font-weight: 800; font-size: 1.15em; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        🗓️ <span>{nazov_mesiaca}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px;">
                        <div style="background: rgba(231, 76, 60, 0.08); padding: 10px; border-radius: 8px; text-align: center; border-left: 3px solid #e74c3c;">
                            <div style="font-size: 0.75em; opacity: 0.8; font-weight: 600;">MAX TEPLOTA</div>
                            <div style="font-size: 1.25em; font-weight: 800; color: #e74c3c; margin-top: 2px;">{row.get('t_max', 0):.1f} °C</div>
                        </div>
                        <div style="background: rgba(52, 152, 219, 0.08); padding: 10px; border-radius: 8px; text-align: center; border-left: 3px solid #3498db;">
                            <div style="font-size: 0.75em; opacity: 0.8; font-weight: 600;">MIN TEPLOTA</div>
                            <div style="font-size: 1.25em; font-weight: 800; color: #3498db; margin-top: 2px;">{row.get('t_min', 0):.1f} °C</div>
                        </div>
                        <div style="background: rgba(243, 156, 18, 0.08); padding: 10px; border-radius: 8px; text-align: center; border-left: 3px solid #f39c12;">
                            <div style="font-size: 0.75em; opacity: 0.8; font-weight: 600;">PRIEMER</div>
                            <div style="font-size: 1.25em; font-weight: 800; color: #f39c12; margin-top: 2px;">{row.get('t_avg', 0):.1f} °C</div>
                        </div>
                        <div style="background: rgba(41, 128, 185, 0.08); padding: 10px; border-radius: 8px; text-align: center; border-left: 3px solid #2980b9;">
                            <div style="font-size: 0.75em; opacity: 0.8; font-weight: 600;">CELÝ MESIAC ZRÁŽKY</div>
                            <div style="font-size: 1.25em; font-weight: 800; color: #2980b9; margin-top: 2px;">{row.get('r_sum', 0):.1f} mm</div>
                        </div>
                        <div style="background: rgba(39, 174, 96, 0.08); padding: 10px; border-radius: 8px; text-align: center; border-left: 3px solid #27ae60;">
                            <div style="font-size: 0.75em; opacity: 0.8; font-weight: 600;">MAX VIETOR</div>
                            <div style="font-size: 1.25em; font-weight: 800; color: #27ae60; margin-top: 2px;">{row.get('w_max', 0):.1f} km/h</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if w_dir_col and w_speed_col:
          st.markdown("---")
          st.subheader("🧭 Veterná ružica (Rozloženie smerov vetra)")

          df_wind_rose = df_filtered.dropna(
              subset=[w_dir_col, w_speed_col]
          ).copy()
          if not df_wind_rose.empty:
            try:
              df_wind_rose["dir_deg"] = (
                  df_wind_rose[w_dir_col]
                  .astype(str)
                  .str.replace("°", "")
                  .astype(float)
              )
              fig_rose = px.bar_polar(
                  df_wind_rose,
                  r=w_speed_col,
                  theta="dir_deg",
                  color=w_speed_col,
                  color_continuous_scale="Viridis",
                  template="plotly",
                  title="Smer a rýchlosť vetra v polárnej schéme",
              )
              fig_rose.update_layout(
                  height=400, margin=dict(l=20, r=20, t=50, b=20)
              )
              st.plotly_chart(
                  fig_rose,
                  use_container_width=True,
                  theme="streamlit",
                  config=chart_config,
              )
            except Exception:
              st.info(
                  "Smer vetra v CSV súbore nie je v číselnom formáte (stupne"
                  " 0-360), preto sa polárna veterná ružica nedá vykresliť."
              )
      else:
        st.subheader("📋 Podrobná tabuľka dát")
        df_table = df_filtered.sort_values("DateTime", ascending=False).copy()

        if "DateTime" in df_table.columns:
          df_table["Dátum"] = df_table["DateTime"].dt.strftime("%d.%m.%Y")
          time_cols = [
              c
              for c in df_table.columns
              if any(
                  k in c.lower() for k in ["čas", "cas", "time", "datetime"]
              )
              and c != "DateTime"
          ]
          df_table = df_table.drop(
              columns=["DateTime"] + time_cols, errors="ignore"
          )
          cols = ["Dátum"] + [c for c in df_table.columns if c != "Dátum"]
          df_table = df_table[cols]

        st.dataframe(df_table, use_container_width=True)

        csv_export_data = df_table.to_csv(index=False, sep=";").encode(
            "utf-8-sig"
        )
        st.download_button(
            label="📥 Stiahnuť vyfiltrované dáta (CSV)",
            data=csv_export_data,
            file_name="meteo_puste_pole_vyber.csv",
            mime="text/csv",
        )

    else:
      st.warning("Pre zvolené obdobie nie sú k dispozícii žiadne dáta.")
  else:
    st.warning(
        f"Súbor '{CSV_FILE}' nebol nájdený. Skontrolujte prosím jeho prítomnosť"
        " v adresári."
    )
