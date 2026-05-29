# Silver Cubes: Computational Investigation Findings

## Background

A **silver (n, d)-cube** is a triple `(K_n^d, I, c)` where:
- `K_n^d` is the d-th Cartesian power of the complete graph on n vertices (the "Hamming graph" on `[n]^d`).
- `I` is a *diagonal* of `K_n^d`, i.e., a maximum independent set (cardinality `n^{d-1}`).
- `c : V(K_n^d) -> {0, 1, ..., d(n-1)}` is a vertex coloring such that for every `v ∈ I`, the closed neighborhood `N[v]` contains every color exactly once (rainbow).

This investigation focuses on the **d = 3** case. We use the *back-circulant* diagonal
`I = {(x, y, z) : x + y + z ≡ 0 (mod n)}`.

**References**: 
Ghebleh, Goddyn, Mahmoodian, Verdian-Rizi, *Silver Cubes*,
*Graphs and Combinatorics* 24 (2008), 429–442.

Ventullo, Khodkar *A three dimensional silver cube of order seven*, *Bulletin of the ICA* 56 (2009), 81-84.
 

The Ghebleh, et al. paper conjectures
silver `(n, 3)`-cubes exist for every n ≥ 1 and proves a multiplicativity theorem: if silver (m, 3)- and (n, 3)-cubes exist, then so does a silver (mn, 3)-cube. The conjecture therefore reduces to the prime n case. The paper constructs silver cubes for n ∈ {2, 3, 5}
and cites Ventullo-Khodkar for n = 7. The smallest
open prime in 2008 was **n = 11**, with n ∈ {13, 17, 19, …} also open.


## Result Summary

| n | Status before this work | Status after |
|---|---|---|
| 2,3,5 | known (Ghebleh et al. 2008) | confirmed by SAT |
| 7 | known (Ventullo-Khodkar 2009) | re-verified via SAT in 18 sec |
| **11** | **open** | **silver cube found, verified** |
| 13 | open | **still open** (~80 CPU-hours invested without result) |

The silver (11, 3)-cube file is at
`silver_z2_n11_h16x6_cadical.txt`; verified by the
script `verify_cube.py`.

## Methodology

### 1. Direct SAT encoding (failed for n ≥ 7)

Variables: one Boolean `x[v, c]` per (cell, color) pair.
Constraints: exactly-one-color per cell; for each w ∈ I, all-different
over N[w].

This works for n ≤ 5 (under 2 seconds) but stalls past 10+ minutes for n = 7
without further structure.

### 2. Biased-multiplicity ansatz (key breakthrough)

Each color's multiplicity on I, call it `a_c`, is constrained by
Proposition 2.1 of the paper: `a_c ≡ n^{d-1} (mod d)`, i.e., for d = 3,
`a_c ≡ n^2 (mod 3)`.

Fixing a *specific* multiplicity distribution (e.g., 5 colors used 7 times
each + 14 colors used once each = 49 = 7^2 for n = 7) drastically tightens
the SAT instance. Doing this:
- Reduced n = 7 from "10+ minutes no result" to **18 seconds**.
- Was independently the recollection of K. Ventullo regarding his
  original 2007 search.

### 3. Z/2 negation equivariance (key for n ≥ 11)

The back-circulant diagonal is preserved by negation `(x, y, z) -> (-x, -y, -z)`.
A coloring is **Z/2-equivariant** if `c(-v) = σ(c(v))` for some involution
σ on colors. Origin is σ-fixed.

For n = 11 with the (16 × 6 + 1 × 25) distribution and Z/2 equivariance, the
search took **71 minutes** of CPU; cadical found a satisfying assignment.

The σ used: heavy colors paired (0↔1), (2↔3), (4↔5); light colors paired
(7↔8), (9↔10), ..., (29↔30); the σ-fixed color is 6 (= color of origin).

### 4. Z/2 with σ-fixed multiplicity > 1 (silver_z2_v2.py)

Extension for n with no Z/2-compatible distribution at σ-fixed mult 1.
For each candidate (h_p, m, m_f), one needs:
- h_p × m = (n² - 2·l_p - m_f) / 2 where h_p + l_p = (3n - 3) / 2.
- h_p, l_p ≥ 0.
- m ≡ n² mod 3.
- m_f odd, m_f ≡ n² mod 3.

This was tried at n = 13 with 5 distinct candidate distributions × 2 SAT
solvers (cadical + kissat); none succeeded in ~10 hours wall × ~6 hours
effective CPU each.

## Structural Analysis

We enumerated 50 distinct *diagonal-color patterns* of silver (7, 3)-cubes
under the (7 × 5 + 1 × 14) distribution and tested whether any classical
combinatorial structure recurs.

**All of these tests returned essentially 0 of 50** or 0 of 250 heavy-class
instances:

