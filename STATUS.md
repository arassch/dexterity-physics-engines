# Status
Updated: 2026-11-17 15:41 UTC by the server agent (wake-up: state changed, new GPU processes 536/555)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T19 fit (Sara, by hand) | Newton | – (starting) | – | – | – | Sara's 2 h GPU cap |

No training runs. The new processes are Sara's `scripts/sysid_fit.py` (1,024 envs, Newton, started 15:39:07 UTC,
log `~/runs/sysid_fit.log`). At 15:41 it had printed `[SYSID] ADR init_difficulty=10, num_substeps=8, clamp=True`
and was still loading; `nvidia-smi` showed no GPU memory yet. T19 stays `blocked` (Sara sets it `done`), so T20
can't start, and T21 is a gate.

## Since last update
- Nothing changed except Sara starting the T19 fit. I didn't start, stop or change anything.

## Needs a human
- Sara: when the fit finishes, set T19 `done` in PLAN.md so T20 (fitted-robot cross-eval) can start.
- Surprising (still open): T22 A (no smoothness penalties) never succeeded in 3,000 iterations, while B (no grasp
  rewards, 90.2%) beat the full-reward baseline at the same iteration (7.9%). See Finding 6.
- The 4-vs-8 substep call is close: 19 vs 16 blow-ups, one seed, 64 envs, and 4 substeps is ~18% faster.
- Sara: watch the 3 T22 clips and add your description to `results/reward_experiment.md` / Finding 6.
- At ADR max, `variable_gravity` gives g_z ≈ −7.1 to −7.6, not −9.81. FYI.
- Sara: "What I learned" notes for T17, T23, T18, T25, T25b, T19, T22.
- Still open from before: watching the 10 Reorient clips.
