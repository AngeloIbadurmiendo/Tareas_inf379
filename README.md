# Fuente de Datos: Climate Change - Earth Surface Temperature Data

## Origen de los Datos
Este conjunto de datos fue obtenido a través de la plataforma **Kaggle** y fue estructurado originalmente por **Berkeley Earth**, una organización de investigación independiente enfocada en el análisis de datos climáticos mundiales.
* **Enlace de descarga original:** [Kaggle - Earth Surface Temperature Data](https://www.kaggle.com/datasets/berkeleyearth/climate-change-earth-surface-temperature-data)

## Descripción de los Datos
El dataset de Berkeley Earth consolida cientos de millones de observaciones meteorológicas históricas (con registros desde 1750). Para abarcar el análisis a lo largo de todo el semestre en sus distintas dimensiones, este repositorio utiliza el conjunto completo de archivos, los cuales ofrecen diferentes niveles de granularidad:

* `GlobalTemperatures.csv`: Tendencias macro de las temperaturas globales de la tierra y los océanos.
* `GlobalLandTemperaturesByCountry.csv`: Temperaturas promedio segmentadas a nivel de país.
* `GlobalLandTemperaturesByState.csv`: Promedios detallados por estados/provincias.
* `GlobalLandTemperaturesByMajorCity.csv` y `GlobalLandTemperaturesByCity.csv`: Granularidad a nivel de ciudades específicas.

Todas las mediciones incluyen la temperatura promedio mensual (`AverageTemperature`) en grados Celsius y su respectiva incertidumbre (`AverageTemperatureUncertainty`) con un intervalo de confianza del 95%.