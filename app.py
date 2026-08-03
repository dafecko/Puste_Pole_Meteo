import datetime
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# --- NASTAVENIE STRÁNCY ---
st.set_page_config(
    page_title="Meteo Web Dashboard - Pusté Pole",
    layout="wide"
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
    
    /* Horizontálny scrolovateľný kontajner pre 24h predpoveď */
    .scroll-container {
        display: flex;
        overflow-x: auto;
        gap: 12px;
        padding: 10px 5px 15px 5px;
        scroll-behavior: smooth;
    }
    .scroll-container::-webkit-scrollbar {
        height: 6px;
    }
    .scroll-container::-webkit-scrollbar-thumb {
        background: rgba(150, 150, 150, 0.4);
        border-radius: 10px;
    }
    .mini-hourly-card {
        min-width: 85px;
        max-width: 85px;
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(150, 150, 150, 0.18);
        border-radius: 12px;
        padding: 10px 6px;
        text-align: center;
        flex-shrink: 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        transition: transform 0.2s ease;
    }
    .mini-hourly-card:hover {
        transform: translateY(-2px);
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
    .thermometer-box, .pressure-box {
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
    .s-0   { bottom: 16px; left: 14px; }
    .s-20  { top: 40px; left: 10px; }
    .s-40  { top: 12px; left: 30px; }
    .s-60  { top: 12px; right: 30px; }
    .s-80  { top: 40px; right: 10px; }
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

    @media (max-width: 768px) {
        .weather-card { height: auto; margin-bottom: 15px; }
        .main-value, .main-value-tooltip { font-size: 1.4em; }
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- KONŠTANTY A SÚBORY ---
CSV_FILE = "meteo_puste_pole_v2.csv"
CSV_AKTUALNE = "meteo_aktualne.csv"
LAT, LON = 49.18, 20.85


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


@st.cache_data
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
    df = df.dropna(subset=["DateTime"]).sort_values("DateTime")
    for col in df.columns:
        if col not in [col_datum, col_cas, "DateTime", "Smer vetra"]:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "."), errors="coerce"
            )
    return df


@st.cache_data(ttl=1800)
def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&hourly=temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,sunrise,sunset&forecast_days=7&timezone=Europe/Bratislava"
    try:
        response = requests.get(url)
        data = response.json()
        return (
            data.get("current", None),
            data.get("daily", None),
            data.get("hourly", None),
        )
    except Exception:
        return None, None, None


def get_weather_icon(code):
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

current_api_data, forecast_data, hourly_api_data = get_weather_data(LAT, LON)
curr_code = (
    current_api_data.get("weather_code", 0) if current_api_data else 0
)
curr_icon = get_weather_icon(curr_code)
curr_desc = get_weather_description(curr_code)

sunrise_str, sunset_str = "--:--", "--:--"
if forecast_data and "sunrise" in forecast_data and "sunset" in forecast_data:
    try:
        sunrise_str = forecast_data["sunrise"][0].split("T")[1]
        sunset_str = forecast_data["sunset"][0].split("T")[1]
    except:
        pass
moon_phase_str = get_moon_phase_info()

# Načítanie aktuálnych dát zo súboru
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
            datum_str = akt.get("Dátum", akt.get("datum", ""))
            cas_str = akt.get("Čas", akt.get("cas", ""))

            def get_val(df_row, keywords):
                for k in keywords:
                    for col in df_row.index:
                        if k.lower() in col.lower():
                            val = df_row[col]
                            try:
                                return float(str(val).replace(",", "."))
                            except:
                                return val
                return 0.0

            def get_str_val(df_row, keywords):
                for k in keywords:
                    for col in df_row.index:
                        if k.lower() in col.lower():
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
        st.error(f"Chyba pri spracovaní aktuálnych dát: {e}")

if t_val <= 10.0 and chill_val != 0:
    pocitova_val = chill_val
elif t_val >= 25.0 and heat_val != 0:
    pocitova_val = heat_val
else:
    if heat_val != 0 and heat_val != t_val:
        pocitova_val = heat_val
    elif chill_val != 0 and chill_val != t_val:
        pocitova_val = chill_val
    else:
        pocitova_val = t_val

# --- HLAVNÉ ZÁLOŽKY (TABS) ---
tab_aktualne, tab_historia = st.tabs(
    ["🌤️ Aktuálne počasie & Predpoveď", "📊 História & Rekordy stanice"]
)

with tab_aktualne:
    if datum_str or cas_str:
        st.caption(f"📅 Posledná aktualizácia zo stanice: {datum_str} o {cas_str}")

    # --- AUTOMATICKÉ METEO VÝSTRAHY (BANNER) ---
    active_warnings = []
    if t_val <= 3.0:
        active_warnings.append({
            "title": "Pozor: Hrozí prízemný mráz!",
            "desc": f"Teplota klesla na {t_val:.1f} °C. Hrozí riziko poškodenia vegetácie.",
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
            "desc": f"Aktuálna hodnota UV indexu je {uv_val:.1f}. Obmedzte pobyt na slnku bez ochrany.",
            "color": "linear-gradient(135deg, #d35400, #e67e22)",
            "icon": "☀️",
        })
    if w_val >= 45.0:
        active_warnings.append({
            "title": "Výstraha: Silný vietor!",
            "desc": f"Rýchlosť vetra dosahuje {w_val:.1f} km/h. Hrozí riziko pádov predmetov.",
            "color": "linear-gradient(135deg, #7f8c8d, #34495e)",
            "icon": "💨",
        })

    if active_warnings:
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

    if h_val < 30:
        hum_desc = "Suchý vzduch (pod 30%)"
    elif h_val <= 60:
        hum_desc = "Ideálna vlhkosť vzduchu (30% - 60%)"
    else:
        hum_desc = "Vysoká vlhkosť / dusno (nad 60%)"

    if p_val < 1000:
        press_desc = f"Atmosférický tlak {p_val:.1f} hPa: Nízky tlak (tlaková níž). Prináša zhoršené počasie."
    elif p_val <= 1025:
        press_desc = f"Atmosférický tlak {p_val:.1f} hPa: Normálny / štandardný tlak vzduchu."
    else:
        press_desc = f"Atmosférický tlak {p_val:.1f} hPa: Vysoký tlak (tlaková výš). Stabilné počasie."

    if uv_val < 3:
        uv_desc = f"UV index {uv_val:.1f}: Nízke riziko."
    elif uv_val < 6:
        uv_desc = f"UV index {uv_val:.1f}: Stredné riziko."
    elif uv_val < 8:
        uv_desc = f"UV index {uv_val:.1f}: Vysoké riziko!"
    elif uv_val < 11:
        uv_desc = f"UV index {uv_val:.1f}: Veľmi vysoké riziko!"
    else:
        uv_desc = f"UV index {uv_val:.1f}: Extrémne riziko!"

    col1, col2, col3, col4, col5 = st.columns(5)
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
                <div class="sub-value">Zrážky: {r_val:.1f} mm</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

# --- HORIZONTÁLNE SCROLOVATEĽNÁ PREDPOVEĎ PO HODINÁCH (24 HODÍN) ---
st.subheader("⏱️ Podrobná predpoveď po hodinách (najbližších 24h)")

if hourly_api_data and "time" in hourly_api_data:
    df_hourly = pd.DataFrame(hourly_api_data)
    df_hourly["time"] = pd.to_datetime(df_hourly["time"])

    now = pd.Timestamp.now().replace(minute=0, second=0, microsecond=0)

    df_next_24h = df_hourly[
        (df_hourly["time"] >= now)
        & (df_hourly["time"] <= now + pd.Timedelta(hours=23))
    ].copy()

    if not df_next_24h.empty:
        cards_html = '<div class="scroll-container">'

        for _, row in df_next_24h.iterrows():
            h_time = row["time"]
            h_temp = row.get("temperature_2m", 0.0)
            h_code = row.get("weather_code", 0)
            h_prob = row.get("precipitation_probability", 0)
            h_icon = get_weather_icon(h_code)

            time_str = h_time.strftime("%H:%M")

            cards_html += (
                f'<div class="mini-hourly-card">'
                f'<div style="font-size: 0.75em; font-weight: 700; opacity: 0.75;">{time_str}</div>'
                f'<div style="font-size: 1.4em; margin: 3px 0;">{h_icon}</div>'
                f'<div style="font-size: 1.05em; font-weight: 800;">{h_temp:.1f}°C</div>'
                f'<div style="font-size: 0.7em; opacity: 0.75; margin-top: 3px;">💧 {h_prob}%</div>'
                f"</div>"
            )

        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)
    else:
        st.info("Žiadne dáta pre najbližších 24 hodín.")
else:
    st.info("Podrobné hodinové dáta predpovede nie sú dostupné.")

        if not df_next_24h.empty:
            # Vytvorenie horizontálneho pásu s 24 mini-kartami (v jednom riadku bez multiline zátvoriek)
            cards_html = '<div class="scroll-container">'
            
            for _, row in df_next_24h.iterrows():
                h_time = row["time"]
                h_temp = row.get("temperature_2m", 0.0)
                h_code = row.get("weather_code", 0)
                h_prob = row.get("precipitation_probability", 0)
                h_icon = get_weather_icon(h_code)

                time_str = h_time.strftime("%H:%M")

                cards_html += (
                    f'<div class="mini-hourly-card">'
                    f'<div style="font-size: 0.75em; font-weight: 700; opacity: 0.75;">{time_str}</div>'
                    f'<div style="font-size: 1.4em; margin: 3px 0;">{h_icon}</div>'
                    f'<div style="font-size: 1.05em; font-weight: 800;">{h_temp:.1f}°C</div>'
                    f'<div style="font-size: 0.7em; opacity: 0.75; margin-top: 3px;">💧 {h_prob}%</div>'
                    f'</div>'
                )
            
            cards_html += '</div>'
            st.markdown(cards_html, unsafe_allow_html=True)

            # Graf hodinového priebehu pod kartičkami
            fig_24h = go.Figure()
            fig_24h.add_trace(
                go.Scatter(
                    x=df_next_24h["time"],
                    y=df_next_24h["temperature_2m"],
                    name="Teplota (°C)",
                    line=dict(color="#e74c3c", width=3),
                    yaxis="y1",
                )
            )
            fig_24h.add_trace(
                go.Bar(
                    x=df_next_24h["time"],
                    y=df_next_24h["precipitation"],
                    name="Zrážky (mm)",
                    marker_color="#3498db",
                    opacity=0.5,
                    yaxis="y2",
                )
            )

            fig_24h.update_layout(
                height=240,
                margin=dict(l=10, r=10, t=30, b=10),
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
                yaxis=dict(title="Teplota (°C)", side="left"),
                yaxis2=dict(
                    title="Zrážky (mm)",
                    side="right",
                    overlaying="y",
                    showgrid=False,
                ),
                xaxis=dict(tickformat="%d.%m. %H:%M"),
            )
            st.plotly_chart(
                fig_24h,
                use_container_width=True,
                theme="streamlit",
                config={"displayModeBar": False},
            )
    else:
        st.info("Podrobné hodinové dáta predpovede nie sú dostupné.")

    st.markdown("---")

    # --- PREDPOVEĎ POČASIA NA 7 DNÍ ---
    st.subheader("🔮 Predpoveď počasia na najbližšie dni")
    if forecast_data:
        days = forecast_data["time"]
        t_max_f = forecast_data["temperature_2m_max"]
        t_min_f = forecast_data["temperature_2m_min"]
        rain_f = forecast_data["precipitation_sum"]
        w_codes = forecast_data["weathercode"]

        num_days = len(days)
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
                nazov_dna = sk_dni.get(date_obj.strftime("%A"), "")
                formatted_date = f"{nazov_dna}<br>{date_obj.day}.{date_obj.month}."

                icon = get_weather_icon(w_codes[i])
                st.markdown(
                    f"""
                    <div class="weather-card">
                        <div class="card-title" style="height: 45px; line-height: 1.2;">{formatted_date}</div>
                        <div style="font-size: 1.8em; margin: 4px 0;">{icon}</div>
                        <div style="font-size: 0.85em; color: #e74c3c; margin: 2px 0;">Max: <b>{t_max_f[i]:.1f}°C</b></div>
                        <div style="font-size: 0.85em; color: #3498db; margin: 2px 0;">Min: <b>{t_min_f[i]:.1f}°C</b></div>
                        <div style="font-size: 0.8em; opacity: 0.7; margin-top: 6px;">🌧️ {rain_f[i]:.1f} mm</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

with tab_historia:
    df = load_data()

    if df is not None and not df.empty:
        st.sidebar.header("⚙️ Ovládací panel (Filtre)")
        volba = st.sidebar.radio(
            "Vyberte spôsob zobrazenia:",
            [
                "1 - Posledných 7 dní",
                "2 - Konkrétny rok",
                "3 - Konkrétny mesiac a rok",
                "4 - Vlastné obdobie (od - do)",
            ],
        )

        min_d = df["DateTime"].min().date()
        max_d = df["DateTime"].max().date()
        df_filtered = df.copy()

        df_prev = pd.DataFrame()

        if "1" in volba:
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
        elif "2" in volba:
            dostupne_roky = sorted(df["DateTime"].dt.year.unique())
            vybrany_rok = st.sidebar.selectbox("Vyberte rok", dostupne_roky)
            df_filtered = df_filtered[df_filtered["DateTime"].dt.year == vybrany_rok]
            df_prev = df[df["DateTime"].dt.year == vybrany_rok - 1]
        elif "3" in volba:
            dostupne_roky = sorted(df["DateTime"].dt.year.unique())
            vybrany_rok = st.sidebar.selectbox("Vyberte rok", dostupne_roky)
            vybrany_mesiac = st.sidebar.selectbox(
                "Vyberte mesiac",
                list(range(1, 13)),
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
        elif "4" in volba:
            datum_od = st.sidebar.date_input("Dátum od", min_d)
            datum_do = st.sidebar.date_input("Dátum do", max_d)
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

        t_max_col = next(
            (
                c
                for c in df.columns
                if "tepl" in c.lower() and "max" in c.lower()
            ),
            None,
        )
        t_min_col = next(
            (
                c
                for c in df.columns
                if "tepl" in c.lower() and "min" in c.lower()
            ),
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
            (
                c
                for c in df.columns
                if "viet" in c.lower() and "max" in c.lower()
            ),
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
            (
                c
                for c in df.columns
                if any(k in c.lower() for k in ["vlhk", "hum"])
            ),
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

        # --- 2. ŠTATISTIKY A EXTRÉMY ZA VYBRANÉ OBDOBIE ---
        st.subheader("📊 Štatistiky a vývoj za vybrané obdobie")

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

            delta_max_t, delta_min_t, delta_avg_t, delta_wind, delta_rain = (
                None,
                None,
                None,
                None,
                None,
            )
            if not df_prev.empty:
                prev_max_temp = (
                    df_prev[t_max_col].max()
                    if t_max_col and not df_prev[t_max_col].isna().all()
                    else None
                )
                prev_min_temp = (
                    df_prev[t_min_col].min()
                    if t_min_col and not df_prev[t_min_col].isna().all()
                    else None
                )
                prev_avg_temp = (
                    df_prev[t_avg_col].mean()
                    if t_avg_col and not df_prev[t_avg_col].isna().all()
                    else None
                )
                prev_max_wind = (
                    df_prev[w_max_col].max()
                    if w_max_col and not df_prev[w_max_col].isna().all()
                    else None
                )
                prev_total_rain = (
                    df_prev[r_col].sum()
                    if r_col and not df_prev[r_col].isna().all()
                    else None
                )

                if prev_max_temp is not None:
                    delta_max_t = f"{max_temp - prev_max_temp:+.1f} °C vs min. obdobie"
                if prev_min_temp is not None:
                    delta_min_t = f"{min_temp - prev_min_temp:+.1f} °C vs min. obdobie"
                if prev_avg_temp is not None:
                    delta_avg_t = f"{avg_temp - prev_avg_temp:+.1f} °C vs min. obdobie"
                if prev_max_wind is not None:
                    delta_wind = f"{max_wind - prev_max_wind:+.1f} km/h vs min. obdobie"
                if prev_total_rain is not None:
                    delta_rain = f"{total_rain - prev_total_rain:+.1f} mm vs min. obdobie"

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📈 Max Teplota", f"{max_temp:.1f} °C", delta=delta_max_t)
            col2.metric("📉 Min Teplota", f"{min_temp:.1f} °C", delta=delta_min_t)
            col3.metric(
                "🌡️ Priemerná Teplota", f"{avg_temp:.1f} °C", delta=delta_avg_t
            )
            col4.metric("💨 Max Vietor", f"{max_wind:.1f} km/h", delta=delta_wind)

            ecol1, ecol2, ecol3 = st.columns(3)
            ecol1.metric(
                "🌧️ Celkové Zrážky", f"{total_rain:.1f} mm", delta=delta_rain
            )
            ecol2.metric("⛈️ Maximálne Zrážky", f"{max_rain:.1f} mm")
            ecol3.metric("📅 Počet záznamov", f"{len(df_filtered)}")

            st.markdown("---")

            view_mode = st.radio(
                "Zvoliť spôsob zobrazenia údajov:",
                ["📈 Grafy", "📋 Tabuľka"],
                horizontal=True,
            )

            if view_mode == "📈 Grafy":
                chart_config = {"displayModeBar": False}
                layout_updates = dict(
                    height=300,
                    margin=dict(l=10, r=10, t=40, b=10),
                    legend=dict(
                        orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5
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
                                line=dict(color="#d9534f", width=2),
                            )
                        )
                    if t_min_col:
                        fig_temp.add_trace(
                            go.Scatter(
                                x=df_filtered["DateTime"],
                                y=df_filtered[t_min_col],
                                name="Min Teplota",
                                line=dict(color="#337ab7", width=2),
                            )
                        )
                    fig_temp.update_layout(title="🌡️ Vývoj teploty v čase", **layout_updates)
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
                                name="Zrážky",
                                marker_color="#3498db",
                            )
                        )
                        fig_rain.update_layout(
                            title="🌧️ Úhrn zrážok v čase", **layout_updates
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
                            )
                        )
                        fig_wind.update_layout(
                            title="💨 Maximálna rýchlosť vetra", **layout_updates
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
                            )
                        )
                        fig_hum.update_layout(
                            title="💧 Vývoj vlhkosti vzduchu", **layout_updates
                        )
                        st.plotly_chart(
                            fig_hum,
                            use_container_width=True,
                            theme="streamlit",
                            config=chart_config,
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
                    cols = ["Dátum"] + [
                        c for c in df_table.columns if c != "Dátum"
                    ]
                    df_table = df_table[cols]

                st.dataframe(df_table, use_container_width=True)

                csv_export_data = df_table.to_csv(index=False, sep=";").encode("utf-8")
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
            f"Súbor '{CSV_FILE}' nebol nájdený. Skontrolujte prosím jeho prítomnosť v adresári."
        )
