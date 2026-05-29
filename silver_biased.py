"""Silver cube SAT with diagonal-multiplicity bias.

For n=7, user's recollection: 5 colors appear 7 times each on I, 14 colors
appear once. General form: pick partition of n^2 (over c=0..3n-3) where each
multiplicity a_c ≡ n^2 (mod 3) -- Prop 2.1.

For n=7:  5 heavy (mult=7) + 14 light (mult=1)  -> total 49 ✓.
For n=11: 10 heavy (mult=10) + 21 light (mult=1) -> total 121 ✓
          (or 5 heavy mult=19 + 26 light mult=1, etc.)

Without loss of generality we pre-label colors: 0..(k-1) are heavy, rest light.
"""

import sys
import time
from itertools import product

from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Kissat404, Cadical195


def back_circulant(n):
    return [(x, y, (-x - y) % n) for x in range(n) for y in range(n)]


def closed_nbhd(w, n):
    x, y, z = w
    out = [w]
    for k in range(n):
        if k != x: out.append((k, y, z))
        if k != y: out.append((x, k, z))
        if k != z: out.append((x, y, k))
    return out


def valid_distributions(n):
    """Return list of (heavy_mult, num_heavy, light_mult, num_light) satisfying
    Prop 2.1: each mult ≡ n^2 mod 3, sum mult * count = n^2, sum counts = 3n-2."""
    nc = 3 * n - 2
    target = n * n
    parity = target % 3
    valid = []
    # try light_mult = 1 (smallest allowed if 1 ≡ parity)
    if 1 % 3 == parity:
        # heavy_mult: try (parity, parity+3, parity+6, ...) > 1
        # for each heavy_mult, count k satisfies k*(h-1) = n^2 - (3n-2)
        # since k*h + (3n-2 - k) = n^2, so k(h-1) = n^2 - 3n + 2 = (n-1)(n-2)
        rhs = (n - 1) * (n - 2)
        for h in range(parity, n*n + 1, 3):
            if h <= 1: continue
            if rhs % (h - 1) != 0: continue
            k = rhs // (h - 1)
            if 0 < k < nc:
                valid.append((h, k, 1, nc - k))
    return valid


def build(n, heavy_mult, num_heavy, light_mult, num_light, sb="strong"):
    nc = 3 * n - 2
    assert num_heavy + num_light == nc
    assert heavy_mult * num_heavy + light_mult * num_light == n * n

    diagonal = back_circulant(n)
    vpool = IDPool()
    def V(i, j, k, c): return vpool.id(('x', i, j, k, c))

    clauses = []

    # cell uniqueness
    for v in product(range(n), repeat=3):
        lits = [V(*v, c) for c in range(nc)]
        clauses.append(lits)
        enc = CardEnc.atmost(lits=lits, bound=1, vpool=vpool, encoding=EncType.seqcounter)
        clauses.extend(enc.clauses)

    # rainbow per diagonal vertex
    for w in diagonal:
        N = closed_nbhd(w, n)
        for c in range(nc):
            lits_c = [V(*v, c) for v in N]
            clauses.append(lits_c)  # at least one
            enc = CardEnc.atmost(lits=lits_c, bound=1, vpool=vpool, encoding=EncType.seqcounter)
            clauses.extend(enc.clauses)

    # diagonal-multiplicity constraints:
    # colors 0..(num_heavy-1) appear EXACTLY heavy_mult times on I
    # colors num_heavy..(nc-1) appear EXACTLY light_mult times on I
    for c in range(num_heavy):
        lits = [V(*w, c) for w in diagonal]
        enc = CardEnc.equals(lits=lits, bound=heavy_mult, vpool=vpool,
                             encoding=EncType.seqcounter)
        clauses.extend(enc.clauses)
    for c in range(num_heavy, nc):
        lits = [V(*w, c) for w in diagonal]
        enc = CardEnc.equals(lits=lits, bound=light_mult, vpool=vpool,
                             encoding=EncType.seqcounter)
        clauses.extend(enc.clauses)

    # Symmetry break:
    # pin one specific I-vertex to color 0 (a heavy color, breaks color sym)
    if sb in ("strong", "light"):
        w0 = diagonal[0]  # (0,0,0)
        clauses.append([V(*w0, 0)])

    return clauses, V, nc, vpool.top


def solve(n, h_mult, k_heavy, l_mult, k_light, solver_name="kissat", sb="strong"):
    print(f"  building (h={h_mult}*{k_heavy} + l={l_mult}*{k_light})...", flush=True)
    t = time.time()
    clauses, V, nc, nvars = build(n, h_mult, k_heavy, l_mult, k_light, sb=sb)
    print(f"  build {time.time()-t:.1f}s, {nvars} vars, {len(clauses)} clauses", flush=True)
    cls = {"kissat": Kissat404, "cadical": Cadical195}[solver_name]
    s = cls(bootstrap_with=clauses)
    t = time.time()
    res = s.solve()
    dt = time.time() - t
    print(f"  solve {dt:.1f}s -> {'SAT' if res else 'UNSAT'}", flush=True)
    if not res:
        s.delete()
        return None
    model = set(s.get_model())
    coloring = {}
    for v in product(range(n), repeat=3):
        for c in range(nc):
            if V(*v, c) in model:
                coloring[v] = c
                break
    s.delete()
    return coloring


def verify(n, coloring):
    nc = 3 * n - 2
    for w in back_circulant(n):
        cols = [coloring[v] for v in closed_nbhd(w, n)]
        if len(set(cols)) != nc: return False, w
    return True, None


if __name__ == "__main__":
    n = int(sys.argv[1])
    print(f"Valid distributions for n={n} (Prop 2.1):")
    dists = valid_distributions(n)
    for d in dists[:10]:
        print(f"  {d}")
    if len(sys.argv) > 2:
        # arg2: distribution index
        idx = int(sys.argv[2])
        solver = sys.argv[3] if len(sys.argv) > 3 else "kissat"
        if idx >= len(dists):
            print(f"only {len(dists)} dists available")
            sys.exit(1)
        h, kh, l, kl = dists[idx]
        print(f"\nTrying distribution: {h}x{kh} + {l}x{kl}, solver={solver}", flush=True)
        sol = solve(n, h, kh, l, kl, solver_name=solver)
        if sol:
            ok, _ = verify(n, sol)
            print(f"verified: {ok}")
            if ok:
                outp = f"/Users/kevinventullo/SilverCube/silver_biased_n{n}_h{h}x{kh}_{solver}.txt"
                with open(outp, "w") as f:
                    f.write(f"Silver ({n},3)-cube; diagonal distribution: {h}x{kh} + {l}x{kl}\n\n")
                    for z in range(n):
                        f.write(f"-- z={z} --\n")
                        for x in range(n):
                            f.write(" ".join(f"{sol[(x,y,z)]:>3}" for y in range(n)) + "\n")
                        f.write("\n")
                print(f"saved {outp}")
