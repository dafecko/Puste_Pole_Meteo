from datetime import datetime
import pandas as pd
import streamlit as st

# --- NASTAVENIE STRÁNCY ---
st.set_page_config(
    page_title="Meteostanica Pusté Pole", page_icon="⛅", layout="wide"
)

# --- NAČÍTANIE DÁT (Prispôsobte si názov vášho CSV súboru) ---
@st.cache_data
def load_data():
  # Predpokladáme CSV súbor, kde stĺpec s dátumom/časom sa volá 'Datum'
  df = pd.read_csv("meteo_data.csv")
  df["Datum"] = pd.to_datetime(df["Datum"])
  return df


try:
  df_all = load_data()
except Exception as e:
  st.error(
      f"Nepodarilo sa načítať dáta. Uistite sa, že súbor 'meteo_data.csv' existuje."
      f" Chyba: {e}"
  )
  st.stop()

# --- BOČNÝ PANEL (FILTRE) ---
st.sidebar.header("🎛️ Filtre a nastavenia")

# Výber obdobia / filtra
min_date = df_all["Datum"].min().date()
max_date = df_all["Datum"].max().date()

selected_date_range = st.sidebar.date_input(
    "Zvoľte obdobie", [min_date, max_date], min_value=min_date, max_value=max_date
)

# Filtrovanie datasetu pre zvolené obdobie
if len(selected_date_range) == 2:
  start_date, end_date = selected_date_range
  df_filtered = df_all[
      (df_all["Datum"].dt.date >= start_date)
      & (df_all["Datum"].dt.date <= end_date)
  ]
else:
  df_filtered = df_all

# --- HLAVIČKA A INFO O STANICI ---
st.title("⛅ Meteorologická stanica Pusté Pole")
st.markdown(
    """
    <div style="background-color: #f1f3f5; padding: 10px 15px; border-radius: 8px; margin-bottom: 20px; font-size: 0.9em; color: #495057; display: flex; justify-content: space-between; flex-wrap: wrap;">
        <div>📍 <b>Lokalita:</b> Pusté Pole</div>
        <div>🚀 <b>Oficiálne spustená od:</b> 1. 7. 2026</div>
        <div>📊 <b>Záznamov v databáze:</b> {total_records}</div>
    </div>
    """.format(
        total_records=len(df_all)
    ),
    unsafe_allow_html=True,
)

