# Status
Updated: 2026-11-17 16:03 UTC by the server agent (wake-up: state changed, PLAN.md T20 rewritten and `todo`)

Instance hours since 15 Nov 16:00 UTC: **≈ 7 h ≈ $26** (estimate. I can't read `uptime`, and no start/stop record
exists. From agent tick logs: ~0.3 h on 15 Nov, ~6 h on 16 Nov 12:30–18:30, ~0.5 h today). About 34 h ≈ $124 left
of the $150. Please correct this from the Brev console if it's off.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| – | – | – | – | – | – | – |

No GPU jobs (0 MiB). T20 is done. T21 is the gate (`blocked`), so nothing else starts.

## Since last update
- T20 done (eval only, ~10 min of GPU): `scripts/sysid_check.py` (new), `evaluate.py --robot_params`,
  `eval.sh ... <match> fitted`. Smoke tests passed; the fitted values are applied and checked after build.
  Results in `results/sysid_check.md`, `results/cross_eval.md` "Fitted robot", Finding 11.

## Needs a human
- **Git: an unfinished rebase is left on the server.** My `git pull --rebase` conflicted with Sara's T19 note in
  `notes/log.md`. I resolved it (both sections kept) and staged it, but the agent isn't allowed to run
  `git rebase --continue`. Please run `git rebase --continue && git push` in `/root/dexterity-physics-engines`.
  Until then, none of the T20 results below are on GitHub.
- **T21 gate: T20 numbers** (1,024+ episodes each, `--match_order`; fitted Newton = clamp + 8 substeps + Sara's fit):

  | | Lift | Reorient |
  |---|---|---|
  | PhysX → fitted Newton (fidelity check) | **1.0%** (0.5–1.8), abnormal 88.7% | **0.1%** (0.02–0.6), abnormal 70.9% |
  | PhysX → default Newton (T23) | 0.2%, abnormal 98.5% | 0.0%, abnormal 95.1% |
  | Newton → fitted Newton (control) | **94.8%** (93.2–96.0) | 65.6% (62.7–68.5) |
  | Newton → default Newton (T23) | 86.9% (84.8–88.8) | 63.9% (61.0–66.8) |
  | Newton → PhysX, unchanged (T21 baseline = T23 rows) | 0.0% | 0.0% |

  Hours/$ since 15 Nov: ≈ 7 h ≈ $26 (estimate, see top). Left: ≈ 34 h. T21 stays `blocked` until the planning
  chat decides the next runs.
- **Surprising: the fit's "22 → 0 blow-ups" doesn't reproduce.** In T20's held-out run, the same fitted parameters on
  the same 64 references gave 28 blow-ups, against 26 for the defaults (fit run: 0 vs 22). Many grid points get 0 in
  both runs (188/343 and 220/343). So blow-up counts seem to vary from run to run by more than the gap between
  candidates, and the minimum over 343 candidates picks a lucky one. Fitting on episodes 0–9 gives 0 train blow-ups,
  but the 5/20 held-out signal-c blow-ups stay, the same as the defaults. Suggest a repeatability test before
  training on this fit: the same params, several rollout calls, different env blocks. Not done (not in PLAN).
- Step-response check: not sluggish. Mean overshoot PhysX 38.5%, default Newton 44.5%, fitted 44.4%. Rise times
  are about equal (0.086 / 0.083 / 0.089 s). Steady-state error is 7× PhysX's in both Newton variants (0.014 vs
  0.002 rad). The worst joint is the thumb (thumb_joint_0 overshoot 41 / 76 / 65%).
- Still open from before: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close; ADR-max gravity ≈ −7.1 to
  −7.6, not −9.81.
- Sara: set T19 `done` when you're happy; `results/plots/sysid_loss.png`; "What I learned" notes for T17, T23, T18,
  T25, T25b, T22, T20 (T19's is in); watch the T22 and Reorient clips.
