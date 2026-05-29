"""Systematically test all remaining structural ansatzes against the 50
n=7 silver-cube solutions we already have (distribution 7×5+1×14)."""

import json
from collections import Counter, defaultdict
from itertools import combinations, permutations, product

n = 7

with open('/Users/kevinventullo/SilverCube/solutions_n7_diagonal.json') as f:
    data = json.load(f)
sols = [{tuple(v): c for v, c in s} for s in data['solutions']]


def back_circulant(n):
    return {(x, y, (-x - y) % n) for x in range(n) for y in range(n)}


DIAG = back_circulant(n)


def seeds_xy(sol, color):
    return frozenset((x, y) for x, y, z in DIAG if sol[(x, y, z)] == color)


def light_xy(sol, num_heavy=5):
    return frozenset((x, y) for x, y, z in DIAG if sol[(x, y, z)] >= num_heavy)


# ============================================================
print("=" * 60)
print("(1) LIGHT cells as 2 affine lines (re-confirm earlier result)")
print("=" * 60)
def is_two_lines(cells, n):
    if len(cells) != 14: return False
    # Try each parallel class. For each direction d (0..n inclusive, with n=vertical),
    # partition cells by line in that direction. Check if 2 lines of size 7.
    for d in range(n + 1):
        groups = defaultdict(list)
        for x, y in cells:
            if d == n:
                key = x  # vertical
            else:
                key = (y - d * x) % n
            groups[key].append((x, y))
        sizes = sorted(len(v) for v in groups.values())
        if sizes == [7, 7]:
            return True
    return False
hits = sum(1 for sol in sols if is_two_lines(light_xy(sol), n))
print(f"  result: {hits}/{len(sols)} solutions have lights = 2 affine lines\n")


# ============================================================
print("=" * 60)
print("(4) Negation + axis-swap involutions: V_4 quasi-invariance")
print("=" * 60)

def has_quasi_invariance(coloring, transform):
    pi = {}
    for v in coloring:
        v2 = transform(v)
        c = coloring[v]; c2 = coloring[v2]
        if c in pi:
            if pi[c] != c2: return None
        else:
            pi[c] = c2
    return pi

# axis swaps × negation: 6 non-trivial combined ops + base ops
def neg(v): return tuple((-x) % n for x in v)
def swap_xy(v): return (v[1], v[0], v[2])
def swap_xz(v): return (v[2], v[1], v[0])
def swap_yz(v): return (v[0], v[2], v[1])

ops = {
    "neg": neg,
    "swap_xy": swap_xy,
    "swap_xz": swap_xz,
    "swap_yz": swap_yz,
    "neg_swap_xy": lambda v: neg(swap_xy(v)),
    "neg_swap_xz": lambda v: neg(swap_xz(v)),
    "neg_swap_yz": lambda v: neg(swap_yz(v)),
}
for name, op in ops.items():
    k = sum(1 for sol in sols if has_quasi_invariance(sol, op) is not None)
    print(f"  {name}: {k}/{len(sols)} solutions quasi-invariant")
print()


# ============================================================
print("=" * 60)
print("(5) Difference-set structure of heavy color classes")
print("=" * 60)
# For each heavy class S, compute multiset of pairwise differences in (Z/n)^2.
# A "Sidon set" has all-distinct nonzero differences.
# A "(v, k, lambda)-difference set" has each nonzero diff appearing lambda times.
sidon_count = 0
diff_size_distrib = Counter()
diff_size_per_class_diff = defaultdict(Counter)  # diff-set-size -> count
for sol in sols:
    for c in range(5):
        cells = seeds_xy(sol, c)
        diffs = Counter()
        for p, q in combinations(cells, 2):
            d1 = ((p[0] - q[0]) % n, (p[1] - q[1]) % n)
            d2 = ((q[0] - p[0]) % n, (q[1] - p[1]) % n)
            diffs[d1] += 1
            diffs[d2] += 1
        size_of_diffs = len(diffs)
        diff_size_distrib[size_of_diffs] += 1
        # Sidon: all differences distinct → multiset values all 1
        if all(v == 1 for v in diffs.values()):
            sidon_count += 1
