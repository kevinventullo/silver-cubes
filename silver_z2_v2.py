"""Silver cube SAT with Z/2 (negation) equivariance + biased diagonal,
extended to allow the sigma-fixed color to have multiplicity m_f > 1.

Color labels:
 - Heavies: 0..num_heavy-1, sigma-paired as (0,1), (2,3), ..., each with
   I-cell count = heavy_mult.
 - sigma-fixed color: num_heavy. I-cell count = fixed_mult (must be odd and
   satisfy Prop 2.1).
 - paired lights: num_heavy+1..3n-3, each with I-cell count = light_mult
   (typically 1).

Z/2 equivariance: c(-v) = sigma(c(v)).
"""

import sys, time
from itertools import product
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical195, Kissat404


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


def neg(v, n):
    return tuple((-x) % n for x in v)


def build(n, heavy_mult, num_heavy, fixed_mult, light_mult, num_light_paired):
    """Build SAT instance under Z/2 equivariance + biased diagonal.
    Distribution: num_heavy colors x heavy_mult + 1 sigma-fixed x fixed_mult
                  + num_light_paired x light_mult."""
    assert num_heavy % 2 == 0, "num_heavy must be even (sigma pairs)"
    assert num_light_paired % 2 == 0, "num_light_paired must be even (sigma pairs)"
    assert fixed_mult % 2 == 1, "fixed_mult must be odd (origin + pairs)"
    nc = 3 * n - 2
    assert num_heavy + 1 + num_light_paired == nc, \
        f"colors {num_heavy} + 1 + {num_light_paired} != {nc}"
    n2 = n * n
    assert heavy_mult * num_heavy + fixed_mult + light_mult * num_light_paired == n2

    fixed_color = num_heavy

    def sigma(c):
        if c == fixed_color: return c
        if c < num_heavy:
            return c ^ 1
        base = c - (fixed_color + 1)
        partner = (base ^ 1) + (fixed_color + 1)
        return partner

    vpool = IDPool()
    orbit_rep = {}
    for v in product(range(n), repeat=3):
        nv = neg(v, n)
        if v not in orbit_rep:
            r = min(v, nv)
            orbit_rep[v] = r
            orbit_rep[nv] = r

    def V(v, c):
        r = orbit_rep[v]
        if r == v:
            return vpool.id(('x', r, c))
        else:
            return vpool.id(('x', r, sigma(c)))

    diag = back_circulant(n)
    clauses = []
    reps = set(orbit_rep.values())
    for r in reps:
        lits = [vpool.id(('x', r, c)) for c in range(nc)]
        clauses.append(lits)
        enc = CardEnc.atmost(lits=lits, bound=1, vpool=vpool, encoding=EncType.seqcounter)
        clauses.extend(enc.clauses)

    # Origin is sigma-fixed
    clauses.append([vpool.id(('x', (0,0,0), fixed_color))])

    # Rainbow per diagonal vertex
    for w in diag:
        N = closed_nbhd(w, n)
        for c in range(nc):
            lits_c = [V(v, c) for v in N]
            clauses.append(lits_c)
            enc = CardEnc.atmost(lits=lits_c, bound=1, vpool=vpool, encoding=EncType.seqcounter)
            clauses.extend(enc.clauses)

    # Diagonal multiplicity per color
    for c in range(nc):
        lits = [V(w, c) for w in diag]
        if c < num_heavy:
            target = heavy_mult
        elif c == fixed_color:
            target = fixed_mult
        else:
            target = light_mult
        enc = CardEnc.equals(lits=lits, bound=target, vpool=vpool,
                             encoding=EncType.seqcounter)
        clauses.extend(enc.clauses)

    return clauses, V, vpool, nc


def solve(n, heavy_mult, num_heavy, fixed_mult, light_mult, num_light_paired,
          solver_name="cadical"):
    print(f"  building Z/2 v2 (h={heavy_mult}x{num_heavy} + "
          f"f={fixed_mult}x1 + l={light_mult}x{num_light_paired})", flush=True)
    t = time.time()
    clauses, V, vpool, nc = build(n, heavy_mult, num_heavy, fixed_mult,
                                  light_mult, num_light_paired)
    nvars = vpool.top
    print(f"  build {time.time()-t:.1f}s, {nvars} vars, {len(clauses)} clauses",
          flush=True)
    cls = {"cadical": Cadical195, "kissat": Kissat404}[solver_name]
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
            if V(v, c) in model:
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
    heavy_mult = int(sys.argv[2])
    num_heavy = int(sys.argv[3])
    fixed_mult = int(sys.argv[4])
    solver = sys.argv[5] if len(sys.argv) > 5 else "cadical"
    light_mult = 1
    nc = 3 * n - 2
    num_light_paired = nc - num_heavy - 1
    assert heavy_mult * num_heavy + fixed_mult + light_mult * num_light_paired == n * n, \
        f"distribution doesn't sum to {n*n}"
    print(f"n={n}, dist h={heavy_mult}x{num_heavy} + f={fixed_mult}x1 + "
          f"l={light_mult}x{num_light_paired}, solver={solver}", flush=True)
    sol = solve(n, heavy_mult, num_heavy, fixed_mult, light_mult, num_light_paired,
                solver_name=solver)
    if sol:
        ok, _ = verify(n, sol)
        print(f"verified: {ok}")
        if ok:
            outp = f"/Users/kevinventullo/SilverCube/silver_z2v2_n{n}_h{heavy_mult}x{num_heavy}_f{fixed_mult}_{solver}.txt"
            with open(outp, "w") as f:
                f.write(f"Silver ({n},3)-cube Z/2 v2; h={heavy_mult}x{num_heavy} + "
                        f"f={fixed_mult}x1 + l=1x{num_light_paired}\n\n")
                for z in range(n):
                    f.write(f"-- z={z} --\n")
                    for x in range(n):
                        f.write(" ".join(f"{sol[(x,y,z)]:>3}" for y in range(n)) + "\n")
                    f.write("\n")
            print(f"saved {outp}")