# --- AKTUÁLNY STAV (Posledný riadok v datasete) ---
if not df_all.empty:
  latest = df_all.iloc[-1]

  # Ukážkové premenné pre aktuálny stav (upravte podľa názvov vašich stĺpcov)
  curr_icon = "⛅"
  curr_desc = "Polooblačno"
  sunrise_str = "05:12"
  sunset_str = "20:34"
  moon_phase_str = "Dorastajúci mesiac"

  t_val = latest.get("Teplota", 0.0)
  pocitova_val = latest.get("PocitovaTeplota", t_val)
  p_val = latest.get("Tlak", 1013.2)
  h_val = latest.get("Vlhkost", 65.0)
  dew_val = latest.get("RosnyBod", 10.0)
  w_val = latest.get("Vietor", 5.0)
  w_dir = latest.get("VietorSmer", "SZ")
  r_val = latest.get("Zrazky", 0.0)
  uv_val = latest.get("UV", 2.1)

  # Horná karta aktuálneho počasia
  st.markdown(
      f"""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); margin-bottom: 25px;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="font-size: 3.5em;">{curr_icon}</div>
                    <div>
                        <div style="font-size: 1.3em; font-weight: bold; color: #2c3e50;">{curr_desc}</div>
                        <div style="font-size: 0.9em; color: #6c757d; margin-top: 2px;">Pusté Pole • Aktuálny stav zo stanice</div>
                        <div style="font-size: 0.85em; color: #495057; margin-top: 6px;">
                            🌅 Východ: <b>{sunrise_str}</b> | 🌇 Západ: <b>{sunset_str}</b> | 🌙 Fáza: <b>{moon_phase_str}</b>
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 20px; flex-wrap: wrap; text-align: right;">
                    <div>
                        <div style="font-size: 0.8em; color: #6c757d; font-weight: 600;">TEPLOTA</div>
                        <div style="font-size: 1.1em; font-weight: bold; color: #2c3e50;">{t_val:.1f} °C</div>
                        <div style="font-size: 0.75em; color: #7f8c8d;">Pocitová: {pocitova_val:.1f} °C</div>
                    </div>
                    <div>
                        <div style="font-size: 0.8em; color: #6c757d; font-weight: 600;">TLAK</div>
                        <div style="font-size: 1.1em; font-weight: bold; color: #2c3e50;">{p_val:.1f} hPa</div>
                    </div>
                    <div>
                        <div style="font-size: 0.8em; color: #6c757d; font-weight: 600;">VLHKOSŤ / ROSNÝ B.</div>
                        <div style="font-size: 1.1em; font-weight: bold; color: #2c3e50;">{h_val:.0f} %</div>
                        <div style="font-size: 0.75em; color: #7f8c8d;">Rosný: {dew_val:.1f} °C</div>
                    </div>
                    <div>
                        <div style="font-size: 0.8em; color: #6c757d; font-weight: 600;">VIETOR ({w_dir})</div>
                        <div style="font-size: 1.1em; font-weight: bold; color: #2c3e50;">{w_val:.1f} km/h</div>
                    </div>
                    <div>
                        <div style="font-size: 0.8em; color: #6c757d; font-weight: 600;">ZRÁŽKY / UV</div>
                        <div style="font-size: 1.1em; font-weight: bold; color: #2c3e50;">{r_val:.1f} mm</div>
                        <div style="font-size: 0.75em; color: #7f8c8d;">UV: {uv_val:.1f}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
      unsafe_allow_html=True,
  )

# --- 1. ABSOLÚTNE REKORDY STANICE (Od 1. 7. 2026, ignorujú filter) ---
st.markdown("### 🏆 Absolútne rekordy stanice (od 1. 7. 2026)")

if not df_all.empty:
  # Nájdenie indexov pre extrémy v celom datasete
  max_t_row = df_all.loc[df_all["Teplota"].idxmax()]
  min_t_row = df_all.loc[df_all["Teplota"].idxmin()]
  max_v_row = df_all.loc[df_all["Vietor"].idxmax()]
  max_z_row = df_all.loc[df_all["Zrazky"].idxmax()]

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric(
        label="🔴 Najvyššia teplota",
        value=f"{max_t_row['Teplota']:.1f} °C",
        delta=str(max_t_row["Datum"].strftime("%d.%m.%Y")),
    )
  with col2:
    st.metric(
        label="🔵 Najnižšia teplota",
        value=f"{min_t_row['Teplota']:.1f} °C",
        delta=str(min_t_row["Datum"].strftime("%d.%m.%Y")),
    )
  with col3:
    st.metric(
        label="💨 Najsilnejší náraz vetra",
        value=f"{max_v_row['Vietor']:.1f} km/h",
        delta=str(max_v_row["Datum"].strftime("%d.%m.%Y")),
    )
  with col4:
    st.metric(
        label="🌧️ Max. denné zrážky",
        value=f"{max_z_row['Zrazky']:.1f} mm",
        delta=str(max_z_row["Datum"].strftime("%d.%m.%Y")),
    )

st.markdown("---")

# --- 2. EXTRÉMY ZA ZVOLENÉ OBDOBIE (Reagujú na filter v bočnom paneli) ---
st.markdown(
    f"### 📊 Extrémy za zvolené obdobie ({selected_date_range[0]} až"
    f" {selected_date_range[1]})"
)

if not df_filtered.empty:
  f_max_t = df_filtered["Teplota"].max()
  f_min_t = df_filtered["Teplota"].min()
  f_max_v = df_filtered["Vietor"].max()
  f_sum_z = df_filtered["Zrazky"].sum()

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric(label="📈 Max. teplota v období", value=f"{f_max_t:.1f} °C")
  with col2:
    st.metric(label="📉 Min. teplota v období", value=f"{f_min_t:.1f} °C")
  with col3:
    st.metric(label="💨 Max. vietor v období", value=f"{f_max_v:.1f} km/h")
  with col4:
    st.metric(label="🌧️ Úhrn zrážok v období", value=f"{f_sum_z:.1f} mm")
else:
  st.warning("Pre zvolené obdobie nie sú k dispozícii žiadne dáta.")

# --- ĎALŠIA ČASŤ APLIKÁCIE (Grafy a tabuľky) ---
st.markdown("---")
st.subheader("📈 Graf vývoja teploty v čase")
if not df_filtered.empty:
  st.line_chart(df_filtered.set_index("Datum")["Teplota"])
