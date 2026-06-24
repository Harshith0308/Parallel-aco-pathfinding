# Publication plan

Turning the ACO project into a citable empirical paper.

## Contribution (the one-sentence claim)

> An empirical comparison of process-based (Python `multiprocessing`) and
> thread-based (C/OpenMP) parallelization strategies for Ant Colony Optimization
> on grid path planning — measuring speedup, parallel efficiency, the
> serialization overhead of process-based parallelism, and solution quality vs
> obstacle density, with an Amdahl's-law characterization of the serial limit.

This is framed as a **measurement/empirical study**, not a "we built a tool"
report — that framing is what makes it publishable given how well-studied ACO is.

## Recommended venue path (solo author)

1. **Preprint with a DOI (do this first).** Post to **Zenodo** or **IEEE
   TechRxiv** — free, reputable, citable, no gatekeeper. This is your dependable
   "Publications" line.
2. **Peer review (stretch).** A regional IEEE conference, an undergraduate
   research symposium, or a PDC/HPC workshop. Real peer review.
3. **Highest-leverage move:** get one professor to read it and ideally
   co-author. It roughly doubles acceptance odds and unlocks arXiv endorsement.

> Avoid pay-to-publish predatory journals that email students. Check any venue
> against Beall's list and a trusted faculty member.

## Status checklist

- [x] C/OpenMP benchmark driver with timing + CSV (`bench/aco_bench.c`)
- [x] Unified runner: Python mp + C/OpenMP, platform capture (`bench/bench.py`)
- [x] Publication-quality figures: speedup, efficiency, Amdahl, quality (`bench/plots.py`)
- [x] LaTeX paper scaffold, IEEEtran (`tex/main.tex`, `tex/refs.bib`)
- [x] Run full benchmark (145 rows) and regenerate figures
- [x] Fill all *data-derived* `[[FILL]]` markers (platform, workload, speedups,
      Amdahl serial fraction, serialization overhead, quality trend)
- [x] Author affiliation filled (SRM University-AP, B.Tech CSE Cloud Computing)
- [x] **Literature review** — Related Work written with 16 verified references
      (foundational ACO, ACO path planning, parallel/GPU ACO, performance models),
      all in `tex/refs.bib` with DOIs; matrix filled in `literature/`.
      **You still must read the papers you cite** before submission.
- [x] Unify the infeasible-grid policy: both back-ends now solve the *identical*
      feasibility-checked grid per density (shared `--grid` files); silent
      density-lowering removed. Phase B is now a true per-instance comparison.
- [ ] Optional: larger grids (requires raising `MAX_N` / dynamic allocation in C),
      multiple grid sizes, GPU or multi-node comparison
- [ ] Proofread, write abstract last, get a faculty read
- [ ] Post preprint (Zenodo/TechRxiv) → optionally submit to a venue

## How to reproduce the results

```bash
cd paper/bench
bash build.sh           # compile the C/OpenMP driver
python bench.py         # full sweep -> ../results/raw.csv + platform.json
python plots.py         # -> ../results/figures/*.png
```

Then compile the paper (Overleaf is easiest, or locally):

```bash
cd paper/tex
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

## What still needs *real intellectual work* from you

The harness gives you rigorous data, but a paper is judged on framing and
scholarship. You personally need to:

1. **Read ~15 papers** and write an honest Related Work that positions this study.
2. **Interpret** the results — *why* does Python saturate early? *why* is the
   serial fraction what it is? Connect to Amdahl/Gustafson.
3. **State limitations** truthfully (single machine, N≤50, independent layouts).

Do not let any tool write the Related Work for you from memory — citations must
be ones you have actually read and verified.
