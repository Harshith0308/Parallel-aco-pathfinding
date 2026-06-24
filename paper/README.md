# paper/ — empirical parallelization study

Research-paper workspace built on top of the ACO project in the repository root.
It benchmarks the **same algorithm** under two parallel back-ends and produces
the figures and LaTeX for a paper.

```
paper/
├── PLAN.md              # publication roadmap + venue advice + checklist
├── bench/
│   ├── aco_bench.c      # C/OpenMP timed driver (wraps ../../c_src solver)
│   ├── build.sh         # compile the driver
│   ├── bench.py         # runs Python mp + C/OpenMP, writes results/raw.csv
│   └── plots.py         # publication-quality figures from raw.csv
├── results/             # raw.csv, platform.json, figures/  (generated)
└── tex/
    ├── main.tex         # IEEEtran paper scaffold (fill the [[FILL]] markers)
    └── refs.bib         # seed bibliography (expand it yourself)
```

## Quick start

```bash
# 1. build + run benchmarks (needs gcc with OpenMP, numpy, scipy, matplotlib)
cd paper/bench
bash build.sh
python bench.py          # add --quick for a fast smoke run
python plots.py

# 2. figures land in paper/results/figures/ and feed straight into the paper
```

## Requirements beyond the root project

- A C compiler with OpenMP (`gcc -fopenmp`)
- `scipy` (for the Amdahl curve fit) in addition to numpy/matplotlib

See [PLAN.md](PLAN.md) for the full roadmap and what still needs your own work
(especially the literature review).
