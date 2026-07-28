import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Nastavenie stránky na šírku
st.set_page_config(page_title="Meteo Web Dashboard - Pusté Pole", layout="wide")

CSV_FILE = "meteo_puste_pole_v2.csv"
CSV_AKTUALNE = "meteo_aktualne.csv"


@st.cache_data
def load_data():
  if not os.path.exists(CSV_FILE):
    return None
  try:
    df = pd.read_csv(CSV_FILE, sep=";", decimal=",")
  except Exception:
    try:
      df = pd.read_csv(CSV_FILE, sep=",", decimal=".")
    except Exception as e:
      st.error(f"Nepodarilo sa načítať historický CSV súbor: {e}")
      return None

  # Hľadanie stĺpcov pre dátum a čas
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

  # Bezpečná konverzia všetkých číselných stĺpcov na čísla
  for col in df.columns:
    if col not in [col_datum, col_cas, "DateTime"]:
      df[col] = pd.to_numeric(
          df[col].astype(str).str.replace(",", "."), errors="coerce"
      )

  return df


# --- HLAVNÁ STRÁNKA ---
st.title("🌤️ Meteorologický Web Dashboard - Pusté Pole")

# 1. SEKCIA: AKTUÁLNE ÚDAJE (Moderné ciferníky / Gauges)
st.subheader("⚡ Aktuálny stav počasia")


def create_gauge(val, title, max_val, unit, min_val=0):
  try:
    numeric_val = float(val)
  except:
    numeric_val = 0.0

  fig = go.Figure(
      go.Indicator(
          mode="gauge+number",
          value=numeric_val,
          title={
              "text": f"{title} ({unit})" if unit else title,
              "font": {"size": 14, "color": "#31333F"},
          },
          number={"font": {"size": 22}},
          gauge={
              "axis": {
                  "range": [min_val, max_val],
                  "tickwidth": 1,
                  "tickcolor": "gray",
              },
              "bar": {"color": "#0284c7"},
              "bgcolor": "#f8fafc",
              "borderwidth": 1,
              "bordercolor": "#cbd5e1",
          },
      )
  )
  fig.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10))
  return fig


if os.path.exists(CSV_AKTUALNE):
  try:
    try:
      df_akt = pd.read_csv(CSV_AKTUALNE, sep=";", decimal=",")
    except:
      df_akt = pd.read_csv(CSV_AKTUALNE, sep=",", decimal=".")

    if not df_akt.empty:
      akt = df_akt.iloc[0]
      datum_str = akt.get("Dátum", akt.get("datum", ""))
      cas_str = akt.get("Čas", akt.get("cas", ""))

      st.caption(f"📅 Posledná aktualizácia zo stanice: {datum_str} o {cas_str}")

      col_a, col_b, col_c, col_d, col_e = st.columns(5)


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

      with col_a:
        st.plotly_chart(
            create_gauge(t_val, "Teplota", 50, "°C", min_val=-20),
            use_container_width=True,
        )
      with col_b:
        st.plotly_chart(
            create_gauge(h_val, "Vlhkosť", 100, "%", min_val=0),
            use_container_width=True,
        )
      with col_c:
        st.plotly_chart(
            create_gauge(w_val, "Vietor", 50, "km/h", min_val=0),
            use_container_width=True,
        )
      with col_d:
        st.plotly_chart(
            create_gauge(r_val, "Zrážky", 50, "mm", min_val=0),
            use_container_width=True,
        )
      with col_e:
        st.plotly_chart(
            create_gauge(uv_val, "UV index", 12, "", min_val=0),
            use_container_width=True,
        )
    else:
      st.warning("Súbor 'meteo_aktualne.csv' je prázdny.")
  except Exception as e:
    st.error(f"Chyba pri čítaní 'meteo_aktualne.csv': {e}")
else:
  st.info("Súbor 'meteo_aktualne.csv' sa zatiaľ nenašiel v repozitári.")

st.markdown("---")

# 2. NAČÍTANIE HISTORICKÝCH DÁT PRE GRAFY
df = load_data()

if df is None or df.empty:
  st.warning(f"⚠️ Historický súbor '{CSV_FILE}' nebol nájdený alebo je prázdny.")
else:
  # Bočný panel (Sidebar) pre výber obdobia
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
    # Identifikácia stĺpcov pre grafy
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

    # KPI karty pre vybrané obdobie
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

    # Rozbaľovacia tabuľka
    with st.expander("📋 Zobraziť zdrojovú tabuľku dát pre vybrané obdobie"):
      col_cas = next(
          (
              c
              for c in df_filtered.columns
              if "čas" in c.lower() or "cas" in c.lower()
          ),
          None,
      )
      cols_to_hide = [col_cas, "DateTime"] if col_cas else ["DateTime"]
      df_table = df_filtered.drop(
          columns=[c for c in cols_to_hide if c in df_filtered.columns],
          errors="ignore",
      )
      st.dataframe(df_table)