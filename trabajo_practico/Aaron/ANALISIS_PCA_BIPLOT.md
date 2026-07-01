# Análisis PCA: Emisiones de GEI, Anomalías Térmicas y Latitud por País (2008-2012)

## 📊 Resumen Ejecutivo

El biplot PCA relaciona **4 variables climáticas y económicas** por país para el período 2008-2012:
- **Temperatura**: Anomalía térmica respecto al baseline histórico (1850-1900)
- **Emisiones**: Totales, per cápita, e intensidad por unidad de PIB
- **Geografía**: Latitud absoluta promedio del país

**Resultado**: 40 países se distribuyen en un espacio bidimensional donde dos componentes principales explican el **60.3%** de la varianza total.

---

## 🎯 Los Dos Ejes del PCA

### **PC1: Eje de Intensidad Antropogénica (38.4% de varianza)**

**¿Qué captura?**
Agrupa países que combinan tres características:
- Anomalía térmica **positiva y elevada** (calentamiento local)
- Emisiones **per cápita altas** (intensidad de vida/producción)
- Latitud **elevada** (distancia del ecuador)

**Interpretación física**: En latitudes altas, el cambio climático se amplifica (amplificación ártica). Los países con gran producción per cápita y anomalías térmicas significativas se desplazan hacia la **derecha** de este eje.

**Países típicos**:
- **China**, **Rusia**, **Canadá**: Extremo derecho (intensidad alta, latitudes altas, anomalía térmica presente)
- **India**, **Brasil**: Centro o izquierda (menor anomalía térmica local, latitudes bajas)

---

### **PC2: Eje de Escala Absoluta vs. Eficiencia Económica (21.9% de varianza)**

**¿Qué captura?**
Separa a los países por la estructura de sus emisiones:
- **Arriba**: Emisiones **totales gigantescas** pero también **ineficiencia por PIB** (mucho carbono por dólar generado)
- **Abajo**: O bien economías eficientes (poco carbono por dólar) o países con menor volumen absoluto

**Interpretación económica**: Un país arriba en PC2 es un **fabricante mundial** que aún requiere mucha energía de combustibles fósiles por unidad de riqueza generada.

**Países típicos**:
- **China**: Extremo superior (emisiones totales masivas + económicamente menos eficiente en carbono)
- **Alemania**, **Japón**: Centro-inferior (producción significativa pero altamente eficiente)

---

## 🗺️ Cuadrantes del Biplot

### **Cuadrante Superior Derecho: "Los Gigantes Ineficientes"**
- **Características**: PC1 positivo (intensidad alta), PC2 positivo (escala masiva)
- **Qué significa**: Países con anomalía térmica elevada, emisiones per cápita altas, latitud importante **y** volumen absoluto gigantesco
- **Ejemplo**: **China** — segundo productor mundial, latitud central-norte, anomalía térmica local significativa

### **Cuadrante Inferior Derecho: "Economías Eficientes a Escala"**
- **Características**: PC1 positivo, PC2 negativo
- **Qué significa**: Países con anomalía térmica positiva y emisiones per cápita altas **pero economías relativamente eficientes** (menos carbono por PIB)
- **Ejemplo**: **Estados Unidos**, **Rusia** — emisiones per cápita elevadas, latitud importante, pero PIB más eficiente que China

### **Cuadrante Superior Izquierda: "Economías Masivas pero Ineficientes"**
- **Características**: PC1 negativo, PC2 positivo
- **Qué significa**: Países con **bajo GHG_Per_Capita** pero **altísimo GHG_Per_GDP** — queman mucho carbono para generar poco PIB
- **Ejemplo**: **India** — emisiones totales significativas, pero distribuidas en 1,400 millones de personas, ineficiencia económica alta

### **Cuadrante Inferior Izquierda: "Países Pequeños o Desarrollados Eficientes"**
- **Características**: PC1 negativo, PC2 negativo
- **Qué significa**: Bajo en todas las dimensiones — países pequeños o con economías verdes/nucleares
- **Ejemplo**: Naciones europeas pequeñas, Nueva Zelanda

---

## 🔍 Interpretación de los Vectores Rojo (Loadings)

Cada flecha roja representa cómo contribuye una variable a los dos ejes principales:

