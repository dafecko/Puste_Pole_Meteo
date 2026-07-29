import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Nastavenie stránky na šírku
st.set_page_config(page_title="Meteo Web Dashboard - Pusté Pole", layout="wide")

# Vlastné CSS štýly pre grafické karty, detailné stupnice a opravené farebné škály ciferníkov
st.markdown(
    """
    <style>
    .weather-card {
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        padding: 15px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        margin-bottom: 10px;
    }
    .card-title {
        font-size: 1.0em;
        font-weight: 600;
        color: #555;
        margin-bottom: 10px;
    }
    .main-value {
        font-size: 1.6em;
        font-weight: bold;
        color: #2c3e50;
        margin: 8px 0 0 0;
    }
    
    /* Štýly pre vertikálne stupnice (teplomer, zrážky) */
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
        color: #7f8c8d;
        text-align: right;
    }
    .thermometer-box, .rain-box {
        height: 100px;
        width: 16px;
        background: #e0e0e0;
        border-radius: 8px;
        position: relative;
        overflow: hidden;
    }
    .thermometer-fill {
        position: absolute;
        bottom: 0;
        width: 100%;
        background: linear-gradient(to top, #3498db, #e74c3c);
        transition: height 0.5s ease;
    }
    .rain-fill {
        position: absolute;
        bottom: 0;
        width: 100%;
        background: #3498db;
        transition: height 0.5s ease;
    }

    /* Štýly pre kruhové ciferníky s farebnými škálami */
    .gauge-circle {
        width: 110px;
        height: 110px;
        border-radius: 50%;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle, #ffffff 62%, #f8f9fa 100%);
        margin: 5px auto;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05), 0 2px 6px rgba(0,0,0,0.05);
    }
    
    /* Farebné okraje pre jednotlivé typy ciferníkov (opravený plný 270-stupňový rozsah) */
    .gauge-hum {
        border: 5px solid transparent;
        background-image: linear-gradient(#ffffff, #ffffff), conic-gradient(from 225deg, #e67e22 0deg, #2ecc71 135deg, #3498db 270deg, transparent 270deg);
        background-origin: border-box;
        background-clip: content-box, border-box;
    }
    .gauge-wind {
        border: 5px solid transparent;
        background-image: linear-gradient(#ffffff, #ffffff), conic-gradient(from 225deg, #2ecc71 0deg, #f1c40f 100deg, #e67e22 180deg, #e74c3c 270deg, transparent 270deg);
        background-origin: border-box;
        background-clip: content-box, border-box;
    }
    .gauge-uv {
        border: 5px solid transparent;
        background-image: linear-gradient(#ffffff, #ffffff), conic-gradient(from 225deg, #2ecc71 0deg 67.5deg, #f1c40f 67.5deg 135deg, #e67e22 135deg 180deg, #e74c3c 180deg 247.5deg, #9b59b6 247.5deg 270deg, transparent 270deg);
        background-origin: border-box;
        background-clip: content-box, border-box;
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
        width: 9px;
        height: 9px;
        background: #2c3e50;
        border-radius: 50%;
        z-index: 4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    /* Pozície pre hustejšie hodnoty na ciferníku */
    .scale-val {
        position: absolute;
        font-size: 8px;
        font-weight: 700;
        color: #7f8c8d;
    }
    .s-0   { bottom: 18px; left: 15px; }
    .s-20  { top: 42px; left: 12px; }
    .s-40  { top: 14px; left: 32px; }
    .s-60  { top: 14px; right: 32px; }
    .s-80  { top: 42px; right: 12px; }
    .s-100 { bottom: 18px; right: 15px; }
    
    .scale-unit {
        position: absolute;
        bottom: 12px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 8px;
        font-weight: 600;
        color: #95a5a6;
    }
    </style>
""",
    unsafe_allow_html=True,
)

