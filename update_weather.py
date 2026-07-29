import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
import pandas as pd


def scrape_weather():
  url = "https://app.weathercloud.net/d8797717349#current"
  print(
      "Sťahujem kompletnú sadu meteorologických údajov z Weathercloud"
      " (vrátane tlaku, smeru vetra a pocitových teplôt)..."
  )

  teplota, vlhkost, zrazky, uv_index = "0", "0", "0", "0"
  tlak, pocitova_chill, heat_index, rosny_bod = "0", "0", "0", "0"
  vietor, smer_vetra = "0", "0"

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_timeout(8000)

    try:
      page.evaluate(
          "const overlay = document.querySelector('.fc-consent-root'); if"
          " (overlay) overlay.remove();"
      )
    except Exception:
      pass

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
      el = page.locator("#bar .bar-value-text")
      if el.count() > 0:
        tlak = el.first.text_content()
    except Exception as e:
      print(f"Tlak chyba: {e}")

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

    try:
      el = page.locator("#chill .chill-value-text")
      if el.count() > 0:
        pocitova_chill = el.first.text_content()
    except Exception as e:
      print(f"Wind Chill chyba: {e}")

    try:
      el = page.locator("#heat .heat-value-text")
      if el.count() > 0:
        heat_index = el.first.text_content()
    except Exception as e:
      print(f"Heat Index chyba: {e}")

    try:
      el = page.locator("#dew .dew-value-text")
      if el.count() > 0:
        rosny_bod = el.first.text_content()
    except Exception as e:
      print(f"Rosný bod chyba: {e}")

    try:
      page.locator("a[href*='wind']").first.click()
      page.wait_for_timeout(4000)

      el_wind = page.locator("#wspd .wspd-value-text")
      if el_wind.count() > 0:
        vietor = el_wind.first.text_content()

      el_wdir = page.locator("#wdir .wdir-value-text")
      if el_wdir.count() > 0:
        smer_vetra = el_wdir.first.text_content()
    except Exception as e:
      print(f"Vietor / Smer vetra chyba: {e}")

    browser.close()

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
  p_val = clean_val(tlak)
  chill_val = clean_val(pocitova_chill)
  heat_val = clean_val(heat_index)
  dew_val = clean_val(rosny_bod)

  w_val_ms = clean_val(vietor)
  w_val = round(w_val_ms * 3.6, 1)

  # Dôsledné vyčistenie smeru vetra od znakov °, "deg" a medzier už pri zbere
  smer_str = (
      str(smer_vetra).replace("°", "").replace("deg", "").strip()
  )
  if not smer_str:
    smer_str = "-"

  teraz = datetime.datetime.now(ZoneInfo("Europe/Bratislava"))

  data = [{
      "Dátum": teraz.strftime("%d.%m.%Y"),
      "Čas": teraz.strftime("%H:%M"),
      "Teplota (°C)": t_val,
      "Wind Chill (°C)": chill_val,
      "Heat Index (°C)": heat_val,
      "Rosný bod (°C)": dew_val,
      "Vlhkosť (%)": h_val,
      "Tlak (hPa)": p_val,
      "Zrážky (mm)": r_val,
      "Vietor (km/h)": w_val,
      "Smer vetra": smer_str,
      "UV index": uv_val,
  }]

  df = pd.DataFrame(data)
  df.to_csv(
      "meteo_aktualne.csv", sep=";", decimal=",", index=False, encoding="utf-8-sig"
  )
  print(
      f"✅ Hotovo! Dáta úspešne uložené do meteo_aktualne.csv (Tlak:"
      f" {p_val} hPa, Smer: {smer_str}, Heat: {heat_val}°C, Chill:"
      f" {chill_val}°C, Rosný bod: {dew_val}°C)"
  )


if __name__ == "__main__":
  scrape_weather()
