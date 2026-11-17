#!/usr/bin/env python3
"""Planta de biodiésel simulada: el modelo que genera todos los datos del curso.

Uso:  python generadores/planta.py → escribe datos/*.csv y datos/planta_resumen.json

Los datos son simulados para enseñar y así se dice en la Sección 0. Las cifras de referencia salen de la
literatura: especificación EN 14214, contenido de ésteres ≥ 96.5 % (m/m);
transesterificación con KOH cerca de 60 °C, relación metanol:aceite 6:1 y 0.5–1 % de catalizador.

Qué hay escondido en los datos (lo que el alumno debe descubrir):
  · Fase I (20 días × 5 lotes): el día 7, el lote 3 tuvo un error de dosificación de catalizador (un valor
    bajo que dispara la carta R); los días 13 y 14 entró aceite del proveedor B, más ácido (la media cae y
    dispara la carta X̄).
  · Fase II (15 días × 5 lotes): desde el día 5, el sensor de temperatura del reactor marca de más y el
    reactor trabaja más frío; el contenido de ésteres baja 0.2 puntos (lo detecta, el día 33, la regla de 9 puntos
    seguidos de un mismo lado).
"""
import json, os
import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "..", "datos")   # en el repositorio, generadores/ y datos/ son hermanas
LEI = 96.5                      # límite inferior de especificación, EN 14214 (% m/m)
MEDIA = 97.30                   # media del proceso actual
SIGMA_LOTE = 0.30               # variación entre lotes del mismo día
SIGMA_DIA = 0.06                # variación natural de un día a otro
LOTES_POR_DIA = 5
HORAS = ["07:00", "09:30", "12:00", "14:30", "17:00"]


def fase1(semilla=7):
    rng = np.random.default_rng(semilla)
    filas = []
    for dia in range(1, 21):
        proveedor = "B" if dia in (13, 14) else "A"
        efecto_dia = rng.normal(0, SIGMA_DIA) + (-0.85 if proveedor == "B" else 0.0)
        for k in range(LOTES_POR_DIA):
            x = MEDIA + efecto_dia + rng.normal(0, SIGMA_LOTE)
            if dia == 7 and k == 2:
                x -= 1.30                      # error de dosificación de catalizador
            filas.append({"dia": dia, "lote": (dia - 1) * LOTES_POR_DIA + k + 1, "hora": HORAS[k],
                          "proveedor": proveedor, "esteres": round(x, 2)})
    return pd.DataFrame(filas)


def fase2(semilla=18):
    rng = np.random.default_rng(semilla)
    filas = []
    for dia in range(1, 16):
        efecto_dia = rng.normal(0, SIGMA_DIA) + (-0.20 if dia >= 5 else 0.0)
        for k in range(LOTES_POR_DIA):
            x = MEDIA + efecto_dia + rng.normal(0, SIGMA_LOTE)
            filas.append({"dia": 20 + dia, "lote": 100 + (dia - 1) * LOTES_POR_DIA + k + 1, "hora": HORAS[k],
                          "proveedor": "A", "esteres": round(x, 2)})
    return pd.DataFrame(filas)


def llenado(semilla=5):
    """Envasado en bidones de 20 L: 25 horas × 4 bidones. Especificación del cliente 19.85–20.15 L (dos lados).
    La llenadora está centrada de más (20.05 L): Cp aceptable, Cpk bajo."""
    rng = np.random.default_rng(semilla)
    filas = []
    for hora in range(1, 26):
        ef = rng.normal(0, 0.008)
        for k in range(4):
            filas.append({"hora": hora, "bidon": (hora - 1) * 4 + k + 1, "volumen": round(20.05 + ef + rng.normal(0, 0.035), 3)})
    return pd.DataFrame(filas)


def envasado(semilla=3):
    """Carta p: bidones rechazados por turno (fuga, etiqueta, tapa), con tamaños de muestra distintos.
    El turno 22 tuvo un lote de tapas defectuoso."""
    rng = np.random.default_rng(semilla)
    filas = []
    for turno in range(1, 31):
        n = int(rng.integers(180, 261))
        p = 0.10 if turno == 22 else 0.04
        filas.append({"turno": turno, "inspeccionados": n, "rechazados": int(rng.binomial(n, p))})
    return pd.DataFrame(filas)


