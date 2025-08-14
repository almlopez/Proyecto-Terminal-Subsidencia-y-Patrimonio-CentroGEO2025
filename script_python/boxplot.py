#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

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
output_filename = os.path.join(output_dir, 'boxplots_velocidades_poligonos_ordenados.png')

# Consulta SQL para obtener los polígonos con sus arrays de velocidad
query = """
    SELECT 
        clave, 
        velmm_yr
    FROM 
        subs.lotes_b_subs
    WHERE
        velmm_yr IS NOT NULL AND array_length(velmm_yr, 1) > 0 AND max_min>=6 AND no_puntos >= 5;
"""

try:
    # Establecer conexión con la base de datos
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    # Ejecutar la consulta
    cursor.execute(query)
    resultados = cursor.fetchall()
    
    # Verificar si obtuvimos datos
    if not resultados:
        print("No se encontraron polígonos con datos de velocidad.")
    else:
        # Preparar los datos para los boxplots
        data = []
        poligono_info = []
        
        for row in resultados:
            poligono_id, vel_array = row
            
            try:
                # Convertir el array a lista de Python
                if isinstance(vel_array, str):
                    velocidades = [float(x) for x in vel_array.strip('{}').split(',')]
                else:
                    velocidades = list(vel_array)
                
                # Filtrar valores no válidos
                velocidades = [v for v in velocidades if v is not None and not np.isnan(v)]
                
                if velocidades:
                    media = np.mean(velocidades)
                    poligono_info.append({
                        'id': str(poligono_id),
                        'data': velocidades,
                        'media': media
                    })
            except Exception as e:
                print(f"Error procesando polígono {poligono_id}: {e}")
                continue
        
        if not poligono_info:
            print("No hay datos válidos para generar los boxplots.")
            exit()

        # Ordenar polígonos por velocidad media
        poligono_info.sort(key=lambda x: x['media'])
        
        # Separar datos ordenados
        data_ordenada = [x['data'] for x in poligono_info]
        labels_ordenados = [x['id'] for x in poligono_info]
        medias_ordenadas = [x['media'] for x in poligono_info]
        
        # Configurar el gráfico
        plt.figure(figsize=(16, 8))
        plt.style.use('ggplot')
        
        # Crear boxplot
        box = plt.boxplot(data_ordenada, patch_artist=True, labels=labels_ordenados)
        
        # Personalizar colores (gradiente según la media)
        colors = plt.cm.plasma(np.linspace(0, 1, len(data_ordenada)))
        for patch, color in zip(box['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Configurar título y ejes
        plt.title('Distribución de velocidades por polígono (ordenados por velocidad media)', 
                fontsize=16, pad=20)
        plt.xlabel('ID de Polígono', fontsize=12)
        plt.ylabel('Velocidad (mm/año)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        
        # Añadir línea de medias
        for i, media in enumerate(medias_ordenadas):
            plt.plot([i+0.8, i+1.2], [media, media], 'r--', lw=1, alpha=0.7)
        
        # Añadir leyenda
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='r', linestyle='--', lw=1, label='Velocidad media'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor=colors[0], 
                  markersize=10, label='Distribución por polígono')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        # Añadir grid
        plt.grid(True, linestyle='--', alpha=0.6, axis='y')
        
        # Ajustar márgenes
        plt.tight_layout()
        
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Guardar el gráfico
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