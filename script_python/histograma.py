#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from matplotlib import rcParams
from scipy.stats import gaussian_kde

# Configuración de la conexión a la base de datos
db_config = {
    'host': 'localhost',
    'database': 'practica01',
    'user': 'postgres',
    'password': 'postgres',
    'port': '5432'
}

# Ruta de guardado
output_dir = r'C:\Users\eurekastein\OneDrive\Documentos\EDIFICIOS\boxplot'
output_filename = os.path.join(output_dir, 'histograma_rangos_velocidad_corregido.png')

# Consulta SQL para obtener los rangos
query = """
    SELECT max_min
    FROM subs.lotes_b_subs
    WHERE max_min IS NOT NULL and max_min <= 5;
"""

try:
    # Establecer conexión
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(query)
    resultados = cursor.fetchall()
    
    if not resultados:
        print("No se encontraron polígonos con datos de rango.")
    else:
        # Procesar datos
        rangos = []
        for (rango,) in resultados:
            try:
                rango = float(rango) if isinstance(rango, str) else rango
                if not np.isnan(rango):
                    rangos.append(rango)
            except Exception as e:
                print(f"Error procesando valor {rango}: {e}")
        
        if not rangos:
            print("No hay datos válidos.")
            exit()

        # Convertir a numpy array
        rangos = np.array(rangos)
        n_poligonos = len(rangos)
        
        # Configuración de estilo
        plt.style.use('ggplot')
        rcParams.update({'figure.autolayout': True})
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # --- HISTOGRAMA PRINCIPAL ---
        # Fijar exactamente 20 bins
        n_bins = 40
        
        # Crear histograma
        n, bins, patches = ax.hist(rangos, bins=n_bins, color='#1f77b4',
                                 edgecolor='white', alpha=0.7, density=False)
        
        # Añadir etiquetas con los valores en el eje x
        bin_centers = 0.5 * (bins[:-1] + bins[1:])  # Calcula los centros de las barras
        bin_width = bins[1] - bins[0]
        
        # Configurar los ticks del eje x en el centro de cada barra
        ax.set_xticks(bin_centers)
        # Formatear las etiquetas para mostrar 2 decimales
        ax.set_xticklabels([f"{x:.2f}" for x in bin_centers], rotation=45, ha='right')
        
        # Añadir curva de densidad
        density = gaussian_kde(rangos)
        x = np.linspace(np.min(rangos), np.max(rangos), 1000)
        ax.plot(x, density(x)*len(rangos)*bin_width, 
              color='darkred', linewidth=2, linestyle='--',
              label='Curva de Densidad')
        
        # Personalización
        ax.set_title(f'Distribución de Rangos de Velocidad (máx - mín)\n({n_poligonos} polígonos)', 
                   fontsize=14, pad=20)
        ax.set_xlabel('Rango de Velocidad (mm/año)', fontsize=12)
        ax.set_ylabel('Número de Polígonos', fontsize=12)
        
        # --- ESTADÍSTICAS DESCRIPTIVAS ---
        q75, q25 = np.percentile(rangos, [75, 25])
        iqr = q75 - q25
        
        stats_text = f"""Estadísticas:
Total polígonos: {n_poligonos}
Media: {np.mean(rangos):.2f} mm/año
Mediana: {np.median(rangos):.2f} mm/año
Mínimo: {np.min(rangos):.2f} mm/año
Máximo: {np.max(rangos):.2f} mm/año
Desviación estándar: {np.std(rangos):.2f} mm/año
Rango intercuartílico (IQR): {iqr:.2f} mm/año"""
        
        # Colocar la leyenda en la parte superior izquierda
        ax.legend(loc='upper left', framealpha=0.8)
        
        # Colocar los estadísticos en la parte superior derecha
        ax.text(0.98, 0.75, stats_text, transform=ax.transAxes,
              ha='right', va='top', fontsize=10,
              bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray'))
        
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Ajustar layout para que las etiquetas no se corten
        plt.tight_layout()
        
        # Guardar el gráfico
        os.makedirs(output_dir, exist_ok=True)
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        print(f"Gráfico guardado como: {output_filename}")
        
        # Mostrar el gráfico
        plt.show()

except psycopg2.Error as e:
    print(f"Error al conectar a PostgreSQL: {e}")
finally:
    if conn is not None:
        conn.close()
        print("Conexión cerrada")