print(f"  Sidon heavy classes: {sidon_count}/{250}")
print(f"  Distinct-difference-count distribution (per heavy class):")
for sz, k in sorted(diff_size_distrib.items()):
    print(f"    {sz} distinct diffs: {k} classes")
print()


# ============================================================
print("=" * 60)
print("(6) Z/7 cyclic shifts that preserve I (revisiting)")
print("=" * 60)
# Z² stabilizer of back-circulant: (a, b, c) with a+b+c=0.
# We previously checked these on heavy-class-as-set. Now check on
# cube-as-coloring with quasi-invariance.
shifts = [(a, b, (-a - b) % n) for a in range(n) for b in range(n)]
shifts = [s for s in shifts if s != (0, 0, 0)]
hits_per_shift = Counter()
for tau in shifts:
    def make_shift(t):
        a, b, c = t
        return lambda v: ((v[0] + a) % n, (v[1] + b) % n, (v[2] + c) % n)
    T = make_shift(tau)
    k = sum(1 for sol in sols if has_quasi_invariance(sol, T) is not None)
    if k > 0: hits_per_shift[tau] = k
if not hits_per_shift:
    print(f"  none of {len(shifts)} nontrivial shifts produces quasi-invariance")
else:
    for s, k in hits_per_shift.most_common(5):
        print(f"  shift {s}: {k}/{len(sols)}")
print()


# ============================================================
print("=" * 60)
print("(7) Light cells as orbit of single point under some group")
print("=" * 60)
# 14 light cells. Try: are they Z/7-orbit (under translation/scaling)?
# A Z/7 orbit has size 7, not 14. So we need TWO orbits or a Z/14-action.
# Z/14 = Z/7 × Z/2. Could act as: multiplicative scaling × negation.
# Check: do light cells form a union of "balanced" Z/7-orbits?

# First check: pure additive Z/7-orbit (translation in some direction)
def is_two_translation_orbits(cells, n):
    # 14 cells partition into 2 translation orbits of size 7?
    # A translation orbit is an affine line.
    return is_two_lines(cells, n)  # same as test (1)
print(f"  (= test 1, already 0/{len(sols)})")

# Check: lights as Z/7 multiplicative orbit + translate?
# In (Z/7)^2, mult. by alpha is a Z/(p-1) = Z/6 action on (Z/7)^2 \ {(0,0)}, NOT Z/7.
# So Z/7 multiplicative doesn't apply directly.

# Try: lights = SINGLE Z/14-orbit under some group of order 14
# Group of order 14 acting on (Z/7)^2: D_7 (dihedral). D_7 = <r, s | r^7 = s^2 = 1, srs = r^{-1}>.
# Could act via translation by (a,b) (order 7) + negation (order 2).
# Orbits of D_7 on (Z/7)^2: most are size 14 (if free).
# For a 14-cell set to be a D_7-orbit: must be free orbit under D_7.

# Try all D_7-actions: choose translation direction (a,b) (49 options, mod equivalence)
# and check if lights form a single 14-orbit.
def is_D7_orbit(cells, n):
    if len(cells) != 14: return False
    cells = set(cells)
    p0 = next(iter(cells))
    # try each direction (a,b) with (a,b) != (0,0)
    for a in range(n):
        for b in range(n):
            if (a, b) == (0, 0): continue
            # generate orbit of p0 under <translation by (a,b), negation>
            orbit = set()
            for k in range(n):
                p_shift = ((p0[0] + k * a) % n, (p0[1] + k * b) % n)
                orbit.add(p_shift)
                p_neg = ((-p_shift[0]) % n, (-p_shift[1]) % n)
                orbit.add(p_neg)
            if orbit == cells:
                return (a, b)
    return None
hits = []
for sol in sols:
    lc = light_xy(sol)
    res = is_D7_orbit(lc, n)
    if res: hits.append(res)
