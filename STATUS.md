# Status
Updated: 2026-11-15 15:50 UTC by the server agent (wake-up: state changed, last video jobs finished)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

No jobs running. GPU 0 / 46 GB in use, 0% util.

## Since last update
- T14 cmd 1 (Reorient PhysX progress clips) finished: 4 clips (1000, 5000, 10000, 14999), no Traceback.
- T15 cmd 2 (Newton policy in PhysX) finished: `reorient_newton_policy_in_physx/model_14999.mp4` (586,896 B), no Traceback.
- Wrote the Reorient T14/T15 sections in `results/videos.md` and a note in `notes/log.md`; set T14 and T15 `done`.

## Needs a human
- Every task in PLAN.md is `done`; none are `todo`. The GPU is idle, so `idle_stop.sh` will stop the instance after 20 minutes unless new tasks are added.
- The 10 Reorient clips (`~/runs/videos/reorient_*`) need watching, especially to check whether the table is missing in the Newton clips, as it is in the Lift ones.
