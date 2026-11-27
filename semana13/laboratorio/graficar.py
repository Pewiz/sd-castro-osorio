"""
Gráfico de speedup, semana 13 (paso 5).

Lee mediciones/mediciones.csv (lo llena master.py), promedia las corridas
con ok=True por cantidad de workers p y calcula

  T(p)        tiempo promedio con p workers
  S(p)        speedup     = T(1) / T(p)
  E(p)        eficiencia  = S(p) / p
  Karp-Flatt  fracción serial estimada = (1/S - 1/p) / (1 - 1/p)

Imprime la tabla y escribe mediciones/speedup.svg con la recta ideal y la
curva medida. Solo usa la biblioteca estándar.

Uso
  docker compose run --rm graficar
  docker compose run --rm graficar --n 2000000
  docker compose run --rm graficar --csv mediciones/experimento.csv --svg mediciones/experimento.svg
"""
import argparse
import csv
from collections import defaultdict

CSV = "mediciones/mediciones.csv"
SVG = "mediciones/speedup.svg"


def leer(archivo, n, trozos):
    """Devuelve {p: [segundos, ...]} solo con corridas válidas del mismo n y trozos."""
    tiempos = defaultdict(list)
    with open(archivo, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila["ok"] == "True" and int(fila["n"]) == n and int(fila["trozos"]) == trozos:
                tiempos[int(fila["workers"])].append(float(fila["segundos"]))
    return tiempos


def calcular(tiempos):
    """Lista de filas (p, corridas, T, S, E, karp_flatt) ordenada por p."""
    t1 = sum(tiempos[1]) / len(tiempos[1])
    filas = []
    for p in sorted(tiempos):
        t = sum(tiempos[p]) / len(tiempos[p])
        s = t1 / t
        e = s / p
        kf = (1 / s - 1 / p) / (1 - 1 / p) if p > 1 else None
        filas.append((p, len(tiempos[p]), t, s, e, kf))
    return filas


def dibujar(filas, archivo):
    """SVG simple, ideal punteado en gris y medido en rojo."""
    ancho, alto, m = 520, 360, 50
    pmax = max(f[0] for f in filas)
    ymax = max(pmax, max(f[3] for f in filas))

    def x(p):
        return m + (p - 1) / max(pmax - 1, 1) * (ancho - 2 * m)

    def y(v):
        return alto - m - v / ymax * (alto - 2 * m)

    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
              f'font-family="sans-serif" font-size="12">',
              f'<rect width="{ancho}" height="{alto}" fill="white"/>',
              f'<text x="{ancho / 2}" y="22" text-anchor="middle" font-size="15">'
              f'Speedup S(p) = T(1) / T(p)</text>']
    # Ejes y grilla
    for v in range(0, int(ymax) + 1):
        partes.append(f'<line x1="{m}" y1="{y(v):.1f}" x2="{ancho - m}" y2="{y(v):.1f}" stroke="#ddd"/>')
        partes.append(f'<text x="{m - 8}" y="{y(v) + 4:.1f}" text-anchor="end">{v}</text>')
    for p in range(1, pmax + 1):
        partes.append(f'<text x="{x(p):.1f}" y="{alto - m + 18}" text-anchor="middle">{p}</text>')
    partes.append(f'<line x1="{m}" y1="{alto - m}" x2="{ancho - m}" y2="{alto - m}" stroke="black"/>')
    partes.append(f'<line x1="{m}" y1="{m}" x2="{m}" y2="{alto - m}" stroke="black"/>')
    partes.append(f'<text x="{ancho / 2}" y="{alto - 12}" text-anchor="middle">workers p</text>')
    # Ideal, S(p) = p
    partes.append(f'<polyline fill="none" stroke="gray" stroke-width="2" stroke-dasharray="8,6" '
                  f'points="{x(1):.1f},{y(1):.1f} {x(pmax):.1f},{y(pmax):.1f}"/>')
    # Medido
    puntos = " ".join(f"{x(f[0]):.1f},{y(f[3]):.1f}" for f in filas)
    partes.append(f'<polyline fill="none" stroke="#c0282d" stroke-width="3" points="{puntos}"/>')
    for f in filas:
        partes.append(f'<rect x="{x(f[0]) - 5:.1f}" y="{y(f[3]) - 5:.1f}" width="10" height="10" fill="#c0282d"/>')
        partes.append(f'<text x="{x(f[0]):.1f}" y="{y(f[3]) - 10:.1f}" text-anchor="middle">{f[3]:.2f}</text>')
    # Leyenda
    partes.append(f'<line x1="{m + 10}" y1="{m}" x2="{m + 40}" y2="{m}" stroke="gray" stroke-width="2" stroke-dasharray="8,6"/>')
    partes.append(f'<text x="{m + 46}" y="{m + 4}">Ideal</text>')
    partes.append(f'<line x1="{m + 10}" y1="{m + 18}" x2="{m + 40}" y2="{m + 18}" stroke="#c0282d" stroke-width="3"/>')
    partes.append(f'<text x="{m + 46}" y="{m + 22}">Medido</text>')
    partes.append("</svg>")
    with open(archivo, "w", encoding="utf-8") as f:
        f.write("\n".join(partes) + "\n")


def main():
    p = argparse.ArgumentParser(description="Tabla y gráfico de speedup")
    p.add_argument("--n", type=int, default=5000000, help="usar solo corridas con este n")
    p.add_argument("--trozos", type=int, default=40, help="usar solo corridas con estos trozos")
    p.add_argument("--csv", default=CSV, help="archivo de mediciones")
    p.add_argument("--svg", default=SVG, help="dónde escribir el gráfico")
    a = p.parse_args()

    tiempos = leer(a.csv, a.n, a.trozos)
    if 1 not in tiempos:
        raise SystemExit("falta al menos una corrida con 1 worker y ok=True, es la base T(1)")
    filas = calcular(tiempos)

    print(f"{'p':>3}{'corridas':>10}{'T(p) s':>9}{'S(p)':>7}{'E(p)':>7}{'Karp-Flatt':>12}")
    for p_, corridas, t, s, e, kf in filas:
        kf_txt = "-" if kf is None else f"{kf:.3f}"
        print(f"{p_:>3}{corridas:>10}{t:>9.2f}{s:>7.2f}{e:>7.2f}{kf_txt:>12}")
    dibujar(filas, a.svg)
    print(f"\ngráfico escrito en {a.svg}")


if __name__ == "__main__":
    main()
