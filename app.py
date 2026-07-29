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
        min-height: 240px; /* Zabezpečí rovnakú výšku pre všetky karty */
        justify-content: space-between; /* Rovnomerne rozmiestni obsah v karte */
    }
    .card-title {
        font-size: 1.0em;
        font-weight: 600;
        color: #555;
        margin-bottom: 5px;
        height: 45px; /* Pevná výška pre nadpis, aby sa 1-riadkové a 2-riadkové názvy zarovnali narovnako */
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .main-value {
        font-size: 1.6em;
        font-weight: bold;
        color: #2c3e50;
        margin: 8px 0 0 0;
    }
    
    /* Zvyšok tvojich štýlov ostáva nezmenený ... */
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
