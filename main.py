import sys
print("✅ Python arrancó", flush=True)
import time
print("✅ time OK", flush=True)
import random
print("✅ random OK", flush=True)
import urllib.parse
print("✅ urllib OK", flush=True)
import requests
print("✅ requests OK", flush=True)
import os
print("✅ os OK", flush=True)
from datetime import datetime
print("✅ datetime OK", flush=True)
print("🔧 Importando Selenium...", flush=True)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
print("✅ Selenium OK", flush=True)

TELEFONO      = os.environ.get("TELEFONO", "")
CALLMEBOT_KEY = os.environ.get("CALLMEBOT_KEY", "")
LEGO_URL      = os.environ.get("LEGO_URL", "https://www.lego.com/es-mx/product/project-hail-mary-11389")
INTERVALO_MIN = int(os.environ.get("INTERVALO_MIN", "30"))

def crear_driver():
    print("🔧 Creando driver...", flush=True)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    driver  = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    print("✅ Driver creado OK", flush=True)
    return driver

def esta_disponible(driver):
    try:
        driver.get(LEGO_URL)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "button")))
        time.sleep(random.uniform(3, 5))
        botones = driver.find_elements(By.TAG_NAME, "button")
        for b in botones:
            txt = b.text.strip()
            if "añadir a la bolsa" in txt.lower():
                if b.is_displayed() and b.is_enabled():
                    print(f"  ✅ Botón activo: '{txt}'", flush=True)
                    return True
                else:
                    print(f"  ⚠️  Botón deshabilitado: '{txt}'", flush=True)
                    return False
        print("  ❌ Botón no encontrado", flush=True)
        return False
    except Exception as e:
        print(f"  [ERROR] {e}", flush=True)
    return False

def enviar_whatsapp(mensaje):
    texto = urllib.parse.quote(mensaje)
    url   = (
        f"https://api.callmebot.com/whatsapp.php"
        f"?phone={TELEFONO}&text={texto}&apikey={CALLMEBOT_KEY}"
    )
    try:
        r = requests.get(url, timeout=10)
        print(f"  [WhatsApp] status {r.status_code}", flush=True)
    except Exception as e:
        print(f"  [WhatsApp ERROR] {e}", flush=True)

def main():
    print("🔍 Iniciando scraper LEGO — Project Hail Mary", flush=True)
    print(f"⏱  Revisando cada {INTERVALO_MIN} minutos\n", flush=True)

    driver              = crear_driver()
    alerta_enviada      = False
    sin_stock_desde     = datetime.now()
    checks_sin_stock    = 0
    checks_hoy          = 0
    ultimo_reporte      = datetime.now()

    try:
        while True:
            ts  = datetime.now().strftime("%H:%M:%S")
            now = datetime.now()
            print(f"[{ts}] Revisando stock...", flush=True)

            disponible = esta_disponible(driver)
            checks_sin_stock += 1
            checks_hoy       += 1

            if disponible:
                dias  = (now - sin_stock_desde).days
                horas = (now - sin_stock_desde).seconds // 3600
                print(f"[{ts}] Stock: ✅ SÍ — mandando WhatsApp!\n", flush=True)
                if not alerta_enviada:
                    enviar_whatsapp(
                        f"🧱 LEGO Project Hail Mary disponible!\n"
                        f"⏳ Estuvo sin stock {dias}d {horas}h\n"
                        f"🔍 Revisiones totales: {checks_sin_stock}\n"
                        f"🔗 {LEGO_URL}"
                    )
                    alerta_enviada   = True
                    checks_sin_stock = 0
                    sin_stock_desde  = now
            else:
                dias  = (now - sin_stock_desde).days
                horas = (now - sin_stock_desde).seconds // 3600
                print(f"[{ts}] Stock: ❌ NO  |  Sin stock: {dias}d {horas}h  |  Revisiones: {checks_sin_stock}\n", flush=True)
                alerta_enviada = False

            # ── REPORTE DIARIO ─────────────────────────────
            horas_desde_reporte = (now - ultimo_reporte).total_seconds() / 3600
            if horas_desde_reporte >= 24:
                dias  = (now - sin_stock_desde).days
                horas = (now - sin_stock_desde).seconds // 3600
                enviar_whatsapp(
                    f"📊 Reporte diario LEGO Hail Mary\n"
                    f"❌ Sin stock\n"
                    f"⏳ Llevamos {dias}d {horas}h sin existencia\n"
                    f"🔍 Revisiones hoy: {checks_hoy}\n"
                    f"🔍 Revisiones totales: {checks_sin_stock}"
                )
                ultimo_reporte = now
                checks_hoy     = 0
                print(f"[{ts}] 📊 Reporte diario enviado\n", flush=True)

            time.sleep(INTERVALO_MIN * 60)

    except KeyboardInterrupt:
        print("\n⛔ Detenido.", flush=True)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
