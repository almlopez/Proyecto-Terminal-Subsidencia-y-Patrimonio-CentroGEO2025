#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expand_google_links.py
───────────────────────────────────────────────────────────────
Sustituye en un Excel las URLs tipo
  https://www.google.com/maps/search/?api=1&query=…
por la URL final “/place/…@lat,lon…” que Google devuelve tras la
redirección, de modo que luego puedas extraer fácilmente latitud
y longitud.

Requisitos
──────────
pip install pandas openpyxl selenium webdriver-manager tqdm

Uso
───
python expand_google_links.py
"""

import re
import time
import pandas as pd
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import unquote

# ── CONFIGURACIÓN ─────────────────────────────────────────────

FILE_IN  = "base_ina_datos_links_final.xlsx"     # archivo de entrada
FILE_OUT = "base_ina_datos_links_expanded.xlsx"  # archivo de salida

URL_COL      = "google_maps_url"  # nombre de la columna con las URLs
TIMEOUT      = 20                # segundos máximos por página
DELAY_BETWEEN = 1.0              # s de pausa entre peticiones (evita bloqueo)
MAX_TRIES    = 2                 # reintentos en caso de fallo

# ── CARGA EL DATAFRAME ───────────────────────────────────────
df = pd.read_excel(FILE_IN)

# Expresión para detectar si la URL YA tiene @lat,lon
PAT_COORDS = re.compile(r'@-?\d+\.\d+,-?\d+\.\d+')

# ── CONFIGURA CHROME HEADLESS ────────────────────────────────
chrome_opts = Options()
chrome_opts.add_argument("--headless=new")   # si quieres ver la ventana, quita esta línea
chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--window-size=1200,800")
chrome_opts.add_argument("--lang=es-ES")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_opts
)
wait = WebDriverWait(driver, TIMEOUT)

# ── PROCESA FILA A FILA ──────────────────────────────────────
for idx, url in tqdm(df[URL_COL].items(), total=len(df), desc="Expandiendo enlaces"):
    url = str(url).strip()

    # 1. Si ya contiene coordenadas, no hacemos nada
    if PAT_COORDS.search(url):
        continue

    # 2. Intentamos abrir y capturar la URL final con @lat,lon
    success = False
    for attempt in range(1, MAX_TRIES + 1):
        try:
            driver.get(url)

            # Espera a que la URL cambie y contenga el patrón @lat,lon
            wait.until(lambda d: PAT_COORDS.search(d.current_url))

            # Guardamos la URL completa (decodificada para legibilidad)
            final_url = unquote(driver.current_url)
            df.at[idx, URL_COL] = final_url
            success = True
            break  # sale del bucle de reintentos

        except Exception as e:
            if attempt == MAX_TRIES:
                print(f"⚠️  Fila {idx}: no se pudo expandir ({e})")
            else:
                time.sleep(3)  # espera antes de reintentar

    time.sleep(DELAY_BETWEEN)  # pequeña pausa para no saturar a Google

driver.quit()

# ── GUARDA EL RESULTADO ─────────────────────────────────────
df.to_excel(FILE_OUT, index=False)
print(f"\n✅  Proceso terminado. Archivo guardado como: {FILE_OUT}")