def defectos(semilla=9):
    """Carta u: defectos de etiquetado por bidón inspeccionado; el número de bidones cambia cada día.
    El día 17 se cambió el rollo de etiquetas por uno de otro proveedor."""
    rng = np.random.default_rng(semilla)
    filas = []
    for dia in range(1, 26):
        n = int(rng.integers(30, 61))
        tasa = 0.45 if dia == 17 else 0.15
        filas.append({"dia": dia, "bidones": n, "defectos": int(rng.poisson(tasa * n))})
    return pd.DataFrame(filas)


def quejas(semilla=21):
    """Carta c (práctica): quejas de clientes por día hábil, sin causa especial."""
    rng = np.random.default_rng(semilla)
    return pd.DataFrame({"dia": range(1, 31), "quejas": rng.poisson(4.0, 30)})


# ---------------------------------------------------------------------------------------------
#  Reactor por lotes: modelo didáctico del rendimiento (%) para las Secciones 6 a 9.
#  Óptimo cerca de 59 °C, 0.95 % de KOH y relación metanol:aceite 6.2:1 (dentro de lo que reporta
#  la literatura, ver HECHOS_VERIFICADOS.md). A temperatura baja, el catalizador ayuda más (interacción
#  negativa T × C). En los rangos del curso, la relación molar, el tiempo y la agitación casi no importan.
# ---------------------------------------------------------------------------------------------
RUIDO_REND = 0.40


def rendimiento_medio(T, C, R=6.0, t=60.0, rpm=500.0):
    y = (97.0 - 0.06 * (T - 59.0) ** 2 - 8.0 * (C - 0.95) ** 2 - 0.25 * (R - 6.2) ** 2
         - 0.3 * (T - 59.0) * (C - 0.95) - 0.015 * max(0.0, 60.0 - t) + 0.0005 * (rpm - 500.0))
    return y


def costo(T, C):
    """Costo didáctico de catalizador y calentamiento, MXN por tonelada de aceite."""
    return 300.0 * C + 1.5 * (T - 50.0)


def corrida(rng, **f):
    return round(rendimiento_medio(**f) + rng.normal(0, RUIDO_REND), 2)


def experimento_1factor(semilla=31):
    rng = np.random.default_rng(semilla)
    filas = [{"catalizador": c, "replica": k + 1} for c in (0.5, 0.75, 1.0) for k in range(4)]
    orden = rng.permutation(len(filas))
    out = []
    for i, j in enumerate(orden):
        f = filas[j]
        out.append({"orden": i + 1, "catalizador": f["catalizador"], "rendimiento": corrida(rng, T=55.0, C=f["catalizador"])})
    return pd.DataFrame(out)


def bloques(semilla=32):
    rng = np.random.default_rng(semilla)
    efecto_lote = {"L1": -1.5, "L2": 0.0, "L3": 0.8, "L4": -0.6}      # acidez distinta de cada lote de aceite
    out = []
    for lote, ef in efecto_lote.items():
        for c in rng.permutation([0.5, 0.75, 1.0]):
            out.append({"lote_aceite": lote, "catalizador": float(c),
                        "rendimiento": round(rendimiento_medio(55.0, float(c)) + ef + rng.normal(0, RUIDO_REND), 2)})
    return pd.DataFrame(out)


