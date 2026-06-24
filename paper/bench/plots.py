"""
Generate publication-quality figures from results/raw.csv.

Figures (saved to results/figures/ at 300 dpi):
  fig_runtime.png          per-iteration time vs worker count (log y), both impls
  fig_speedup.png          speedup vs worker count + ideal line + Amdahl fit (C)
  fig_efficiency.png       parallel efficiency vs worker count
  fig_quality_density.png  best path length vs obstacle density, both impls

Speedup is computed per implementation relative to its own 1-worker mean, so the
process-based and thread-based curves are each measured against their own serial
baseline. Error bars are 95% confidence intervals over the repeats.

Usage:  python plots.py
"""

import csv
import math
import os
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")
FIGDIR = os.path.join(RESULTS, "figures")

LABEL = {"c_openmp": "C / OpenMP (threads)",
         "py_mp": "Python multiprocessing (processes)",
         "py_serial": "Python serial"}
COLOR = {"c_openmp": "#1f77b4", "py_mp": "#d62728", "py_serial": "#7f7f7f"}
MARKER = {"c_openmp": "o", "py_mp": "s", "py_serial": "^"}

plt.rcParams.update({
    "font.family": "serif", "font.size": 11,
    "axes.grid": True, "grid.alpha": 0.3,
    "figure.dpi": 120, "savefig.dpi": 300, "savefig.bbox": "tight",
})


def load():
    with open(os.path.join(RESULTS, "raw.csv")) as f:
        return list(csv.DictReader(f))


def ci95(vals):
    a = np.asarray(vals, float)
    if len(a) < 2:
        return 0.0
    return 1.96 * a.std(ddof=1) / math.sqrt(len(a))


def agg(rows, impl, phase, xkey, ykey):
    """Return sorted (x, mean_y, ci_y) for one implementation/phase."""
    buckets = defaultdict(list)
    for r in rows:
        if r["impl"] != impl or r["phase"] != phase:
            continue
        buckets[float(r[xkey])].append(float(r[ykey]))
    xs = sorted(buckets)
    return (np.array(xs),
            np.array([np.mean(buckets[x]) for x in xs]),
            np.array([ci95(buckets[x]) for x in xs]))


def amdahl(p, s):
    return 1.0 / (s + (1.0 - s) / p)


# ---------------------------------------------------------------------------

def fig_runtime(rows):
    plt.figure(figsize=(6, 4))
    for impl in ("c_openmp", "py_mp"):
        x, y, e = agg(rows, impl, "A", "threads", "per_iter_ms")
        if len(x):
            plt.errorbar(x, y, yerr=e, marker=MARKER[impl], color=COLOR[impl],
                         label=LABEL[impl], capsize=3, lw=1.8)
    plt.yscale("log")
    plt.xlabel("Worker count (threads / processes)")
    plt.ylabel("Per-iteration time (ms, log scale)")
    plt.title("Per-iteration runtime vs parallel workers")
    plt.legend()
    _save("fig_runtime.png")


def fig_speedup(rows):
    plt.figure(figsize=(6, 4))
    maxp = 1
    for impl in ("c_openmp", "py_mp"):
        x, y, _ = agg(rows, impl, "A", "threads", "per_iter_ms")
        if not len(x):
            continue
        base = y[0]                      # mean time at 1 worker
        sp = base / y
        maxp = max(maxp, x.max())
        plt.plot(x, sp, marker=MARKER[impl], color=COLOR[impl],
                 label=LABEL[impl], lw=1.8)
        if impl == "c_openmp" and len(x) >= 3:
            try:
                (s,), _ = curve_fit(amdahl, x, sp, bounds=(0, 1))
                xx = np.linspace(1, x.max(), 100)
                plt.plot(xx, amdahl(xx, s), "--", color=COLOR[impl], alpha=0.6,
                         label=f"Amdahl fit (serial={s*100:.1f}%)")
            except Exception:
                pass
    ideal = np.arange(1, maxp + 1)
    plt.plot(ideal, ideal, ":", color="black", alpha=0.5, label="Ideal (linear)")
    plt.xlabel("Worker count (threads / processes)")
    plt.ylabel("Speedup  S(p) = T(1) / T(p)")
    plt.title("Strong-scaling speedup")
    plt.legend()
    _save("fig_speedup.png")


def fig_efficiency(rows):
    plt.figure(figsize=(6, 4))
    for impl in ("c_openmp", "py_mp"):
        x, y, _ = agg(rows, impl, "A", "threads", "per_iter_ms")
        if not len(x):
            continue
        eff = (y[0] / y) / x
        plt.plot(x, eff, marker=MARKER[impl], color=COLOR[impl],
                 label=LABEL[impl], lw=1.8)
    plt.axhline(1.0, ls=":", color="black", alpha=0.5, label="Ideal (100%)")
    plt.ylim(0, 1.15)
    plt.xlabel("Worker count (threads / processes)")
    plt.ylabel("Parallel efficiency  S(p) / p")
    plt.title("Parallel efficiency")
    plt.legend()
    _save("fig_efficiency.png")


def fig_quality(rows):
    plt.figure(figsize=(6, 4))
    for impl in ("c_openmp", "py_mp"):
        x, y, e = agg(rows, impl, "B", "density", "best_length")
        if len(x):
            plt.errorbar(x, y, yerr=e, marker=MARKER[impl], color=COLOR[impl],
                         label=LABEL[impl], capsize=3, lw=1.8)
    plt.xlabel("Obstacle density")
    plt.ylabel("Best path length (Euclidean)")
    plt.title("Solution quality vs obstacle density")
    plt.legend()
    _save("fig_quality_density.png")


def _save(name):
    os.makedirs(FIGDIR, exist_ok=True)
    path = os.path.join(FIGDIR, name)
    plt.savefig(path)
    plt.close()
    print("  saved", os.path.relpath(path, RESULTS))


def main():
    rows = load()
    print(f"Loaded {len(rows)} rows. Generating figures ...")
    fig_runtime(rows)
    fig_speedup(rows)
    fig_efficiency(rows)
    fig_quality(rows)
    print(f"Figures -> {FIGDIR}")


if __name__ == "__main__":
    main()
