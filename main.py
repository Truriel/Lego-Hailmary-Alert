import time
import random
import urllib.parse
import requests
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── CONFIGURACIÓN — leer de variables de entorno ──
TELEFONO      = os.environ.get("TELEFONO", "5215582371050")
CALLMEBOT_KEY = os.environ.get("CALLMEBOT_KEY", "4035483")
LEGO_URL      = os.environ.get("LEGO_URL", "https://www.lego.com/es-mx/product/project-hail-mary-11389")
INTERVALO_MIN = int(os.environ.get("INTERVALO_MIN", "30"))

# ── NAVEGADOR — usa Chromium del sistema en Docker ──
def crear_driver():
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
    return driver

# ── VERIFICAR STOCK ────────────────────────────────
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
                    print(f"  ✅ Botón activo: '{txt}'")
                    return True
                else:
                    print(f"  ⚠️  Botón deshabilitado: '{txt}'")
                    return False

        print("  ❌ Botón no encontrado")
        return False

    except Exception as e:
        print(f"  [ERROR] {e}")
    return False

# ── WHATSAPP ───────────────────────────────────────
def enviar_whatsapp(mensaje):
    texto = urllib.parse.quote(mensaje)
    url   = (
        f"https://api.callmebot.com/whatsapp.php"
        f"?phone={TELEFONO}&text={texto}&apikey={CALLMEBOT_KEY}"
    )
    try:
        r = requests.get(url, timeout=10)
        print(f"  [WhatsApp] status {r.status_code}")
    except Exception as e:
        print(f"  [WhatsApp ERROR] {e}")

# ── LOOP PRINCIPAL ─────────────────────────────────
def main():
    print("🔍 Iniciando scraper LEGO — Project Hail Mary")
    print(f"⏱  Revisando cada {INTERVALO_MIN} minutos\n")

    driver           = crear_driver()
    alerta_enviada   = False
    sin_stock_desde  = datetime.now()
    checks_sin_stock = 0

    try:
        while True:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] Revisando stock...")

            disponible = esta_disponible(driver)

            if disponible:
                dias  = (datetime.now() - sin_stock_desde).days
                horas = (datetime.now() - sin_stock_desde).seconds // 3600
                print(f"[{ts}] Stock: ✅ SÍ — mandando WhatsApp!\n")
                if not alerta_enviada:
                    enviar_whatsapp(
                        f"🧱 LEGO Project Hail Mary disponible!\n"
                        f"⏳ Estuvo sin stock {dias}d {horas}h\n"
                        f"🔗 {LEGO_URL}"
                    )
                    alerta_enviada   = True
                    checks_sin_stock = 0
            else:
                checks_sin_stock += 1
                dias  = (datetime.now() - sin_stock_desde).days
                horas = (datetime.now() - sin_stock_desde).seconds // 3600
                print(f"[{ts}] Stock: ❌ NO  |  Sin stock: {dias}d {horas}h  |  Revisiones: {checks_sin_stock}\n")
                alerta_enviada = False

            time.sleep(INTERVALO_MIN * 60)

    except KeyboardInterrupt:
        dias  = (datetime.now() - sin_stock_desde).days
        horas = (datetime.now() - sin_stock_desde).seconds // 3600
        print(f"\n⛔ Detenido. Sin stock: {dias}d {horas}h | Revisiones: {checks_sin_stock}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
