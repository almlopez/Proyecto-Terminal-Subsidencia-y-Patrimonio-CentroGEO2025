# -*- coding: utf-8 -*-
"""
Created on Sun May 25 22:42:27 2025

@author: zazas
"""

# geocode_google_v2.py
# ----------------------------------------------------------
# pip install pandas openpyxl requests tqdm geopy beautifulsoup4
# ----------------------------------------------------------

import re, time, json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from urllib.parse import urlparse, parse_qs, unquote_plus
from tqdm import tqdm

FILE_IN  = "base_ina_datos_coord.xlsx"          # tu archivo actual
FILE_OUT = "base_ina_datos_coord_full.xlsx"      # salida XLSX
CSV_OUT  = "base_ina_datos_coord_full.csv"       # salida CSV

# ------------------------------------------------------------------
# 1. Carga el dataframe
# ------------------------------------------------------------------
df = pd.read_excel(FILE_IN)

# 2. Prepara columnas vacías (por si no existían)
for col in ("latitud", "longitud"):
    if col not in df.columns:
        df[col] = None

# 3. Sesión HTTP (cabecera de navegador)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

SESSION = requests.Session()

# 4. Geocoder de respaldo (Nominatim)
geolocator = Nominatim(user_agent="inah_centrog_historico")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# 5. Expresiones regulares
RE_AT      = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)")
RE_CENTER  = re.compile(r'"center":\s*{\s*"lat":\s*(-?\d+\.\d+),\s*"lng":\s*(-?\d+\.\d+)')
RE_APPINIT = re.compile(r'APP_INITIALIZATION_STATE.*?\[(\[-?\d+\.\d+,-?\d+\.\d+)')

def extract_from_html(html: str):
    """Intenta extraer lat/lon del HTML devuelto por Google Maps search."""
    # Método 1: bloque "center":{"lat":x,"lng":y}
    m = RE_CENTER.search(html)
    if m:
        return float(m.group(1)), float(m.group(2))

    # Método 2: APP_INITIALIZATION_STATE=… [[lat,lng],
    m = RE_APPINIT.search(html)
    if m:
        lat, lon = map(float, m.group(1).split(','))
        return lat, lon
    return None, None

def query_from_url(url: str) -> str:
    """Devuelve el texto de búsqueda original de la URL /search/"""
    qs = parse_qs(urlparse(url).query)
    return unquote_plus(qs.get("query", [""])[0])

# 6. Bucle principal
for idx, row in tqdm(df.iterrows(), total=len(df)):
    if pd.notna(row["latitud"]) and pd.notna(row["longitud"]):
        continue  # ya tiene coordenadas

    url = str(row["google_maps_url"]).strip()
    if not url:
        continue

    lat = lon = None

    try:
        resp = SESSION.get(url, headers=HEADERS, allow_redirects=True, timeout=15)
        final_url = resp.url

        # 6.1 Caso 1: redirección con @lat,lon
        m = RE_AT.search(final_url)
        if m:
            lat, lon = map(float, m.groups())
        else:
            # 6.2 Caso 2: buscar en el HTML
            lat, lon = extract_from_html(resp.text)

        # 6.3 Caso 3: geocodificar con Nominatim (solo si no obtuvimos nada)
        if lat is None or lon is None:
            query = query_from_url(url)
            if query:
                loc = geocode(query + ", CDMX, México")
                if loc:
                    lat, lon = loc.latitude, loc.longitude

    except Exception as e:
        print(f"⚠️  [{idx}] Error con URL → {e}")

    df.at[idx, "latitud"]  = lat
    df.at[idx, "longitud"] = lon

    time.sleep(1)        # respeta 1 req/s hacia Google

# 7. Guarda resultados
df.to_excel(FILE_OUT, index=False)
df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
print("\n✅  Archivo completo generado:")
print("   •", FILE_OUT)
print("   •", CSV_OUT)
print("   Importa el CSV en QGIS → Añadir capa de texto delimitado (X=longitud, Y=latitud, EPSG:4326).")
