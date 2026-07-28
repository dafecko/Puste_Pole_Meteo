import datetime
from playwright.sync_api import sync_playwright
import pandas as pd


def scrape_weather():
  url = "https://app.weathercloud.net/d8797717349#current"
  print("Sťahujem kompletné dáta z Weathercloud...")

  teplota, vlhkost, zrazky, uv_index, vietor = "0", "0", "0", "0", "0"

  with sync_playwright() as p:
    # headless=True zabezpečí, že sa okno prehliadača nebude otvárať na obrazovke
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)

    # Počkáme 8 sekúnd na načítanie stránky
    page.wait_for_timeout(8000)

    # Odstránime prekážajúce okno cookies/consent
    try:
      page.evaluate(
          "const overlay = document.querySelector('.fc-consent-root'); if"
          " (overlay) overlay.remove();"
      )
    except Exception:
      pass

    # 1. Zber údajov zo záložky Current (Teplota, Vlhkosť, Zrážky, UV index)
    try:
      el = page.locator("#temp .temp-value-text")
      if el.count() > 0:
        teplota = el.first.text_content()
    except Exception as e:
      print(f"Teplota chyba: {e}")

    try:
      el = page.locator("#hum .hum-value-text")
      if el.count() > 0:
        vlhkost = el.first.text_content()
    except Exception as e:
      print(f"Vlhkosť chyba: {e}")

    try:
      el = page.locator("#rain .rain-value-text")
      if el.count() > 0:
        zrazky = el.first.text_content()
    except Exception as e:
      print(f"Zrážky chyba: {e}")

    try:
      el = page.locator("#uvi .uvi-value-text")
      if el.count() > 0:
        uv_index = el.first.text_content()
    except Exception as e:
      print(f"UV index chyba: {e}")

    # 2. Prechod na záložku Wind a zber hodnoty vetra
    try:
      page.locator("a[href*='wind']").first.click()
      page.wait_for_timeout(5000)

      el_wind = page.locator("#wspd .wspd-value-text")
      if el_wind.count() > 0:
        vietor = el_wind.first.text_content()
    except Exception as e:
      print(f"Vietor chyba: {e}")

    browser.close()

  # Funkcia na očistenie textu na čisté desatinné číslo
  def clean_val(val):
    if not val:
      return 0.0
    cleaned = "".join([c for c in str(val) if c.isdigit() or c in [".", "-"]])
    try:
      return float(cleaned)
    except:
      return 0.0

  t_val = clean_val(teplota)
  h_val = clean_val(vlhkost)
  r_val = clean_val(zrazky)
  uv_val = clean_val(uv_index)

  # Prepočet vetra z m/s na km/h (* 3.6)
  w_val_ms = clean_val(vietor)
  w_val = round(w_val_ms * 3.6, 1)

  teraz = datetime.datetime.now()
  data = [{
      "Dátum": teraz.strftime("%d.%m.%Y"),
      "Čas": teraz.strftime("%H:%M"),
      "Teplota (°C)": t_val,
      "Vlhkosť (%)": h_val,
      "Zrážky (mm)": r_val,
      "Vietor (km/h)": w_val,
      "UV index": uv_val,
  }]

  df = pd.DataFrame(data)
  # Uloženie do CSV s prepísaním starého súboru
  df.to_csv(
      "meteo_aktualne.csv", sep=";", decimal=",", index=False, encoding="utf-8-sig"
  )
  print(
      f"✅ Hotovo! Teplota={t_val}, Vlhkosť={h_val}, Zrážky={r_val},"
      f" Vietor={w_val} km/h, UV index={uv_val}"
  )


if __name__ == "__main__":
  scrape_weather()