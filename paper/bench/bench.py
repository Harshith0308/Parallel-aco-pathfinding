"""
Unified benchmark runner for the ACO parallelization study.

Drives BOTH implementations across configurations and writes a single tidy CSV
plus a platform-info file for reproducibility:

  * Python multiprocessing  (aco_grid.ACOPathfinder, process-based)
  * C / OpenMP              (./aco_bench, thread-based shared memory)

Phases
------
  A  Strong scaling : fixed workload, sweep worker/thread count (-> speedup).
  B  Quality vs density : fixed workers, sweep obstacle density (-> path length).

Each (impl, workers, repeat) is recorded as one row. A warm-up run is discarded
and every config is repeated so the plots can show mean +/- 95% CI.

Usage
-----
  python bench.py            # full run
  python bench.py --quick    # fast smoke run (small sweep, few repeats)
"""

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))   # main project dir
sys.path.insert(0, ROOT)

import multiprocessing as mp                                  # noqa: E402
from aco_grid import Grid, ACOPathfinder                      # noqa: E402

RESULTS = os.path.join(HERE, "..", "results")
# Columns emitted by the C binary (order matters — must match aco_bench.c).
C_COLS = ["impl", "N", "density", "n_ants", "n_iters", "threads",
          "repeat", "total_s", "per_iter_ms", "best_length",
          "valid_last", "reached"]
# Final CSV adds a phase tag ("A" scaling, "B" density).
CSV_COLS = C_COLS + ["phase"]


# ---------------------------------------------------------------------------
# Platform / reproducibility info
# ---------------------------------------------------------------------------

def _cmd(args):
    try:
        return subprocess.check_output(args, stderr=subprocess.STDOUT,
                                       text=True).strip()
    except Exception:
        return "n/a"


def capture_platform():
    info = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "cpu": platform.processor() or "n/a",
        "machine": platform.machine(),
        "logical_cores": mp.cpu_count(),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python": platform.python_version(),
        "numpy": _np_version(),
        "gcc": _cmd(["gcc", "--version"]).splitlines()[0] if _cmd(["gcc", "--version"]) != "n/a" else "n/a",
    }
    return info


def _np_version():
    try:
        import numpy
        return numpy.__version__
    except Exception:
        return "n/a"


# ---------------------------------------------------------------------------
# C / OpenMP runner
# ---------------------------------------------------------------------------

def _bin_path():
    for name in ("aco_bench.exe", "aco_bench"):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("aco_bench not built — run: bash build.sh")


def run_c(N, density, ants, iters, threads, repeats, warmup,
          alpha=1.0, beta=2.5, rho=0.10, seed=42):
    out = subprocess.check_output(
        [_bin_path(),
         "--N", str(N), "--density", str(density), "--ants", str(ants),
         "--iters", str(iters), "--threads", str(threads),
         "--repeats", str(repeats), "--warmup", str(warmup),
         "--alpha", str(alpha), "--beta", str(beta), "--rho", str(rho),
         "--seed", str(seed)],
        text=True)
    rows = []
    for line in out.strip().splitlines():
        f = line.split(",")
        rows.append(dict(zip(C_COLS, f)))
    return rows


# ---------------------------------------------------------------------------
# Python multiprocessing runner
# ---------------------------------------------------------------------------

def run_py(N, density, ants, iters, workers, repeats, warmup,
           parallel=True, alpha=1.0, beta=2.5, rho=0.10, seed=42):
    rows = []
    for rep in range(repeats + warmup):
        grid = Grid(N, obstacle_density=density, seed=seed)
        if not grid.has_path():
            grid = Grid(N, obstacle_density=min(density, 0.15), seed=seed)
        aco = ACOPathfinder(grid, n_ants=ants, n_iterations=iters,
                            alpha=alpha, beta=beta, rho=rho,
                            n_processes=workers)
        t0 = time.perf_counter()
        aco.run(parallel=parallel, verbose=False)
        total = time.perf_counter() - t0
        if rep < warmup:
            continue
        per_iter_ms = (sum(aco.iteration_times) / len(aco.iteration_times)) * 1000.0
        reached = 1 if aco.best_length != float("inf") else 0
        rows.append({
            "impl": "py_mp" if parallel else "py_serial",
            "N": N, "density": density, "n_ants": ants, "n_iters": iters,
            "threads": workers if parallel else 1, "repeat": rep - warmup,
            "total_s": round(total, 6),
            "per_iter_ms": round(per_iter_ms, 4),
            "best_length": round(aco.best_length, 4) if reached else 0.0,
            "valid_last": "",
            "reached": reached,
        })
    return rows


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="fast smoke sweep")
    ap.add_argument("--out", default=RESULTS)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    cores = mp.cpu_count()

    if args.quick:
        N, density, ants, iters = 32, 0.20, 60, 30
        thread_list = [1, 2, 4]
        repeats, warmup = 2, 1
        densities = [0.10, 0.20, 0.30]
        q_iters = 30
    else:
        N, density, ants, iters = 48, 0.20, 200, 100
        thread_list = sorted({1, 2, 4, 8, 12, min(16, cores), cores})
        thread_list = [t for t in thread_list if t <= cores]
        repeats, warmup = 5, 1
        densities = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
        q_iters = 80

    plat = capture_platform()
    with open(os.path.join(args.out, "platform.json"), "w") as f:
        json.dump(plat, f, indent=2)
    print("Platform:", json.dumps(plat, indent=2))

    csv_path = os.path.join(args.out, "raw.csv")
    rows = []

    def tag(new_rows, phase):
        for r in new_rows:
            r["phase"] = phase
        return new_rows

    # ---- Phase A: strong scaling ----
    print(f"\n[Phase A] strong scaling  N={N} density={density} "
          f"ants={ants} iters={iters} repeats={repeats}")
    print("  C/OpenMP serial baseline (1 thread) + thread sweep ...")
    for t in thread_list:
        print(f"    C  threads={t}")
        rows += tag(run_c(N, density, ants, iters, t, repeats, warmup), "A")
    print("  Python multiprocessing process sweep ...")
    for w in thread_list:
        print(f"    PY threads={w}")
        rows += tag(run_py(N, density, ants, iters, w, repeats, warmup, parallel=True), "A")
    print("  Python pure-serial reference ...")
    rows += tag(run_py(N, density, ants, iters, 1, repeats, warmup, parallel=False), "A")

    # ---- Phase B: quality vs density ----
    qt = min(8, cores)
    print(f"\n[Phase B] quality vs density  (threads={qt}, iters={q_iters})")
    for d in densities:
        print(f"    density={d:.2f}")
        rows += tag(run_c(N, d, ants, q_iters, qt, repeats, warmup), "B")
        rows += tag(run_py(N, d, ants, q_iters, qt, repeats, warmup, parallel=True), "B")

    # ---- write CSV ----
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CSV_COLS})

    print(f"\nDone. {len(rows)} rows -> {csv_path}")
    print(f"Platform info  -> {os.path.join(args.out, 'platform.json')}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
