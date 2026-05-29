# silver-cubes

N.b. Everything in this repo was written by Claude Code, with the exception of "kv_cube_test.py", some minor style edits to findings.md, and this disclaimer. 

Computational investigation of silver (n, 3)-cubes — specifically, finding a
silver (11, 3)-cube (which was open in the literature) and exploring whether
the same approach extends to n = 13.

See **[findings.md](findings.md)** for the full writeup: methodology, the
biased-multiplicity ansatz, Z/2 negation equivariance, structural analysis,
and Lovász Local Lemma attempt.

## Quick verification

```bash
python3 verify_cube.py silver_z2_n11_h16x6_cadical.txt
```

Should report: `Valid silver (11, 3)-cube w.r.t. back-circulant diagonal.`

## Dependencies

- Python 3
- `python-sat` (for the SAT-based encoders): `pip install python-sat`

## License

MIT. See [LICENSE](LICENSE).