| Variable | PC1 | PC2 | Interpretación |
|----------|-----|-----|---|
| **Latitude_Abs** | 0.87 | -0.09 | Fuerte correlación con PC1: la latitud determina la amplificación térmica |
| **GHG_Per_Capita** | 0.80 | -0.06 | Emissions per capita sigue la latitud y anomalía térmica |
| **Temp_Anomaly_2010** | 0.66 | 0.04 | Anomalía térmica es central en la separación norte-sur |
| **GHG_Total** | 0.34 | 0.61 | Escala absoluta de emisiones determina principalmente PC2 |
| **GHG_Per_GDP** | -0.12 | 0.86 | Eficiencia económica es el factor dominante de PC2 |

**Clave**: Los vectores **cortos en PC1** (GHG_Total, GHG_Per_GDP) indican que estas variables **son menos importantes** para diferenciar intensidad antropogénica. Lo que más importa es la **latitud** y las **emisiones por persona**.

---

## 🌍 Casos de Estudio

### **China (Extremo Superior Derecho)**
- **PC1 = +4.1, PC2 = +4.1**
- Masa de población gigantesca (emisiones totales altísimas)
- Latitud importante (norte de Asia)
- Industria masiva pero aún carbonointensiva
- **Conclusión**: Máximo en escala absoluta y anomalía térmica local

### **Estados Unidos**
- **PC1 ≈ +3.0, PC2 ≈ +0.3 a -0.3**
- Emisiones per cápita **muy altas** (estilo de vida consumista)
- Latitud media-alta (desde Canadá hasta Golfo de México)
- Economía eficiente (mucho PIB por unidad de carbono)
- **Conclusión**: Intensidad alta pero mejor posicionado que China en eficiencia

### **India (Superior Izquierda)**
- **PC1 ≈ +0.6, PC2 ≈ +1.2**
- Emisiones per cápita **muy bajas** (densidad de población, pobreza relativa)
- Latitud baja (trópicos)
- Economía ineficiente en carbono (industria en crecimiento)
- **Conclusión**: Aparentemente "verde" en PC1, pero ineficiente en PC2

### **Alemania & Japón (Centro-Inferior)**
- **PC1 ≈ -0.5 a -1.0, PC2 ≈ -0.6**
- Emisiones per cápita moderadas
- Economía altamente eficiente (PIB verde/nuclear)
- **Conclusión**: Referentes de transición energética

### **Brasil (Centro)**
- **PC1 ≈ 0.0, PC2 ≈ -0.2**
- Cerca del origen — comportamiento "promedio global"
- Latitud ecuatorial (baja amplificación térmica)
- Emisiones totales significativas pero per cápita bajas
- **Conclusión**: Representa el "equilibrio" del dataset

---

## 📈 Varianza Explicada

- **PC1**: 38.4% — Casi **40% de toda la variación** se explica por **latitud, anomalía térmica e intensidad per cápita**
- **PC2**: 21.9% — Otro **22%** por **escala absoluta vs. eficiencia económica**
- **Total (PC1 + PC2)**: 60.3% — Suficiente para capturar la estructura global del problema

---

## ✅ Conclusiones

1. **Amplificación Ártica es real**: Los vectores muestran que latitud y anomalía térmica están profundamente acopladas.

2. **China es el outlier de escala**: Se separa radicalmente en ambos ejes — el país más grande en emisiones absolutas y con anomalía térmica local significativa.

3. **EE.UU. vs. China**: Estados Unidos emite mucho **per cápita**, pero China lidera en **volumen absoluto**.

4. **India es un dilema**: Baja intensidad per cápita, pero enorme ineficiencia económica — un país en transición industrial.

5. **La latitud es predictor fuerte**: Casi de forma automática, los países nórdicos aparecen a la derecha (mayor anomalía, más latitud).

---

## 🔬 Metodología

- **Período**: 2008-2012 (ventana de 5 años para reducir ruido interanual)
- **Temperatura**: Media móvil de 12 meses (MA12) del dataset de ciudades principales
- **Baseline**: Anomalía respecto a la climatología 1850-1900
- **Variables**: 5 (4 de emisiones + 1 de latitud)
- **Normalización**: StandardScaler (todas las variables en escala similar)
- **Técnica**: PCA con 2 componentes principales
- **Muestra**: 40 países con datos completos

---

**Generado**: Análisis PCA transversal 2010 (ventana 2008-2012)  
**Versión**: 1.0 con soporte opcional LULUCF  
**Autor**: Análisis automático de datos climáticos y emisiones de GEI