def factorial_2k(semilla=33):
    """2³ con 2 réplicas: temperatura (50, 60 °C), catalizador (0.5, 1.0 %), relación molar (5:1, 7:1)."""
    rng = np.random.default_rng(semilla)
    base = [(T, C, R) for R in (5.0, 7.0) for C in (0.5, 1.0) for T in (50.0, 60.0)]   # orden estándar
    filas = [{"corrida_std": i % 8 + 1, "replica": i // 8 + 1, "temperatura": T, "catalizador": C, "relacion": R}
             for i, (T, C, R) in enumerate(base + base)]
    out = []
    for i, j in enumerate(rng.permutation(len(filas))):
        f = dict(filas[j])
        f["orden"] = i + 1
        f["rendimiento"] = corrida(rng, T=f["temperatura"], C=f["catalizador"], R=f["relacion"])
        out.append(f)
    return pd.DataFrame(out)[["orden", "corrida_std", "replica", "temperatura", "catalizador", "relacion", "rendimiento"]]


def cribado(semilla=34):
    """2^(5−1) con E = ABCD y 4 puntos centrales. A temperatura, B relación, C catalizador, D tiempo, E agitación."""
    rng = np.random.default_rng(semilla)
    niveles = {"temperatura": (50.0, 60.0), "relacion": (5.0, 7.0), "catalizador": (0.5, 1.0),
               "tiempo": (30.0, 90.0), "agitacion": (300.0, 700.0)}
    filas = []
    for k in range(16):
        a, b, c, d = [(-1) ** (1 + ((k >> s) & 1)) for s in range(4)]      # orden estándar, A cambia más rápido
        cod = {"temperatura": a, "relacion": b, "catalizador": c, "tiempo": d, "agitacion": a * b * c * d}
        filas.append({n: niveles[n][0] if cod[n] < 0 else niveles[n][1] for n in niveles} | {"corrida_std": k + 1})
    for k in range(4):
        filas.append({n: sum(niveles[n]) / 2 for n in niveles} | {"corrida_std": 17 + k})
    out = []
    for i, j in enumerate(rng.permutation(len(filas))):
        f = dict(filas[j])
        f["orden"] = i + 1
        f["rendimiento"] = corrida(rng, T=f["temperatura"], C=f["catalizador"], R=f["relacion"], t=f["tiempo"], rpm=f["agitacion"])
        out.append(f)
    cols = ["orden", "corrida_std", "temperatura", "relacion", "catalizador", "tiempo", "agitacion", "rendimiento"]
    return pd.DataFrame(out)[cols]


def ccd(semilla=35):
    """Central compuesto rotable en temperatura y catalizador; centro 58 °C y 0.85 %, pasos 4 °C y 0.2 %,
    alfa = 1.414, 5 centros. Relación 6:1, 60 min, 500 rpm. Respuestas: rendimiento y costo."""
    rng = np.random.default_rng(semilla)
    a = 2 ** 0.5
    cod = [(-1, -1), (1, -1), (-1, 1), (1, 1), (-a, 0), (a, 0), (0, -a), (0, a)] + [(0, 0)] * 5
    filas = []
    for k, (x1, x2) in enumerate(cod):
        T, C = 58.0 + 4.0 * x1, 0.85 + 0.2 * x2
        filas.append({"corrida_std": k + 1, "x1": round(x1, 3), "x2": round(x2, 3), "temperatura": round(T, 2), "catalizador": round(C, 3)})
    out = []
    for i, j in enumerate(rng.permutation(len(filas))):
        f = dict(filas[j])
        f["orden"] = i + 1
        f["rendimiento"] = corrida(rng, T=f["temperatura"], C=f["catalizador"])
        f["costo"] = round(costo(f["temperatura"], f["catalizador"]), 1)
        out.append(f)
    return pd.DataFrame(out)[["orden", "corrida_std", "x1", "x2", "temperatura", "catalizador", "rendimiento", "costo"]]


def gauge(semilla=36):
    """Gauge R&R del contenido de ésteres por cromatografía: 10 lotes × 3 analistas × 2 réplicas."""
    rng = np.random.default_rng(semilla)
    lotes_v = MEDIA + rng.normal(0, 0.30, 10)
    sesgo = {"Ana": 0.0, "Beto": 0.05, "Carla": -0.03}
    out = []
    for i, v in enumerate(lotes_v):
        for an, s in sesgo.items():
            for r in range(2):
                out.append({"lote": f"L{i + 1:02d}", "analista": an, "replica": r + 1, "esteres": round(v + s + rng.normal(0, 0.05), 3)})
    return pd.DataFrame(out)


def confirmacion(semilla=37, T=58.7, C=0.88):
    """Sección 11: cinco corridas de confirmación en el óptimo de la superficie de respuesta."""
    rng = np.random.default_rng(semilla)
    return pd.DataFrame({"corrida": range(1, 6), "temperatura": T, "catalizador": C,
                         "rendimiento": [corrida(rng, T=T, C=C) for _ in range(5)]})


def fase3(semilla=38):
    """Sección 11: 20 días × 5 lotes operando en el óptimo. La reacción se completa mejor: el contenido de
    ésteres sube a ~97.95 % y la variación entre lotes baja a ~0.24."""
    rng = np.random.default_rng(semilla)
    filas = []
    for dia in range(1, 21):
        ef = rng.normal(0, 0.05)
        for k in range(LOTES_POR_DIA):
            filas.append({"dia": 40 + dia, "lote": 300 + (dia - 1) * LOTES_POR_DIA + k + 1, "hora": HORAS[k],
                          "proveedor": "A", "esteres": round(97.95 + ef + rng.normal(0, 0.24), 2)})
    return pd.DataFrame(filas)


def proyecto_llenado(semilla=39):
    """Proyecto final: línea 2 de llenado de bidones de 20 L (especificación 19.85–20.15 L).
    25 horas × 4 bidones; en la hora 12 se tapó una boquilla (causa especial). La línea no es capaz."""
    rng = np.random.default_rng(semilla)
    filas = []
    for hora in range(1, 26):
        ef = rng.normal(0, 0.01) + (-0.11 if hora == 12 else 0.0)
        for k in range(4):
            filas.append({"hora": hora, "bidon": (hora - 1) * 4 + k + 1, "volumen": round(20.0 + ef + rng.normal(0, 0.06), 3)})
    return pd.DataFrame(filas)


def proyecto_experimento(semilla=40):
    """Proyecto final: 2² con 3 réplicas para reducir la variación del llenado. Respuesta: desviación estándar
    (mL) de 20 bidones por corrida. Velocidad lenta y boquilla nueva reducen la variación; sin interacción."""
    rng = np.random.default_rng(semilla)
    filas = []
    for rep in range(3):
        for vel in ("lenta", "rapida"):
            for boq in ("estandar", "nueva"):
                sd = 60.0 - (15.0 if vel == "lenta" else 0.0) - (18.0 if boq == "nueva" else 0.0)
                vol = rng.normal(20.0, sd / 1000.0, 20)
                filas.append({"velocidad": vel, "boquilla": boq, "replica": rep + 1, "de_ml": round(float(np.std(vol, ddof=1) * 1000), 1)})
    orden = rng.permutation(len(filas))
    out = [dict(filas[j], orden=i + 1) for i, j in enumerate(orden)]
    return pd.DataFrame(out)[["orden", "velocidad", "boquilla", "replica", "de_ml"]]


def resumen(f1, f2):
    limpios = f1[~f1.dia.isin([7, 13, 14])]
    return {"LEI": LEI, "media_simulada": MEDIA, "sigma_lote": SIGMA_LOTE, "sigma_dia": SIGMA_DIA,
            "fase1": {"n": len(f1), "media": round(f1.esteres.mean(), 3), "de": round(f1.esteres.std(), 3),
                      "min": float(f1.esteres.min()), "max": float(f1.esteres.max()),
                      "bajo_LEI": int((f1.esteres < LEI).sum())},
            "fase1_sin_7_13_14": {"n": len(limpios), "media": round(limpios.esteres.mean(), 3),
                                  "de": round(limpios.esteres.std(), 3)},
            "fase2": {"n": len(f2), "media": round(f2.esteres.mean(), 3)}}


if __name__ == "__main__":
    os.makedirs(DATOS, exist_ok=True)
    f1, f2 = fase1(), fase2()
    f1.to_csv(os.path.join(DATOS, "lotes_fase1.csv"), index=False)
    f2.to_csv(os.path.join(DATOS, "lotes_fase2.csv"), index=False)
    llenado().to_csv(os.path.join(DATOS, "llenado.csv"), index=False)
    envasado().to_csv(os.path.join(DATOS, "envasado.csv"), index=False)
    defectos().to_csv(os.path.join(DATOS, "defectos.csv"), index=False)
    quejas().to_csv(os.path.join(DATOS, "quejas.csv"), index=False)
    experimento_1factor().to_csv(os.path.join(DATOS, "experimento_1factor.csv"), index=False)
    bloques().to_csv(os.path.join(DATOS, "bloques.csv"), index=False)
    factorial_2k().to_csv(os.path.join(DATOS, "factorial_2k.csv"), index=False)
    cribado().to_csv(os.path.join(DATOS, "cribado_2_5-1.csv"), index=False)
    ccd().to_csv(os.path.join(DATOS, "ccd.csv"), index=False)
    gauge().to_csv(os.path.join(DATOS, "gauge_rr.csv"), index=False)
    confirmacion().to_csv(os.path.join(DATOS, "confirmacion.csv"), index=False)
    fase3().to_csv(os.path.join(DATOS, "lotes_fase3.csv"), index=False)
    proyecto_llenado().to_csv(os.path.join(DATOS, "llenado_proyecto.csv"), index=False)
    proyecto_experimento().to_csv(os.path.join(DATOS, "experimento_proyecto.csv"), index=False)
    r = resumen(f1, f2)
    json.dump(r, open(os.path.join(DATOS, "planta_resumen.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))
