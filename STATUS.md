# Status
Updated: 2026-11-18 10:58 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 8.2 h ≈ $30** (estimate: 7.3 h at the last STATUS, about 0.4 h
yesterday until `idle_stop.log` ends at 17:10, and this wake-up from 10:27 to about 11:00). About 32.8 h ≈ $120 left
of the $150. Please correct this from the Brev console if it's off.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| – | – | – | – | – | – | – |

No GPU jobs. T26b is `done`; T21 is `blocked` (gate).

## Since last update
- Already committed before this wake-up (51e3ea1): T26b steps 1, 2, 3.1, 3.2 and 4.
- Ran step 3.3: Sara's fit with ADR frozen at max, `--repeats 4` (block noise from step 3.2 ≈ 4–5 blow-ups, about
  the size of the gaps between candidates) → `results/sysid_robot_adrmax.json`. The first launch failed straight
  away on a relative `--ref` path (`~/runs/sysid_fit_adrmax.log`, FileNotFoundError). I relaunched it with an
  absolute path (`~/runs/sysid_fit_adrmax2.log`).
- Ran step 3.4: `sysid_check.py --tag adrmax` → `results/sysid_check_adrmax.md` / `.json`, 3 plots `*_adrmax.png`.
- Wrote Finding 13 in `notes/log.md`; T26b set to `done`.

## Needs a human
- **T26b results (Finding 13).** The call-1 effect was ADR demotion: unfrozen, difficulty 10 → 8.0 at the first
  signal → 2.5 by call 2, signal c, and gravity −7.85 → −2.44. With `--freeze_adr`: 10 and −9.81 in every signal and
  call.
- **Old fit vs ADR-max fit** (blow-ups per 64 references, ADR frozen):

  | | armature | damping | effort | blow-ups | loss |
  |---|---|---|---|---|---|
  | default | 0.0100 | ×1.000 | ×1.000 | 62.6 ± 4.4 (repeat) / 65.5 ± 5.9 (fit) | 0.649 |
  | old fit (T19) | 0.0131 | ×1.149 | ×1.591 | 54.5 ± 5.2 (repeat) | 0.586 |
  | ADR-max fit | 0.0923 | ×0.545 | ×1.206 | 34.5 ± 6.0 (fit) | 1.244 |
  | coarse-grid lowest loss | 0.0100 | ×1.741 | ×1.149 | 46.0 ± 5.2 | 0.522 |

  `choose_best` ranks by blow-ups first, so the new fit halves blow-ups at the cost of nearly double the tracking loss,
  with armature and damping close to their bounds. `sysid_check`: step rise time 0.199 s vs PhysX 0.086 s (default
  0.083), overshoot 90 % vs 39 % (default 47 %). Held-out blow-ups 16 vs default 18 (within noise); the train-only
  best is a different point (0.0398, ×2.64, ×0.871). **My reading: the ADR-max fit is worse than the default as a
  model of PhysX's drives.** Is it worth using for T21 at all? Should `choose_best` (Sara's) weigh loss more? Or should
  the blow-up penalty treat ±6 as a tie?
- **Eval cells, ADR frozen vs drifting:** Reorient PhysX → fitted Newton (old fit) 0.29 % vs 0.10 %; PhysX → PhysX
  51.0 % vs 51.5 %. The drift barely matters for closed-loop evals.
- T21 gate: waiting for the planning chat's decision. Nothing started.
- Still open: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when you're happy;
  "What I learned" notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
