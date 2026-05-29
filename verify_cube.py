"""Standalone verifier for a silver (n,3)-cube text file.

Usage:  python3 verify_cube.py <file>

Reads a coloring file in the format produced by this project (z-slice
headers like '-- z=K --', followed by n rows of n numbers each), verifies:
  1. It is a valid silver (n,3)-cube w.r.t. the back-circulant diagonal
     I = {(x,y,z) : x+y+z ≡ 0 mod n}: for each w ∈ I, the closed
     neighborhood N[w] has all 3n-2 colors distinct.
  2. The cube has exactly 3n-2 distinct colors total.
  3. Prints multiplicities of colors on the diagonal (Prop 2.1 check:
     each multiplicity ≡ n^2 mod 3).
"""

import sys
import re
from collections import Counter


def parse(path):
    coloring = {}
    z = -1
    n = None
    with open(path) as f:
        for line in f:
            m = re.match(r'\s*--\s*z=(\d+)\s*--', line)
            if m:
                z = int(m.group(1))
                x = 0
                continue
            if z >= 0:
                toks = line.split()
                # must be all ints
                try:
                    row = [int(t) for t in toks]
                except ValueError:
                    continue
                if not row:
                    continue
                if n is None:
                    n = len(row)
                if len(row) != n:
                    continue
                for y, c in enumerate(row):
                    coloring[(x, y, z)] = c
                x += 1
    return n, coloring


def closed_nbhd(w, n):
    x, y, z = w
    out = [w]
    for k in range(n):
        if k != x: out.append((k, y, z))
        if k != y: out.append((x, k, z))
        if k != z: out.append((x, y, k))
    return out


def back_circulant(n):
    return [(x, y, (-x - y) % n) for x in range(n) for y in range(n)]


def verify(path):
    n, coloring = parse(path)
    print(f"Read coloring for n={n} ({len(coloring)} cells; expected {n**3})")
    assert len(coloring) == n ** 3, f"missing cells: {n**3 - len(coloring)}"
    nc = 3 * n - 2
    expected_colors = set(range(nc))
    used = set(coloring.values())
    print(f"Used {len(used)} distinct colors (expected {nc})")
    assert used == expected_colors, f"unexpected colors: {used.symmetric_difference(expected_colors)}"

    diag = back_circulant(n)
    print(f"Checking {len(diag)} rainbow constraints (|N[w]| = {3*n-2})...")
    failures = []
    for w in diag:
        cols = [coloring[v] for v in closed_nbhd(w, n)]
        if len(set(cols)) != nc:
            failures.append(w)
    print(f"  rainbow violations: {len(failures)}")
    assert not failures, f"first violation at w={failures[0]}"

    print("\n✓ Valid silver ({},3)-cube w.r.t. back-circulant diagonal.".format(n))

    diag_counts = Counter(coloring[w] for w in diag)
    mults = sorted(diag_counts.values(), reverse=True)
    print(f"\nDiagonal color multiplicities (sorted): {mults}")
    print(f"  total: {sum(mults)} = {n}^2 = {n*n}")
    mod3_target = (n * n) % 3
    bad = [c for c, k in diag_counts.items() if k % 3 != mod3_target]
    print(f"  Prop 2.1 ({n}^2 mod 3 = {mod3_target}): "
          f"{'OK' if not bad else f'VIOLATIONS at colors {bad}'}")
    print(f"  distinct multiplicities: {sorted(set(mults))}")


if __name__ == "__main__":
    verify(sys.argv[1])