- Heavy color classes on affine lines in (Z/7)².
- Heavy color classes as partial permutations (transversals).
- Heavy color classes as conic sections (quadrics).
- Light cells forming 2 affine lines (= 14 cells).
- 5 heavy classes as mutual translates of a single tile.
- Multiplicative symmetry: `(x, y) -> (αx, αy)` preserving heavy partition.
- Quasi-invariance under any of:
  - all 48 non-identity translations preserving I
  - all 5 non-identity coordinate permutations
  - negation
  - 6 combined negation × axis-swap involutions (V₄, D₆ family)
- Sidon (distinct-difference) structure on heavy classes.
- Light cells as a D₇-orbit.
- Triple structure (each heavy class' 14 non-I cells produce 14 triples
  partitioning the other 42 I-cells; these triples are not Steiner-system-like
  and have multiple distinct "shapes" per heavy class).

We also checked the n = 11 winning cube for symmetries beyond the Z/2 we
enforced. The only non-trivial cube symmetry it has is negation (= scaling
by α = 10 mod 11 = -1).

**Conclusion**: silver cube solutions appear *structurally amorphous*. No
clean algebraic recipe parameterizes them.

## Lovász Local Lemma Attempt (failed)

We attempted a non-constructive existence proof via LLL.

Random model: pin the diagonal coloring with the chosen multiplicity
distribution. Then color each non-I cell uniformly from
"allowed" colors = {0..3n-3} minus the 3 colors of its I-neighbors.
Bad events: "for w ∈ I and pair (u, v) ⊂ N(w), c(u) = c(v)".

- Probability bound: p ≤ 1/(q - 6) = 1/31 for n = 13.
- Dependency degree: d ≤ 18n - 25 = 209 for n = 13.
- LLL condition: e · p · (d + 1) ≤ 1.
- Computed value: 2.718 × (1/31) × 210 ≈ **18.4**.

The basic argument fails by a factor of ~18. The constants are inherently
bad because each non-I cell participates in O(n) bad events while each
bad event has probability O(1/n). Cluster-expansion or asymmetric LLL is
unlikely to close an 18× gap.

This is consistent with the structural amorphousness: silver cubes appear
to live just at the "phase transition" boundary where probabilistic
arguments do not work easily.

## Open Questions

1. **Does a silver (13, 3)-cube exist?** We invested ~80 CPU-hours across
   10 SAT runs spanning 5 distributions × 2 solvers, with no result. The
   outcome could be: (a) UNSAT for every Z/2-compatible distribution
   tested; or (b) SAT but a specific search is needed that we haven't
   found. We cannot distinguish.

2. **Is there a non-Z/2 distribution at n = 13 that admits a silver cube?**
   For n = 13, the "canonical" distribution (m = n, k_h = n - 2) =
   (13 × 11 + 1 × 26) satisfies Prop 2.1 but is not Z/2-compatible
   (k_h = 11 is odd). A 4.5-hour plain-cadical run found nothing; whether
   this is UNSAT or hard-SAT is unknown.

3. **General theorem**: the Ghebleh et al. conjecture (silver cubes exist for
   all n ≥ 2) remains open for primes n ≥ 13. The probabilistic and algebraic
   tools we tried do not seem to close it.

## Practical Pipeline (what worked)

For a silver (n, 3)-cube at prime n with n² ≡ 1 mod 3 (which includes 11, 13, ...):

1. Pick a multiplicity distribution `(h_mult × k_h + 1 × k_l)` satisfying
   Prop 2.1 (`h_mult ≡ 1 mod 3`).
2. If k_h is even and k_l is odd, the distribution is Z/2-compatible. Use
   the Z/2 encoder.
3. Sweep over candidate `(h_p, m, m_f)` triples that are structurally
   close to the n = 11 winner (h_p = 3, m = 16, m_f = 1):
   - keep h_p small (~3),
   - keep m moderate (~n),
   - increase m_f as needed for divisibility.
4. Use a SAT solver (cadical or kissat) with the seqcounter encoding for
   at-most-one cardinality constraints.
5. Run in parallel across distributions and solvers; first to finish wins.

For n ≤ 11 this pipeline finishes in under 90 CPU-minutes per successful
case. For n = 13 it has not yet succeeded in 80 CPU-hours.

## Files of Note

- `verify_cube.py` — standalone verifier for a coloring file.
- `silver_biased.py` — plain biased-diagonal SAT encoder.
- `silver_z2.py` — Z/2-equivariant encoder, σ-fixed mult = 1.
- `silver_z2_v2.py` — Z/2-equivariant encoder, σ-fixed mult > 1 supported.
- `silver_z2_n11_h16x6_cadical.txt` — the n = 11 silver cube file.
- `silver_biased_n7_h7x5_cadical.txt` — the n = 7 silver cube file
  (matches the structure of the 2009 Ventullo-Khodkar cube).
- `solutions_n7_diagonal.json` — 50 distinct diagonal patterns for n = 7
  used for the structural analysis.
- `analyze_all.py` — runs all structural ansatz tests.
- `n11_symmetries.py` — probes which cube automorphisms the n = 11 cube has.
