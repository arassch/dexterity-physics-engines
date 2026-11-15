# Status
Updated: 2026-11-15 15:45 UTC by the server agent (wake-up: state changed, video jobs moved on)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T14 cmd 1 (Reorient PhysX progress clips) | PhysX | video: 1000, 5000 saved; recording 10000, then 14999 | — | — | — | ~3 min |
| T15 cmd 2 (Reorient Newton policy in PhysX, 14999) | PhysX | video: started 15:42, loading | — | — | — | ~2 min |

No training runs. GPU 7.7 / 46 GB, 41% util.

## Since last update
- T14 cmd 2 (Newton) finished: 4 clips saved, no Traceback (model_1000 240K, 5000 272K, 10000 388K, 14999 364K).
- T15 cmd 1 (PhysX policy in Newton) finished 15:39: `reorient_physx_policy_in_newton/model_14999.mp4` (556K), no Traceback.
- Started T15 cmd 2 (Newton policy in PhysX), log `~/runs/videos_reorient_newton_policy_in_physx.log`.
- `results/videos.md` Reorient section will be written once T14 cmd 1 and T15 cmd 2 finish.

## Needs a human
- nothing
