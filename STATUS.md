# Status
Updated: 2026-11-17 16:48 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 7.3 h ≈ $27** (estimate, as before plus this wake-up. I can't read
`uptime`). About 33.7 h ≈ $123 left of the $150. Please correct this from the Brev console if it's off.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| – | – | – | – | – | – | – |

No GPU jobs. T26 measured (~2 min of GPU); T26 and T21 are `blocked`.

## Since last update
- T26: wrote `scripts/sysid_repeat.py`. Smoke test (512 envs, 2 calls), then the full run (1,024 envs = 4 candidates
  × 4 blocks of 64, 5 calls). No errors. Results in `results/sysid_repeat.md` / `.json`, Finding 12.
- Averaged refit (`sysid_fit_r4`) **not run**, see below.

## Needs a human
- **T26 result: blow-up counts depend on the rollout call number.** Blow-ups per 64-env block:

  | candidate | call 1 | call 2 | calls 3–5 |
  |---|---|---|---|
  | default | 26–37 | 8–9 | 5 (all 12 blocks) |
  | full fit (T19 best) | 31–36 | 5–7 | 0 (one block 1) |
  | T20 train best | 23–33 | 6 | 4–6 |
  | 0 in T19 and T20 | 29–38 | 1–3 | 0–1 |

  Within a call, blocks differ by about 1 (std 0.7–1.1). Nothing is bit-identical (0/60 block pairs, 0/64 call
  pairs). T19 scored the default alone in call 1 (22, and the penalty level), and T20 scored [default, fit] in
  call 1 (26 vs 28). All grid points ran later. So the "doesn't reproduce" from T20 is a **call-1 artifact, not the
  winner's curse**. Settled (calls ≥ 3), the full fit beats the defaults: 0 vs 5 blow-ups per 64 references, a gap
  much bigger than the noise.
- **Averaged refit not started, two reasons.** (1) `SYSID_REPEATS=4 SYSID_OUT=... scripts/run_isaac.sh ...` is denied
  by my command allowlist (env-var prefix), and I didn't work around it. (2) The refit would still score the default
  in call 1 and take the penalty level from it, so its "default" row and all its losses carry the same artifact.
  Suggestion: add one or two warm-up `rollout()` calls (discarded) at the start of `fit()` and `sysid_check.py`, and
  let the agent pass the env vars some allowed way (e.g. `--repeats`/`--out` flags). Then rerun T19/T20's comparison.
  Why call 1 differs (state left by env construction or the first reset, ADR state, graph capture) isn't known yet.
- Comparison for the T21 gate: single-run fit vs averaged fit is not available (refit not run). Use T26's settled
  numbers above. T20's closed-loop cross-eval numbers (previous STATUS / `results/cross_eval.md` "Fitted robot")
  still stand: they don't depend on the fit's scoring order.
- Still open from before: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close; ADR-max gravity ≈ −7.1 to
  −7.6, not −9.81.
- Sara: set T19 `done` when you're happy; `results/plots/sysid_loss.png`; "What I learned" notes for T17, T23, T18,
  T25, T25b, T22, T20, T26; watch the T22 and Reorient clips.
