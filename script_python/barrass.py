#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from matplotlib import rcParams

# Configuración de la conexión a la base de datos
db_config = {
    'host': 'localhost',
    'database': 'practica01',
    'user': 'postgres',
    'password': 'postgres',
    'port': '5432'
}

# Ruta de guardado específica
output_dir = r'C:\Users\eurekastein\OneDrive\Documentos\EDIFICIOS\boxplot'
output_filename = os.path.join(output_dir, 'barras_rangos_mejorado.png')

# Consulta SQL para obtener los rangos
query = """
    SELECT 
        clave, 
        max_min
    FROM 
        subs.lotes_b_subs
    WHERE
        max_min IS NOT NULL;
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
        datos = []
        for poligono_id, rango in resultados:
            try:
                rango = float(rango) if isinstance(rango, str) else rango
                if not np.isnan(rango):
                    datos.append({'id': str(poligono_id), 'rango': rango})
            except Exception as e:
                print(f"Error procesando polígono {poligono_id}: {e}")
        
        if not datos:
            print("No hay datos válidos.")
            exit()

        # Convertir a DataFrame y ordenar
        df = pd.DataFrame(datos)
        df = df.sort_values('rango')
        n_barras = len(df)
        
        # Configuración de estilo
        plt.style.use('ggplot')
        rcParams.update({'figure.autolayout': True})
        
        # Configurar el gráfico con espacio adaptativo
        fig, ax = plt.subplots(figsize=(max(10, n_barras*0.3), 8))  # Ancho dinámico
        
        # Ajustar posición de las barras y su ancho
        posiciones = np.arange(n_barras)
        ancho_barra = max(0.2, min(0.8, 30/n_barras))  # Ancho adaptativo
        
        # Crear gráfico de barras con colores
        colors = plt.cm.plasma(np.linspace(0, 1, n_barras))
        bars = ax.bar(posiciones, df['rango'], width=ancho_barra, color=colors, alpha=0.7)
        
        # Títulos y etiquetas
        ax.set_title('Rangos de velocidad (máx - mín) por polígono (ordenados)', 
                    fontsize=14, pad=20)
        ax.set_xlabel('ID de Polígono', fontsize=12)
        ax.set_ylabel('Rango de Velocidad (mm/año)', fontsize=12)
        
        # Ajustar etiquetas del eje X
        fontsize_etiquetas = max(6, min(10, 300/n_barras))
        ax.set_xticks(posiciones)
        ax.set_xticklabels(df['id'], 
                          rotation=45, 
                          ha='right', 
                          fontsize=fontsize_etiquetas)
        
        # Añadir espacio entre etiquetas y eje
        ax.tick_params(axis='x', which='major', pad=10)
        
        # Añadir línea de media general
        media = df['rango'].mean()
        ax.axhline(media, color='red', linestyle='--', 
                  linewidth=1.5, alpha=0.7, 
                  label=f'Media: {media:.2f} mm/año')
        
        # Añadir valores encima de las barras
        fontsize_valores = max(6, min(9, 200/n_barras))
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', 
                   va='bottom' if height >= 0 else 'top',
                   fontsize=fontsize_valores,
                   rotation=90 if n_barras > 50 else 0,
                   bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
        
        # Ajustar límites del eje X
        ax.set_xlim(-0.7, n_barras - 0.3)
        
        # Ajustar margen inferior de forma segura
        margen_inferior = min(0.15 + (n_barras * 0.007), 0.5)
        plt.subplots_adjust(bottom=margen_inferior, top=0.92)
        
        # Leyenda mejorada
        ax.legend(loc='upper right', framealpha=0.9)
        
        # Grid y estilo
        ax.grid(True, linestyle='--', alpha=0.5, axis='y')
        ax.set_axisbelow(True)
        
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