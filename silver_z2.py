"""Silver cube SAT with Z/2 (negation) equivariance + biased diagonal.

Equivariance: c(-v) = sigma(c(v)) where sigma is a fixed involution on
colors, with structure:
 - heavy colors are paired by sigma (so num_heavy must be even)
 - one light color is sigma-fixed (= c((0,0,0)))
 - remaining light colors are paired (so num_light - 1 must be even)

For n=11 (10,10,1,21): num_heavy=10 (5 sigma-pairs), num_light=21 (10
sigma-pairs + 1 fixed) - works.
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


def build(n, heavy_mult, num_heavy, light_mult, num_light, sb=True):
    assert num_heavy % 2 == 0, "need even number of heavy colors for sigma pairing"
    assert (num_light - 1) % 2 == 0, "need odd number of light colors so one is fixed"
    nc = 3 * n - 2
    assert num_heavy + num_light == nc
    assert heavy_mult * num_heavy + light_mult * num_light == n * n
    # color labels:
    # heavy: 0,1,2,...,num_heavy-1, paired as (0,1), (2,3), ..., (num_heavy-2, num_heavy-1)
    # light fixed: num_heavy  (the one fixed color, used at (0,0,0))
    # light paired: num_heavy+1, num_heavy+2, ..., nc-1, paired adjacent

    fixed_color = num_heavy

    def sigma(c):
        if c == fixed_color: return c
        if c < num_heavy:
            return c ^ 1  # pair (2k, 2k+1)
        # c > fixed_color
        base = c - (fixed_color + 1)
        partner = (base ^ 1) + (fixed_color + 1)
        return partner

    vpool = IDPool()

    # We use a "canonical" representative for each negation-orbit.
    orbit_rep = {}
    for v in product(range(n), repeat=3):
        nv = neg(v, n)
        if v not in orbit_rep:
            r = min(v, nv)
            orbit_rep[v] = r
            orbit_rep[nv] = r

    def V(v, c):
        # variable for "rep(v) has color c"  (under equivariance, c(-v)=sigma(c(v)))
        r = orbit_rep[v]
        if r == v:
            return vpool.id(('x', r, c))
        else:
            # c(v) = sigma(c(r))
            return vpool.id(('x', r, sigma(c)))

    diag = back_circulant(n)
    clauses = []

    # Cell uniqueness per ORBIT (vary c over all values; relation enforces opposite)
    reps = set(orbit_rep.values())
    for r in reps:
        lits = [vpool.id(('x', r, c)) for c in range(nc)]
        clauses.append(lits)
        enc = CardEnc.atmost(lits=lits, bound=1, vpool=vpool, encoding=EncType.seqcounter)
        clauses.extend(enc.clauses)

    # Fixed point (0,0,0) must have color = fixed_color
    clauses.append([vpool.id(('x', (0,0,0), fixed_color))])

    # rainbow at each diagonal vertex
    for w in diag:
        N = closed_nbhd(w, n)
        for c in range(nc):
            lits_c = [V(v, c) for v in N]
            clauses.append(lits_c)
            enc = CardEnc.atmost(lits=lits_c, bound=1, vpool=vpool, encoding=EncType.seqcounter)
            clauses.extend(enc.clauses)

    # Diagonal multiplicity constraints
    # For heavy colors 0..num_heavy-1: each has heavy_mult cells on I.
    # Note: I is negation-closed. (0,0,0) is in I, fixed.
    # For a paired heavy color c (not fixed), the cells of c on I correspond to:
    # (orbit, equiv-side). Hard to express directly; use full I cell-by-cell.
    diag_cells = list(diag)
    for c in range(nc):
        lits = [V(w, c) for w in diag_cells]
        target = heavy_mult if c < num_heavy else light_mult
        enc = CardEnc.equals(lits=lits, bound=target, vpool=vpool,
                             encoding=EncType.seqcounter)
        clauses.extend(enc.clauses)

    return clauses, V, vpool, nc


def solve(n, h, kh, l, kl, solver_name="cadical"):
    print(f"  building Z/2 equiv (h={h}x{kh} + l={l}x{kl})", flush=True)
    t = time.time()
    clauses, V, vpool, nc = build(n, h, kh, l, kl)
    nvars = vpool.top
    print(f"  build {time.time()-t:.1f}s, {nvars} vars, {len(clauses)} clauses", flush=True)
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
    h = int(sys.argv[2])
    kh = int(sys.argv[3])
    solver = sys.argv[4] if len(sys.argv) > 4 else "cadical"
    nc = 3 * n - 2
    kl = nc - kh
    # find l such that h*kh + l*kl = n*n
    l_val = (n*n - h * kh) // kl
    assert l_val * kl + h * kh == n * n
    print(f"n={n}, dist h={h}*{kh} + l={l_val}*{kl}, solver={solver}", flush=True)
    sol = solve(n, h, kh, l_val, kl, solver_name=solver)
    if sol:
        ok, _ = verify(n, sol)
        print(f"verified: {ok}")
        if ok:
            outp = f"/Users/kevinventullo/SilverCube/silver_z2_n{n}_h{h}x{kh}_{solver}.txt"
            with open(outp, "w") as f:
                f.write(f"Silver ({n},3)-cube with Z/2 equivariance; dist h{h}x{kh}\n\n")
                for z in range(n):
                    f.write(f"-- z={z} --\n")
                    for x in range(n):
                        f.write(" ".join(f"{sol[(x,y,z)]:>3}" for y in range(n)) + "\n")
                    f.write("\n")
            print(f"saved {outp}")