CSV_FILE = "meteo_puste_pole_v2.csv"
CSV_AKTUALNE = "meteo_aktualne.csv"


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
    except Exception as e:
      st.error(f"Nepodarilo sa načítať historický CSV súbor: {e}")
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
      format="%d.%m.%Y %H:%M",
      errors="coerce",
  )
  df = df.dropna(subset=["DateTime"]).sort_values("DateTime")

  for col in df.columns:
    if col not in [col_datum, col_cas, "DateTime"]:
      df[col] = pd.to_numeric(
          df[col].astype(str).str.replace(",", "."), errors="coerce"
      )

  return df


# --- HLAVNÁ STRÁNKA ---
st.title("🌤️ Meteorologický Web Dashboard - Pusté Pole")

# 1. SEKCIA: AKTUÁLNE ÚDAJE
st.subheader("⚡ Aktuálny stav počasia")

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

      st.caption(f"📅 Posledná aktualizácia zo stanice: {datum_str} o {cas_str}")

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

      t_val = get_val(akt, ["teplota", "temp"])
      h_val = get_val(akt, ["vlhkosť", "vlhkost", "hum"])
      w_val = get_val(akt, ["vietor", "wind", "wspd"])
      r_val = get_val(akt, ["zrážky", "zrazky", "rain"])
      uv_val = get_val(akt, ["uv", "uvi"])

      # Výpočty pre grafické prvky (rozsah 270 stupňov pre ciferníky)
      temp_pct = min(100, max(0, ((t_val + 20) / 70) * 100))
      rain_pct = min(100, max(0, (r_val / 50) * 100))

      hum_angle = (h_val / 100) * 270 - 135
      wind_angle = min(135, max(-135, (w_val / 50) * 270 - 135))
      uv_angle = min(135, max(-135, (uv_val / 12) * 270 - 135))

      col1, col2, col3, col4, col5 = st.columns(5)

      with col1:
        st.markdown(
            f"""
                <div class="weather-card">
                    <div class="card-title">Teplota</div>
                    <div class="bar-container">
                        <div class="bar-scale">
                            <span>50°</span>
                            <span>25°</span>
                            <span>0°</span>
                            <span>-20°</span>
                        </div>
                        <div class="thermometer-box">
                            <div class="thermometer-fill" style="height: {temp_pct}%;"></div>
                        </div>
                    </div>
                    <div class="main-value">{t_val:.1f} °C</div>
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
                        <div class="scale-val s-0">0</div>
                        <div class="scale-val s-20">20</div>
                        <div class="scale-val s-40">40</div>
                        <div class="scale-val s-60">60</div>
                        <div class="scale-val s-80">80</div>
                        <div class="scale-val s-100">100</div>
                        <div class="scale-unit">%</div>
                        <div class="gauge-needle" style="transform: translateX(-50%) rotate({hum_angle}deg);"></div>
                        <div class="gauge-center-dot"></div>
                    </div>
                    <div class="main-value">{h_val:.0f} %</div>
                </div>
                """,
            unsafe_allow_html=True,
        )

      with col3:
        st.markdown(
            f"""
                <div class="weather-card">
                    <div class="card-title">Rýchlosť vetra</div>
                    <div class="gauge-circle gauge-wind">
                        <div class="scale-val s-0">0</div>
                        <div class="scale-val s-20">10</div>
                        <div class="scale-val s-40">20</div>
                        <div class="scale-val s-60">30</div>
                        <div class="scale-val s-80">40</div>
                        <div class="scale-val s-100">50</div>
                        <div class="scale-unit">km/h</div>
                        <div class="gauge-needle" style="transform: translateX(-50%) rotate({wind_angle}deg);"></div>
                        <div class="gauge-center-dot"></div>
                    </div>
                    <div class="main-value">{w_val:.1f} km/h</div>
                </div>
                """,
            unsafe_allow_html=True,
        )

      with col4:
        st.markdown(
            f"""
                <div class="weather-card">
                    <div class="card-title">Zrážky</div>
                    <div class="bar-container">
                        <div class="bar-scale">
                            <span>50</span>
                            <span>35</span>
                            <span>20</span>
                            <span>0</span>
                        </div>
                        <div class="rain-box">
                            <div class="rain-fill" style="height: {rain_pct}%;"></div>
                        </div>
                    </div>
                    <div class="main-value">{r_val:.1f} mm</div>
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
                    <div class="main-value">{uv_val:.1f}</div>
                </div>
                """,
            unsafe_allow_html=True,
        )

    else:
      st.warning("Súbor 'meteo_aktualne.csv' je prázdny.")
  except Exception as e:
    st.error(f"Chyba pri čítaní 'meteo_aktualne.csv': {e}")
