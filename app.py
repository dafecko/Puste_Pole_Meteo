import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Nastavenie stránky na šírku
st.set_page_config(page_title="Meteo Web Dashboard - Pusté Pole", layout="wide")

CSV_FILE = "meteo_puste_pole_v2.csv"

@st.cache_data
def load_data():
    if not os.path.exists(CSV_FILE):
        return None
    df = pd.read_csv(CSV_FILE, sep=';', decimal=',')
    col_datum = next((c for c in df.columns if 'dátum' in c.lower() or 'datum' in c.lower()), None)
    col_cas = next((c for c in df.columns if 'čas' in c.lower() or 'cas' in c.lower()), None)
    
    if not col_datum or not col_cas:
        return df
    
    df['DateTime'] = pd.to_datetime(
        df[col_datum].astype(str) + ' ' + df[col_cas].astype(str),
        format='%d.%m.%Y %H:%M',
        errors='coerce'
    )
    df = df.dropna(subset=['DateTime']).sort_values('DateTime')
    
    # Bezpečná konverzia všetkých číselných stĺpcov na čísla
    for col in df.columns:
        if col not in [col_datum, col_cas, 'DateTime']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
            
    return df

df = load_data()

if df is None or df.empty:
    st.error(f"Súbor '{CSV_FILE}' nebol na ploche nájdený alebo je prázdny!")
else:
    st.title("🌤️ Meteorologický Web Dashboard - Pusté Pole")

    # Bočný panel (Sidebar) pre výber obdobia
    st.sidebar.header("⚙️ Ovládací panel")
    volba = st.sidebar.radio(
        "Vyberte spôsob zobrazenia:",
        [
            "1 - Celé obdobie",
            "2 - Konkrétny rok",
            "3 - Konkrétny mesiac a rok",
            "4 - Vlastné obdobie (od - do)"
        ]
    )

    min_d = df['DateTime'].min().date()
    max_d = df['DateTime'].max().date()
    
    df_filtered = df.copy()

    if "2" in volba:
        dostupne_roky = sorted(df['DateTime'].dt.year.unique())
        vybrany_rok = st.sidebar.selectbox("Vyberte rok", dostupne_roky)
        df_filtered = df_filtered[df_filtered['DateTime'].dt.year == vybrany_rok]

    elif "3" in volba:
        dostupne_roky = sorted(df['DateTime'].dt.year.unique())
        vybrany_rok = st.sidebar.selectbox("Vyberte rok", dostupne_roky)
        vybrany_mesiac = st.sidebar.selectbox(
            "Vyberte mesiac", 
            list(range(1, 13)), 
            format_func=lambda x: ["Január", "Február", "Marec", "Apríl", "Máj", "Jún", "Júl", "August", "September", "Október", "November", "December"][x-1]
        )
        df_filtered = df_filtered[(df_filtered['DateTime'].dt.year == vybrany_rok) & (df_filtered['DateTime'].dt.month == vybrany_mesiac)]

    elif "4" in volba:
        datum_od = st.sidebar.date_input("Dátum od", min_d)
        datum_do = st.sidebar.date_input("Dátum do", max_d)
        df_filtered = df_filtered[(df_filtered['DateTime'].dt.date >= datum_od) & (df_filtered['DateTime'].dt.date <= datum_do)]

    if df_filtered.empty:
        st.warning("⚠️ Pre zvolené obdobie sa nenašli žiadne dáta.")
    else:
        # Identifikácia stĺpcov
        t_max = next((c for c in df_filtered.columns if 'tepl' in c.lower() and 'max' in c.lower()), None)
        t_avg = next((c for c in df_filtered.columns if 'tepl' in c.lower() and ('priem' in c.lower() or 'avg' in c.lower())), None)
        t_min = next((c for c in df_filtered.columns if 'tepl' in c.lower() and 'min' in c.lower()), None)

        w_max = next((c for c in df_filtered.columns if 'viet' in c.lower() and 'max' in c.lower()), None)
        w_avg = next((c for c in df_filtered.columns if 'viet' in c.lower() and ('priem' in c.lower() or 'avg' in c.lower())), None)
        w_min = next((c for c in df_filtered.columns if 'viet' in c.lower() and 'min' in c.lower()), None)

        r_col = next((c for c in df_filtered.columns if any(k in c.lower() for k in ['zráž', 'zraz', 'rain', 'uhrn', 'precipitation'])), None)

        max_temp = df_filtered[t_max].max() if t_max and not df_filtered[t_max].isna().all() else 0
        avg_temp = df_filtered[t_avg].mean() if t_avg and not df_filtered[t_avg].isna().all() else 0
        max_wind = df_filtered[w_max].max() if w_max and not df_filtered[w_max].isna().all() else 0
        total_rain = df_filtered[r_col].sum() if r_col and not df_filtered[r_col].isna().all() else 0

        # Rýchle KPI karty na vrchu webu
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔴 Max Teplota", f"{max_temp:.1f} °C")
        col2.metric("🟠 Priemerná Teplota", f"{avg_temp:.1f} °C")
        col3.metric("🟣 Max Vietor", f"{max_wind:.1f} km/h")
        col4.metric("🔵 Celkové Zrážky", f"{total_rain:.1f} mm")

        st.markdown("---")

        # Vykreslenie interaktívnych Plotly grafov
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=(
                "Teplota (°C)",
                "Rýchlosť vetra (km/h)",
                "Zrážky (mm)"
            )
        )

        if t_max:
            fig.add_trace(go.Scatter(x=df_filtered['DateTime'], y=df_filtered[t_max], name="Teplota Max", line=dict(color='#d9534f', width=2)), row=1, col=1)
        if t_avg:
            fig.add_trace(go.Scatter(x=df_filtered['DateTime'], y=df_filtered[t_avg], name="Teplota Priemer", line=dict(color='#f0ad4e', width=2)), row=1, col=1)
        if t_min:
            fig.add_trace(go.Scatter(x=df_filtered['DateTime'], y=df_filtered[t_min], name="Teplota Min", line=dict(color='#5bc0de', width=2)), row=1, col=1)

        if w_max:
            fig.add_trace(go.Scatter(x=df_filtered['DateTime'], y=df_filtered[w_max], name="Vietor Max", line=dict(color='#8e44ad', width=2)), row=2, col=1)
        if w_avg:
            fig.add_trace(go.Scatter(x=df_filtered['DateTime'], y=df_filtered[w_avg], name="Vietor Priemer", line=dict(color='#27ae60', width=2)), row=2, col=1)
        if w_min:
            fig.add_trace(go.Scatter(x=df_filtered['DateTime'], y=df_filtered[w_min], name="Vietor Min", line=dict(color='#16a085', width=2)), row=2, col=1)

        # Stĺpcový graf zrážok s vynútenou šírkou stĺpca (43200000 ms = 12 hodín, aby boli dobre viditeľné)
        if r_col:
            fig.add_trace(go.Bar(
                x=df_filtered['DateTime'], 
                y=df_filtered[r_col], 
                name="Zrážky (mm)", 
                marker_color='#3498db',
                width=43200000 
            ), row=3, col=1)

        fig.update_layout(
            height=800,
            template="plotly_white",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Rozbaľovacia tabuľka s podrobnými dátami
        with st.expander("📋 Zobraziť zdrojovú tabuľku dát pre vybrané obdobie"):
            st.dataframe(df_filtered)