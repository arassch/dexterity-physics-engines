# Status
Updated: 2026-11-17 15:47 UTC by the server agent (wake-up: state changed, PLAN.md T19 set running by Sara)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| – | – | – | – | – | – | – |

No GPU jobs (`nvidia-smi` 0 MiB). Sara's T19 fit (`scripts/sysid_fit.py`, 1,024 envs, Newton) **finished** at
15:44 UTC (~5 min) with no Traceback; it wrote `results/sysid_robot.json` (committed now as a backup).

T19 fit result (from `~/runs/sysid_fit.log` / the json; 216 coarse + 125 fine candidates, penalty level 0.465):

| | armature | damping_scale | effort_scale | loss | blowups | RMS a | RMS b | RMS c (rad) |
|---|---|---|---|---|---|---|---|---|
| default | 0.010 | 1.00 | 1.00 | 0.316 | 22 | 0.091 | 0.074 | 0.335 |
| fitted  | 0.0131 | 1.149 | 1.591 | 0.208 | 0 | 0.019 | 0.049 | 0.324 |

T19 stays `running` until Sara sets it `done`; T20 waits for that. T21 is a gate.

## Since last update
- Sara's fit finished; I committed `results/sysid_robot.json`. Nothing started or stopped.

## Needs a human
- Sara: T19 fit is done. Still to do on your side: `results/plots/sysid_loss.png` and the step-response plots
  (not written by the script), Finding 11, then set T19 `done` so T20 can start.
- Worth a look before T20: the fit removes all blow-ups (22 → 0) but barely changes signal-c RMS (0.335 → 0.324 rad).
  The coarse best hit the `effort_scale` upper bound (2.0); the fine grid moved to 1.59. Also, the default row here
  (RMS a 0.091, c 0.335, 22 blow-ups) differs from the harness `--check` (a 0.027, c 0.100, 16/64): different metric
  or env count? Worth checking which is comparable.
- Surprising (still open): T22 A (no smoothness penalties) never succeeded in 3,000 iterations, while B (no grasp
  rewards, 90.2%) beat the full-reward baseline at the same iteration (7.9%). See Finding 6.
- The 4-vs-8 substep call is close: 19 vs 16 blow-ups, one seed, 64 envs, and 4 substeps is ~18% faster.
- Sara: watch the 3 T22 clips and add your description to `results/reward_experiment.md` / Finding 6.
- At ADR max, `variable_gravity` gives g_z ≈ −7.1 to −7.6, not −9.81. FYI.
- Sara: "What I learned" notes for T17, T23, T18, T25, T25b, T19, T22.
- Still open from before: watching the 10 Reorient clips.