else:
  st.info("Súbor 'meteo_aktualne.csv' sa zatiaľ nenašiel v repozitári.")

st.markdown("---")

# 2. NAČÍTANIE HISTORICKÝch DÁT PRE GRAFY
df = load_data()

if df is None or df.empty:
  st.warning(f"⚠️ Historický súbor '{CSV_FILE}' nebol nájdený alebo je prázdny.")
else:
  st.sidebar.header("⚙️ Ovládací panel")
  volba = st.sidebar.radio(
      "Vyberte spôsob zobrazenia:",
      [
          "1 - Celé obdobie",
          "2 - Konkrétny rok",
          "3 - Konkrétny mesiac a rok",
          "4 - Vlastné obdobie (od - do)",
      ],
  )

  min_d = df["DateTime"].min().date()
  max_d = df["DateTime"].max().date()

  df_filtered = df.copy()

  if "2" in volba:
    dostupne_roky = sorted(df["DateTime"].dt.year.unique())
    vybrany_rok = st.sidebar.selectbox("Vyberte rok", dostupne_roky)
    df_filtered = df_filtered[df_filtered["DateTime"].dt.year == vybrany_rok]

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

  elif "4" in volba:
    datum_od = st.sidebar.date_input("Dátum od", min_d)
    datum_do = st.sidebar.date_input("Dátum do", max_d)
    df_filtered = df_filtered[
        (df_filtered["DateTime"].dt.date >= datum_od)
        & (df_filtered["DateTime"].dt.date <= datum_do)
    ]

  if df_filtered.empty:
    st.warning("⚠️ Pre zvolené obdobie sa nenašli žiadne dáta.")
  else:
    t_max = next(
        (
            c
            for c in df_filtered.columns
            if "tepl" in c.lower() and "max" in c.lower()
        ),
        None,
    )
    t_avg = next(
        (
            c
            for c in df_filtered.columns
            if "tepl" in c.lower()
            and ("priem" in c.lower() or "avg" in c.lower())
        ),
        None,
    )
    t_min = next(
        (
            c
            for c in df_filtered.columns
            if "tepl" in c.lower() and "min" in c.lower()
        ),
        None,
    )

    w_max = next(
        (
            c
            for c in df_filtered.columns
            if "viet" in c.lower() and "max" in c.lower()
        ),
        None,
    )
    w_avg = next(
        (
            c
            for c in df_filtered.columns
            if "viet" in c.lower()
            and ("priem" in c.lower() or "avg" in c.lower())
        ),
        None,
    )
    w_min = next(
        (
            c
            for c in df_filtered.columns
            if "viet" in c.lower() and "min" in c.lower()
        ),
        None,
    )

    r_col = next(
        (
            c
            for c in df_filtered.columns
            if any(
                k in c.lower()
                for k in ["zráž", "zraz", "rain", "uhrn", "precipitation"]
            )
        ),
        None,
    )

    max_temp = (
        df_filtered[t_max].max()
        if t_max and not df_filtered[t_max].isna().all()
        else 0
    )
    avg_temp = (
        df_filtered[t_avg].mean()
        if t_avg and not df_filtered[t_avg].isna().all()
        else 0
    )
    max_wind = (
        df_filtered[w_max].max()
        if w_max and not df_filtered[w_max].isna().all()
        else 0
    )
    total_rain = (
        df_filtered[r_col].sum()
        if r_col and not df_filtered[r_col].isna().all()
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔴 Max Teplota (Obdobie)", f"{max_temp:.1f} °C")
    col2.metric("🟠 Priemerná Teplota (Obdobie)", f"{avg_temp:.1f} °C")
    col3.metric("🟣 Max Vietor (Obdobie)", f"{max_wind:.1f} km/h")
    col4.metric("🔵 Celkové Zrážky (Obdobie)", f"{total_rain:.1f} mm")

    st.markdown("---")

    # 1. GRAF: TEPLOTY
    fig_temp = go.Figure()
    if t_max:
      fig_temp.add_trace(
          go.Scatter(
              x=df_filtered["DateTime"],
              y=df_filtered[t_max],
              name="Teplota Max",
              line=dict(color="#d9534f", width=2),
          )
      )
    if t_avg:
      fig_temp.add_trace(
          go.Scatter(
              x=df_filtered["DateTime"],
              y=df_filtered[t_avg],
              name="Teplota Priemer",
              line=dict(color="#f0ad4e", width=2),
          )
      )
    if t_min:
      fig_temp.add_trace(
          go.Scatter(
              x=df_filtered["DateTime"],
              y=df_filtered[t_min],
              name="Teplota Min",
              line=dict(color="#5bc0de", width=2),
          )
      )

    fig_temp.update_layout(
        title="Teplota (°C)",
        height=320,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )
    fig_temp.update_xaxes(hoverformat="%d.%m.%Y")
    st.plotly_chart(fig_temp, use_container_width=True)

    # 2. GRAF: VIETOR
    fig_wind = go.Figure()
    if w_max:
      fig_wind.add_trace(
          go.Scatter(
              x=df_filtered["DateTime"],
              y=df_filtered[w_max],
              name="Vietor Max",
              line=dict(color="#8e44ad", width=2),
          )
      )
    if w_avg:
      fig_wind.add_trace(
          go.Scatter(
              x=df_filtered["DateTime"],
              y=df_filtered[w_avg],
              name="Vietor Priemer",
              line=dict(color="#27ae60", width=2),
          )
      )
    if w_min:
      fig_wind.add_trace(
          go.Scatter(
              x=df_filtered["DateTime"],
              y=df_filtered[w_min],
              name="Vietor Min",
              line=dict(color="#16a085", width=2),
          )
      )

    fig_wind.update_layout(
        title="Rýchlosť vetra (km/h)",
        height=320,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )
    fig_wind.update_xaxes(hoverformat="%d.%m.%Y")
    st.plotly_chart(fig_wind, use_container_width=True)

    # 3. GRAF: ZRÁŽKY
    fig_rain = go.Figure()
    if r_col:
      fig_rain.add_trace(
          go.Bar(
              x=df_filtered["DateTime"],
              y=df_filtered[r_col],
              name="Zrážky (mm)",
              marker_color="#3498db",
              width=21600000,
          )
      )

    fig_rain.update_layout(
        title="Zrážky (mm)",
        height=320,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )
    fig_rain.update_xaxes(hoverformat="%d.%m.%Y")
    st.plotly_chart(fig_rain, use_container_width=True)

    with st.expander("📋 Zobraziť zdrojovú tabuľku dát pre vybrané obdobie"):
      col_cas_tab = next(
          (
              c
              for c in df_filtered.columns
              if "čas" in c.lower() or "cas" in c.lower()
          ),
          None,
      )
      cols_to_hide = [col_cas_tab, "DateTime"] if col_cas_tab else ["DateTime"]
      df_table = df_filtered.drop(
          columns=[c for c in cols_to_hide if c in df_filtered.columns],
          errors="ignore",
      )
      st.dataframe(df_table)
