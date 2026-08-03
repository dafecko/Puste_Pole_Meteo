import datetime
import math
import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import streamlit as st

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(
    page_title="Meteo Stanica Pusté Pole",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- SÚBOR S DÁTAMI ---
CSV_FILE = "puste_pole.csv"

# --- OPEN-METEO SÚRADNICE PRE PUSTÉ POLE (cca 49.22°N, 20.90°E) ---
LATITUDE = 49.22
LONGITUDE = 20.90


# --- CACHED NAČÍTANIE A SPRACOVANIE DÁT S BEZPEČNÝM FORMÁTOVANÍM DÁTUMOV ---
@st.cache_data(ttl=300)
def load_data():
    if not os.path.exists(CSV_FILE):
        return None

    try:
        # Skúška načítania s bodkočiarkou aj čiarkou
        try:
            df = pd.read_csv(CSV_FILE, sep=";")
            if len(df.columns) <= 1:
                df = pd.read_csv(CSV_FILE, sep=",")
        except Exception:
            df = pd.read_csv(CSV_FILE, sep=",")

        # Nájdenie stĺpca s dátumom
        date_col = next(
            (c for c in df.columns if any(k in c.lower() for k in ["dátum", "datum", "date"])),
            None,
        )

        if date_col:
            # dayfirst=True zabezpečí správne čítanie formátov ako 1.7.2026 aj 01.07.2026
            df["DateTime"] = pd.to_datetime(
                df[date_col], dayfirst=True, errors="coerce"
            )
            df = df.dropna(subset=["DateTime"])
            df = df.sort_values("DateTime")

        # Prevod číselných stĺpcov
        for col in df.columns:
            if col not in [date_col, "DateTime"]:
                if df[col].dtype == object:
                    df[col] = (
                        df[col]
                        .astype(str)
                        .str.replace(",", ".")
                        .str.replace(" ", "")
                    )
                    df[col] = pd.to_numeric(df[col], errors="coerce")

        return df
    except Exception as e:
        st.error(f"Chyba pri načítavaní CSV súboru: {e}")
        return None


# --- APLIKÁCIA CSS ŠTÝLOV ---
st.markdown(
    """
    <style>
    /* Hlavný kontajner */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Vlastné kartičky / bannery */
    .weather-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    
    .card-title {
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 5px;
    }

    /* CSS Kruhové Budíky / Gauge Icons */
    .gauge-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 5px 0;
    }
    .gauge-container {
        position: relative;
        width: 140px;
        height: 70px;
        overflow: hidden;
    }
    .gauge-circle {
        position: absolute;
        top: 0;
        left: 0;
        width: 140px;
        height: 140px;
        border-radius: 50%;
        box-sizing: border-box;
    }
    .gauge-wind {
        background: conic-gradient(from 270deg at 50% 50%, #2ecc71 0deg 90deg, #f1c40f 90deg 144deg, #e67e22 144deg 162deg, #e74c3c 162deg 180deg, transparent 180deg);
    }
    .gauge-uv {
        background: conic-gradient(from 270deg at 50% 50%, #2ecc71 0deg 45deg, #f1c40f 45deg 105deg, #e67e22 105deg 150deg, #e74c3c 150deg 180deg, transparent 180deg);
    }
    .gauge-inner-cover {
        position: absolute;
        top: 15px;
        left: 15px;
        width: 110px;
        height: 110px;
        background-color: #ffffff;
        border-radius: 50%;
    }
    .gauge-needle {
        position: absolute;
        bottom: 0;
        left: 50%;
        width: 4px;
        height: 55px;
        background-color: #34495e;
        transform-origin: bottom center;
        transition: transform 0.5s ease;
        border-radius: 2px;
    }
    .gauge-center-dot {
        position: absolute;
        bottom: -5px;
        left: 50%;
        width: 14px;
        height: 14px;
        background-color: #2c3e50;
        border-radius: 50%;
        transform: translateX(-50%);
    }
    .scale-val {
        position: absolute;
        font-size: 9px;
        font-weight: bold;
        color: #7f8c8d;
    }
    .s-0 { bottom: 2px; left: 6px; }
    .s-20 { top: 22px; left: 16px; }
    .s-40 { top: 4px; left: 42px; }
    .s-60 { top: 4px; right: 42px; }
    .s-80 { top: 22px; right: 16px; }
    .s-100 { bottom: 2px; right: 6px; }
    
    .scale-unit {
        position: absolute;
        bottom: 18px;
        width: 100%;
        text-align: center;
        font-size: 10px;
        font-weight: bold;
        color: #95a5a6;
    }
    .main-value-tooltip {
        font-size: 1.5em;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2px;
    }
    .sub-value {
        font-size: 0.85em;
        color: #7f8c8d;
    }

    /* Teplomer CSS */
    .thermometer-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        height: 110px;
    }
    .thermometer-outer {
        position: relative;
        width: 16px;
        height: 90px;
        background: #e0e0e0;
        border-radius: 10px;
        padding: 3px;
    }
    .thermometer-inner {
        position: absolute;
        bottom: 3px;
        width: 10px;
        background: linear-gradient(to top, #3498db, #f39c12, #e74c3c);
        border-radius: 5px;
        transition: height 0.5s ease;
    }
    .thermo-vals {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 90px;
        text-align: left;
    }
    
    /* Bannery pre výstrahy */
    .alert-banner {
        padding: 10px 15px;
        border-radius: 6px;
        margin-bottom: 15px;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .alert-danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .alert-warning { background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
    .alert-info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- POMOCNÉ FUNKCIE PRE PREDPOVEĎ A WEATHER CODES ---
@st.cache_data(ttl=3600)
def fetch_forecast():
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,uv_index_max,windspeed_10m_max&timezone=Europe%2FBratislava"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json().get("daily", {})
    except Exception:
        pass
    return None


def get_weather_icon(code):
    # WMO Weather interpretation codes
    if code in [0]:
        return "☀️"  # Jasno
    elif code in [1, 2]:
        return "🌤️"  # Prevažne jasno
    elif code in [3]:
        return "☁️"  # Zamračené
    elif code in [45, 48]:
        return "🌫️"  # Hmla
    elif code in [51, 53, 55, 56, 57]:
        return "🌦️"  # Mrholenie
    elif code in [61, 63, 65, 66, 67]:
        return "🌧️"  # Dážď
    elif code in [71, 73, 75, 77]:
        return "❄️"  # Sneženie
    elif code in [80, 81, 82]:
        return "🌧️"  # Prehánky
    elif code in [85, 86]:
        return "🌨️"  # Snehové prehánky
    elif code in [95, 96, 99]:
        return "⛈️"  # Búrka
    return "🌡️"


# --- HLAVNÝ NÁZOV ---
st.title("🌤️ Meteostanica Pusté Pole")

# Záložky aplikácie
tab_aktualne, tab_historia = st.tabs(["📊 Aktuálny prehľad", "📜 História a Štatistiky"])

# Načítanie dát pre predpoveď
forecast_data = fetch_forecast()

with tab_aktualne:
    # Získanie najnovšieho záznamu z CSV
    df_raw = load_data()

    if df_raw is not None and not df_raw.empty:
        latest = df_raw.iloc[-1]
        last_time = (
            latest["DateTime"].strftime("%d.%m.%Y %H:%M")
            if pd.notnull(latest["DateTime"])
            else "Neznámy"
        )
    else:
        latest = None
        last_time = "Žiadne dáta"

    # Predpoveď na dnes (z Open-Meteo)
    t_max_today = forecast_data["temperature_2m_max"][0] if forecast_data else 20.0
    t_min_today = forecast_data["temperature_2m_min"][0] if forecast_data else 10.0
    wind_max_today = forecast_data["windspeed_10m_max"][0] if forecast_data else 15.0
    uv_today = forecast_data["uv_index_max"][0] if forecast_data else 3.0
    rain_today = forecast_data["precipitation_sum"][0] if forecast_data else 0.0

    # Hodnoty pre zobrazenie
    t_val = latest["Teplota"] if (latest is not None and "Teplota" in latest) else t_max_today
    w_val = latest["Max Vietor"] if (latest is not None and "Max Vietor" in latest) else wind_max_today
    r_val = latest["Zrážky"] if (latest is not None and "Zrážky" in latest) else rain_today
    uv_val = uv_today

    # --- VÝSTRAŽNÝ BANNER ---
    alerts = []
    if w_val >= 60:
        alerts.append(("danger", f"⚠️ <b>VÝSTRAHA PRED SILNÝM VETROM:</b> Nárazy vetra dosahujú až {w_val:.1f} km/h!"))
    elif w_val >= 40:
        alerts.append(("warning", f"💨 <b>UPOZORNENIE:</b> Zvýšená rýchlosť vetra ({w_val:.1f} km/h)."))

    if r_val >= 20:
        alerts.append(("danger", f"🌧️ <b>VÝSTRAHA PRED INTENZÍVNYM DAŽĎOM:</b> Očakávaný úhrn zrážok je {r_val:.1f} mm!"))

    if uv_val >= 8:
        alerts.append(("warning", f"☀️ <b>EXTRÉMNE UV ŽIARENIE:</b> UV Index dosahuje hodnotu {uv_val:.1f}. Použite ochranné prostriedky!"))

    for a_type, a_msg in alerts:
        st.markdown(f'<div class="alert-banner alert-{a_type}">{a_msg}</div>', unsafe_allow_html=True)

    if not alerts:
        st.markdown('<div class="alert-banner alert-info">✅ <b>METEO STATUS:</b> Poveternostné podmienky sú momentálne bez výstrah.</div>', unsafe_allow_html=True)

    st.caption(f"Posledná aktualizácia stanice: **{last_time}**")

    # Uhol ručičky pre vietor (0 - 100 km/h -> -90° až 90°)
    w_angle = min(max((w_val / 100.0) * 180.0 - 90.0, -90.0), 90.0)

    # Popis vetra
    if w_val < 10:
        w_desc = "Slabý vietor"
    elif w_val < 30:
        w_desc = "Mierny vietor"
    elif w_val < 60:
        w_desc = "Silný vietor"
    else:
        w_desc = "Víchrica"

    # Uhol ručičky pre UV Index (0 - 12 -> -90° až 90°)
    uv_angle = min(max((uv_val / 12.0) * 180.0 - 90.0, -90.0), 90.0)

    if uv_val <= 2:
        uv_desc = "Nízke UV"
    elif uv_val <= 5:
        uv_desc = "Mierne UV"
    elif uv_val <= 7:
        uv_desc = "Vysoké UV"
    elif uv_val <= 10:
        uv_desc = "Veľmi vysoké UV"
    else:
        uv_desc = "Extrémne UV"

    # Teplomer výška %
    t_min_scale, t_max_scale = -20.0, 40.0
    t_perc = min(max((t_val - t_min_scale) / (t_max_scale - t_min_scale) * 100.0, 5.0), 100.0)

    # --- ZOBRAZENIE BUĎÍKOV A TEPLOMERA ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="weather-card gauge-wrapper">
                <div class="card-title">💨 Maximálny vietor</div>
                <div class="gauge-container">
                    <div class="gauge-circle gauge-wind">
                        <div class="gauge-inner-cover"></div>
                        <div class="scale-val s-0">0</div>
                        <div class="scale-val s-20">20</div>
                        <div class="scale-val s-40">40</div>
                        <div class="scale-val s-60">60</div>
                        <div class="scale-val s-80">80</div>
                        <div class="scale-val s-100">100</div>
                        <div class="scale-unit">km/h</div>
                        <div class="gauge-needle" style="transform: translateX(-50%) rotate({w_angle}deg);"></div>
                        <div class="gauge-center-dot"></div>
                    </div>
                </div>
                <div class="main-value-tooltip" title="{w_desc}">{w_val:.1f} <small style="font-size:0.6em">km/h</small></div>
                <div class="sub-value">{w_desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="weather-card gauge-wrapper">
                <div class="card-title">🌡️ Aktuálna teplota</div>
                <div class="thermometer-container">
                    <div class="thermometer-outer">
                        <div class="thermometer-inner" style="height: {t_perc}%;"></div>
                    </div>
                    <div class="thermo-vals">
                        <div style="color: #e74c3c; font-size: 0.8em;">Max: <b>{t_max_today:.1f}°C</b></div>
                        <div style="font-size: 1.4em; font-weight: bold; color: #2c3e50;">{t_val:.1f}°C</div>
                        <div style="color: #3498db; font-size: 0.8em;">Min: <b>{t_min_today:.1f}°C</b></div>
                    </div>
                </div>
                <div class="sub-value" style="margin-top: 5px;">Dnes: {t_min_today:.1f}°C až {t_max_today:.1f}°C</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="weather-card gauge-wrapper">
                <div class="card-title">☀️ UV Index a Zrážky</div>
                <div class="gauge-container">
                    <div class="gauge-circle gauge-uv">
                        <div class="gauge-inner-cover"></div>
                        <div class="scale-val s-0">0</div>
                        <div class="scale-val s-20">2</div>
                        <div class="scale-val s-40">5</div>
                        <div class="scale-val s-60">7</div>
                        <div class="scale-val s-80">10</div>
                        <div class="scale-val s-100">12</div>
                        <div class="scale-unit">UV</div>
                        <div class="gauge-needle" style="transform: translateX(-50%) rotate({uv_angle}deg);"></div>
                        <div class="gauge-center-dot"></div>
                    </div>
                </div>
                <div class="main-value-tooltip" title="{uv_desc}">{uv_val:.1f}</div>
                <div class="sub-value">Zrážky: {r_val:.1f} mm</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # --- PREDPOVEĎ POČASIA ---
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
            (c for c in df.columns if any(k in c.lower() for k in ["smer", "wdir"])),
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
                                "Smer vetra v CSV súbore nie je v číselnom formáte (stupne 0-360), preto sa polárna veterná ružica nedá vykresliť."
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