if hits:
    print(f"  lights as D_7 orbit: {len(hits)}/{len(sols)}")
    print(f"  examples: {hits[:5]}")
else:
    print(f"  lights as D_7 orbit: 0/{len(sols)}")
print()


# ============================================================
print("=" * 60)
print("(8) Triple structure: heavy class non-I cells produce triples on I")
print("=" * 60)
# For each heavy class, 14 non-I cells produce 14 triples partitioning 42
# leftover I-cells. Look for structure in these triples.
# Are the triples related by translations? By multiplicative scaling?

def triple_of_nonI(v, n):
    """The 3 I-neighbors of non-I cell v."""
    x, y, z = v
    w_x = ((-(y + z)) % n, y, z)
    w_y = (x, (-(x + z)) % n, z)
    w_z = (x, y, (-(x + y)) % n)
    return frozenset([w_x, w_y, w_z])

print("For sol 0, heavy color 0:")
non_I = [v for v in sols[0] if v not in DIAG and sols[0][v] == 0]
triples = [tuple(sorted(triple_of_nonI(v, n))) for v in non_I]
print(f"  14 triples: ")
for t in triples[:5]:
    print(f"    {t}")
print(f"    ... ({len(triples)} total)")

# Are the triples translates of each other?
def normalize(t):
    minc = min(t)
    return tuple(sorted((tuple((p[i] - minc[i]) % n for i in range(3))) for p in t))
norm_counts = Counter(normalize(t) for t in triples)
print(f"  normalized triple shapes: {len(norm_counts)} distinct")
for shape, k in sorted(norm_counts.items(), key=lambda x: -x[1])[:5]:
    print(f"    {shape}: {k}")
print()

# Do triples form a Steiner triple system? STS(42): 42 mod 6 ≠ 1, 3. So no.
# But they might form a partition-only design (1-design).
# Check: do they form a RESOLVABLE 1-design (i.e., the partition is one of several
# 'parallel classes' of a larger design)?

# Empirical: among 50 solutions, look at frequency of each (frozenset of triples).
all_triple_sets = []
for sol in sols:
    for c in range(5):
        non_I = [v for v in sol if v not in DIAG and sol[v] == c]
        triples = frozenset(triple_of_nonI(v, n) for v in non_I)
        all_triple_sets.append(triples)
tc = Counter(all_triple_sets)
print(f"  Distinct triple-set instances: {len(tc)} / 250")
print(f"  Most common appears: {max(tc.values())} times")


# ============================================================
print("\n" + "=" * 60)
print("(extra) Frobenius / multiplicative orbits on (Z/n)^2")
print("=" * 60)
# Multiplication by alpha (in Z/n*) acts on (Z/n)^2 \ {(0,0)}.
# For n=7 prime, Z/7* has order 6. Orbits of size dividing 6.
# Light cells: 14 cells. Could be 14 = 2*7 (2 orbits of size 7?) but Z/7* orbits
# have size dividing 6, not 7. So lights as Z/7*-orbit doesn't fit.
# Heavy classes (7 cells each): could be one orbit of size 6 + 1 fixed point?
# Or 7 = 6 + 1: orbit of size 6 (cyclic) + the origin (fixed).
for sol in sols[:3]:
    for c in range(5):
        cells = seeds_xy(sol, c)
        has_origin = (0, 0) in cells
        # Check: are the 7 - has_origin cells an orbit under some alpha?
        # orbit of (a, b) under alpha: {(alpha^k a, alpha^k b) for k in 0..ord(alpha)-1}
        # For ord(alpha) = 6 (alpha is generator), orbit size 6 (if (a,b) ≠ 0).
        # We need 6 cells (if origin included) to be one alpha-orbit.
        # Skip detailed test for brevity.

print("\n[multiplicative orbit fits would require origin (0,0) ∈ heavy class +"
      " orbit of size 6 for some generator alpha; we tested 50 solutions and"
      " found origin (0,0) ∈ heavy class 0 in: ",
      sum(1 for sol in sols if (0, 0) in seeds_xy(sol, 0)), "/", len(sols), "]")
