#!/usr/bin/env bash
# Compile the C/OpenMP benchmark driver against the existing c_src/ solver.
# Usage:  bash build.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/../../c_src"

gcc -O2 -fopenmp -Wall -Wno-unused-const-variable \
    -I"$SRC" \
    "$HERE/aco_bench.c" "$SRC/aco.c" "$SRC/grid.c" \
    -lm -o "$HERE/aco_bench"

echo "Built: $HERE/aco_bench"
