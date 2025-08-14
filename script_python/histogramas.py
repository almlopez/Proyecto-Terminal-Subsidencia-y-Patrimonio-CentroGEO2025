#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

# Configuración de la conexión a la base de datos
db_config = {
    'host': 'localhost',
    'database': 'practica01',
    'user': 'postgres',
    'password': 'postgres',
    'port': '5432'
}

# Consulta SQL para obtener los polígonos con sus arrays de velocidad
query = """
    SELECT 
        clave, 
        velmm_yr
    FROM 
        subs.lotes_b_subs
    WHERE
        velmm_yr IS NOT NULL AND array_length(velmm_yr, 1) > 0;
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
        # Configurar el estilo de los gráficos
        plt.style.use('ggplot')
        
        # Procesar cada polígono
        for row in resultados:
            poligono_id, vel_array = row
            
            # Convertir el array de PostgreSQL a lista de Python
            try:
                if isinstance(vel_array, str):
                    velocidades = [float(x) for x in vel_array.strip('{}').split(',')]
                else:
                    velocidades = list(vel_array)
                velocidades = np.array(velocidades, dtype=float)
            except Exception as e:
                print("Error procesando velocidades para polígono {}: {}".format(poligono_id, e))
                continue
            
            # Filtrar valores nulos o inválidos
            velocidades = velocidades[~np.isnan(velocidades)]
            
            if len(velocidades) == 0:
                print("Polígono {} no tiene valores de velocidad válidos.".format(poligono_id))
                continue
            
            # Configurar la figura
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Cálculo robusto del número de bins
            try:
                # Regla de Freedman-Diaconis con manejo de casos especiales
                iqr = np.percentile(velocidades, 75) - np.percentile(velocidades, 25)
                if iqr == 0:
                    # Si todos los valores son iguales, usar 1 bin
                    num_bins = 1
                else:
                    bin_width = 2 * iqr / (len(velocidades) ** (1/3))
                    range_val = np.max(velocidades) - np.min(velocidades)
                    num_bins = int(range_val / bin_width) if bin_width > 0 else 10
                    num_bins = max(1, min(num_bins, 20))  # Entre 1 y 20 bins
            except:
                num_bins = 10  # Valor por defecto si falla el cálculo
            
            # Crear el histograma con manejo de errores
            try:
                n, bins, patches = ax.hist(velocidades, bins=num_bins, color='#3498db', 
                                        edgecolor='black', alpha=0.7)
                
                # Configurar título y etiquetas
                ax.set_title('Distribución de velocidades - Polígono: {}'.format(poligono_id))
                ax.set_xlabel('Velocidad (mm/año)')
                ax.set_ylabel('Frecuencia')
                
                # Asegurar que las etiquetas del eje y sean enteros
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))
                
                # Mostrar estadísticas en el gráfico
                stats_text = """
                Total valores: {}
                Media: {:.2f} mm/año
                Mediana: {:.2f} mm/año
                Máx: {:.2f} mm/año
                Mín: {:.2f} mm/año
                Desv. Estándar: {:.2f} mm/año""".format(
                    len(velocidades),
                    np.mean(velocidades),
                    np.median(velocidades),
                    np.max(velocidades),
                    np.min(velocidades),
                    np.std(velocidades)
                )
                
                ax.text(0.95, 0.95, stats_text, transform=ax.transAxes, 
                       verticalalignment='top', horizontalalignment='right',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                
                # Guardar el gráfico
                plt.tight_layout()
                filename = "histograma_velocidades_poligono_{}.png".format(poligono_id)
                plt.savefig(filename, dpi=300)
                print("Gráfico guardado como {}".format(filename))
                plt.close()
                
            except Exception as e:
                print("Error al generar histograma para polígono {}: {}".format(poligono_id, e))
                plt.close()

except psycopg2.Error as e:
    print("Error al conectar a PostgreSQL: {}".format(e))
finally:
    if conn is not None:
        conn.close()
        print("Conexión cerrada")