# -*- coding: utf-8 -*-
"""
Created on Sun May 25 22:23:20 2025

@author: zazas
"""

"""
geocode_via_google_redirect.py
—————————————————————————————————
Lee la columna 'google_maps_url', sigue la redirección de Google
y extrae latitud / longitud que aparecen después de '@'.

⚠️  Respeta el servicio:
    • Máx. ~1 petición por segundo (Google puede bloquear IPs).
    • Usa un User-Agent "humano".
"""

import re
import time
import pandas as pd
import requests
from urllib.parse import urlparse, parse_qs, unquote_plus
from tqdm import tqdm

# 1. CONFIGURA TU ARCHIVO
FILE_IN  = "base_ina_datos_links_expanded.xlsx"   # ← tu archivo
FILE_OUT = "base_ina_datos_coord.xlsx"         # salida Excel
CSV_OUT  = "base_ina_datos_coord.csv"          # salida CSV

# 2. CARGA EL DATAFRAME
df = pd.read_excel(FILE_IN)

# 3. Prepara columnas vacías
df["latitud"]  = None
df["longitud"] = None

# 4. Cabecera para que parezca un navegador
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

# 5. Función auxiliar
COORD_RE = re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)")

def get_coords(url: str, session: requests.Session) -> tuple[float | None, float | None]:
    """ Sigue redirecciones y devuelve (lat, lon) o (None, None). """
    try:
        # 'allow_redirects=True' para que requests siga hasta la URL final
        resp = session.get(url, headers=HEADERS, allow_redirects=True, timeout=15)
        final_url = resp.url
        match = COORD_RE.search(final_url)
        if match:
            lat, lon = map(float, match.groups())
            return lat, lon
    except Exception as e:
        print(f"  ⚠️  Error con {url[:60]}… → {e}")
    return None, None


# 6. PROCESA FILA A FILA (1 req/s aprox.)
with requests.Session() as session:
    for idx, url in tqdm(df["google_maps_url"].items(), total=len(df)):
        lat, lon = get_coords(url, session)
        df.at[idx, "latitud"]  = lat
        df.at[idx, "longitud"] = lon
        time.sleep(1)        # <<— respeta el límite; ajusta si hace falta


# 7. GUARDA RESULTADOS
df.to_excel(FILE_OUT, index=False)
df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")

print("\n✅  Listo:")
print(f"   • {FILE_OUT}")
print(f"   • {CSV_OUT}")
print("   Importa el CSV en QGIS ‘Añadir capa de texto delimitado’ X=longitud Y=latitud (EPSG:4326).")
