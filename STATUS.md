# Status
Updated: 2026-11-15 16:00 UTC by the server agent (wake-up: state changed, PLAN.md updated with T16)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

No jobs running. GPU 0 / 46 GB in use, 0% util.

## Since last update
- Nothing changed on the GPU. PLAN.md now has T16 (Unreal replay), marked `running` but run by hand; the agent does nothing for it.
- `~/runs/lift_newton_full.log` still shows up as a crashed log in the watcher. That is T2's old NaN crash at 10,234, which was already resumed and finished. Nothing to do.

## Needs a human
- No `todo` tasks are left (T1–T15 `done`, T16 is by hand). The GPU is idle, so `idle_stop.sh` will stop the instance after 20 minutes unless new tasks are added or the T16 work keeps it busy.
- The 10 Reorient clips (`~/runs/videos/reorient_*`) still need watching, especially to check whether the table is missing in the Newton clips, as it is in the Lift ones.
