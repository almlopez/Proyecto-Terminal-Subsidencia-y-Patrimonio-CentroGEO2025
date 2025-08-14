#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from matplotlib.lines import Line2D

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

# Consulta SQL modificada para obtener también los nombres de los edificios
query = """
    SELECT 
        clave, 
        velmm_yr,
        nombres
    FROM 
        subs.lotes_b_subs
    WHERE
        velmm_yr IS NOT NULL AND array_length(velmm_yr, 1) > 0 AND max_min>=4.5 AND no_puntos >= 5;
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
            poligono_id, vel_array, nombres_edificios = row
            
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
                    
                    # Procesar los nombres de edificios
                    if isinstance(nombres_edificios, str):
                        nombres_lista = nombres_edificios.strip('{}').split(',')
                    elif isinstance(nombres_edificios, list):
                        nombres_lista = nombres_edificios
                    else:
                        nombres_lista = []
                    
                    # Eliminar nombres duplicados manteniendo el orden
                    nombres_unicos = []
                    visto = set()
                    for nombre in nombres_lista:
                        nombre = nombre.strip()  # Eliminar espacios en blanco
                        if nombre not in visto:
                            visto.add(nombre)
                            nombres_unicos.append(nombre)
                    
                    # Crear etiqueta compacta con los nombres únicos
                    etiqueta = "\n".join(nombres_unicos[:2])  # Mostramos solo 2 nombres máximo
                    if len(nombres_unicos) > 2:
                        etiqueta += f"\n(+{len(nombres_unicos)-2} más)"
                    
                    poligono_info.append({
                        'id': str(poligono_id),
                        'data': velocidades,
                        'media': media,
                        'nombres': etiqueta
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
        labels_ordenados = [x['nombres'] for x in poligono_info]
        medias_ordenadas = [x['media'] for x in poligono_info]
        
        # Configurar el gráfico con más espacio entre boxplots
        plt.figure(figsize=(20, 8))  # Ancho aumentado para más separación
        plt.style.use('ggplot')
        
        # Posiciones más espaciadas para los boxplots
        positions = np.arange(1, len(data_ordenada)+1) * 2  # Duplicamos el espacio entre boxplots
        
        # Crear boxplot con posiciones personalizadas
        box = plt.boxplot(data_ordenada, patch_artist=True, 
                         labels=labels_ordenados,
                         positions=positions,
                         widths=1.2)  # Ancho de los boxplots
        
        # Personalizar colores
        colors = plt.cm.plasma(np.linspace(0, 1, len(data_ordenada)))
        for patch, color in zip(box['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Configurar título y ejes con texto más pequeño
        plt.title('Distribución de velocidades por grupo de edificios (ordenados por velocidad media)', 
                 fontsize=14, pad=20)
        plt.xlabel('Edificios en el polígono', fontsize=10)
        plt.ylabel('Velocidad (mm/año)', fontsize=10)
        
        # Ajustar las etiquetas del eje x
        plt.xticks(positions, labels=labels_ordenados, rotation=45, ha='right', fontsize=7)  # Texto más pequeño
        
        # Añadir línea de medias
        for i, media in enumerate(medias_ordenadas):
            plt.plot([positions[i]+0.8, positions[i]+1.2], [media, media], 'r--', lw=1, alpha=0.7)
        
        # Añadir leyenda
        legend_elements = [
            Line2D([0], [0], color='r', linestyle='--', lw=1, label='Velocidad media'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor=colors[0], 
                  markersize=10, label='Distribución por grupo de edificios')
        ]
        plt.legend(handles=legend_elements, loc='lower right')
        
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