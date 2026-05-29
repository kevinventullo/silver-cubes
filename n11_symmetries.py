"""Test what cube-automorphism symmetries our n=11 winner has beyond Z/2."""
import re
from itertools import product, permutations
from collections import Counter

n = 11

with open('/Users/kevinventullo/SilverCube/silver_z2_n11_h16x6_cadical.txt') as f:
    text = f.read()
coloring = {}
z = -1
for line in text.splitlines():
    m = re.match(r'-- z=(\d+) --', line)
    if m:
        z = int(m.group(1)); x = 0; continue
    if z >= 0 and line.strip() and not line.startswith('Silver'):
        toks = line.split()
        if len(toks) == n:
            for y, t in enumerate(toks):
                coloring[(x, y, z)] = int(t)
            x += 1

assert len(coloring) == n**3
print(f"Loaded n={n} cube with {len(coloring)} cells")


def quasi_invariance(coloring, transform):
    """transform: V -> V. Does there exist permutation pi s.t.
    coloring[transform(v)] = pi(coloring[v]) for all v? Return pi or None."""
    pi = {}
    for v in coloring:
        v2 = transform(v)
        c = coloring[v]
        c2 = coloring[v2]
        if c in pi:
            if pi[c] != c2: return None
        else:
            pi[c] = c2
    return pi


def cycle_structure(pi):
    """Return list of cycle lengths in pi."""
    seen = set()
    cycs = []
    for k in pi:
        if k in seen: continue
        cyc = []
        cur = k
        while cur not in seen:
            seen.add(cur)
            cyc.append(cur)
            cur = pi[cur]
        cycs.append(len(cyc))
    return sorted(cycs, reverse=True)


# Test all the standard symmetries
tests = {}

# Negation
tests["negation"] = lambda v: tuple((-x) % n for x in v)

# Axis permutations (S_3)
for sigma in permutations(range(3)):
    if sigma == (0, 1, 2): continue
    name = f"axis_perm{sigma}"
    tests[name] = (lambda s: lambda v: tuple(v[s[i]] for i in range(3)))(sigma)

# Translations preserving I = back-circulant: (a, b, c) with a+b+c=0
# (only test a small sample for time)
for a, b in [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 3), (3, 5), (4, 7)]:
    c = (-a - b) % n
    name = f"translation{a, b, c}"
    tests[name] = (lambda a, b, c: lambda v: ((v[0] + a) % n, (v[1] + b) % n, (v[2] + c) % n))(a, b, c)

# Combined: negation + each axis perm
for sigma in permutations(range(3)):
    if sigma == (0, 1, 2): continue
    name = f"neg_axis_perm{sigma}"
    tests[name] = (lambda s: lambda v: tuple((-v[s[i]]) % n for i in range(3)))(sigma)

# Multiplicative scaling by alpha
for alpha in range(2, n):
    name = f"scale_alpha={alpha}"
    tests[name] = (lambda a: lambda v: tuple((a * x) % n for x in v))(alpha)

print(f"\n=== Testing {len(tests)} candidate symmetries ===\n")
for name, T in tests.items():
    pi = quasi_invariance(coloring, T)
    if pi is not None:
        # Check if T preserves the back-circulant diagonal (it should, given pi exists)
        sample = (1, 2, (-3) % n)  # in I
        in_I = sum(T(sample)) % n == 0
        cycs = cycle_structure(pi)
        fixed = sum(1 for c in pi if pi[c] == c)
        print(f"  {name}: YES  cycles={cycs}  fixed={fixed}  preserves I: {in_I}")

# What's the group? Compose pairs of found symmetries to find generators.
print("\nDone.")
