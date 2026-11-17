# Diseño de experimentos y control estadístico con Python

Datos y cuaderno del curso **Diseño de experimentos y control estadístico con Python** de **DanLara Learning**.

Cada celda del cuaderno lleva el mismo número que en el video. Por ejemplo, la **Celda 2.8** es la que se ve en la Sección 2.

## Contenido

```
notebooks/
  curso_doe.ipynb          · el cuaderno del curso, de la Sección 0 a la 11
datos/
  lotes_fase1.csv          · 20 días × 5 lotes: contenido de ésteres (Secciones 0 a 5)
  lotes_fase2.csv          · 15 días más, con límites fijos (Sección 3)
  lotes_fase1_depurada.csv · la fase I sin los días 7, 13 y 14 (normalidad en Jamovi, Sección 5)
  lotes_fase3.csv          · 20 días operando en el óptimo (Sección 11)
  envasado.csv             · bidones rechazados por turno (carta p, Sección 4)
  defectos.csv             · defectos de etiquetado por bidón (carta u, Sección 4)
  quejas.csv               · quejas de clientes por día (carta c, práctica de la Sección 4)
  llenado.csv              · volumen de bidones de 20 L (capacidad, Sección 5)
  experimento_1factor.csv  · catalizador en tres niveles (Sección 6)
  bloques.csv              · el mismo experimento con cuatro lotes de aceite (Sección 6)
  factorial_2k.csv         · factorial 2³ con dos réplicas (Sección 7)
  cribado_2_5-1.csv        · fraccionado 2^(5−1) con cuatro puntos centrales (Sección 8)
  ccd.csv                  · diseño central compuesto (Sección 9)
  gauge_rr.csv             · estudio Gauge R&R: 10 lotes × 3 analistas × 2 réplicas (Sección 10)
  confirmacion.csv         · corridas de confirmación en el óptimo (Sección 11)
  llenado_proyecto.csv     · proyecto final: línea 2 de llenado
  experimento_proyecto.csv · proyecto final: experimento 2² de la línea 2
```

## Cómo abrir el cuaderno

Ábrelo en Google Colab, sin instalar nada:

https://colab.research.google.com/github/lara-montano/doe-control-estadistico/blob/main/notebooks/curso_doe.ipynb

La primera celda instala las dos librerías que Colab no trae, `pyDOE3` y `statsmodels`, con versiones fijas. Las demás celdas leen los datos de este repositorio por su URL.

## Para usar tus propios datos

En el panel izquierdo de Colab (ícono de carpeta), sube tu archivo `.csv`. Después, en la celda que lee los datos, cambia `URL + "lotes_fase1.csv"` por el nombre de tu archivo.

## Sobre los datos

Los datos son **simulados para enseñar**. Tienen la forma de una planta de biodiésel real: lotes con su contenido de ésteres, que según la norma EN 14214 debe ser de al menos 96.5 % (m/m), y un reactor cuyo rendimiento depende de la temperatura y del catalizador. No describen ninguna planta en particular.

El modelo que los genera está en `generadores/planta.py`, así que cualquiera puede reproducirlos.

## Versiones con las que se comprobó el cuaderno

Python 3.13 con pandas 3.1.1, numpy 2.5.5, scipy 1.18.1, statsmodels 0.15.0, pyDOE3 1.6.2 y matplotlib 3.11.2.
