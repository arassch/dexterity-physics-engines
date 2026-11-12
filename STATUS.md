# Status
Updated: 2026-11-12 22:25 UTC by the server agent (wake-up: manual --once)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 27/15000 | 0 | — (just started) | 0 | ~12 h (rsl_rl ETA, sharing GPU; early reading) |
| T11 Reorient, 4,096 envs | Newton | 2/15000 | 0 | — (just started) | 0 | ~13 h (rsl_rl ETA, very early reading) |

GPU: 16.8 GB / 46 GB in use, 96–97% utilisation with both runs.

## Since last update
- **T5 done.** Command 2 (Lift Newton 300) had finished normally at ~12:03 (`Training time: 325.43 seconds`).
  Medians over its 100–299: PhysX 1.98 s/it, 8,293 steps/s; Newton 1.09 s/it, 15,073 steps/s (1.82×; difference
  all in collection). Written to `results/speed_benchmark.md`, `notes/log.md`, RUNS.md.
- **Started T10 and T11** together (22:18 and 22:19), per the 11:54 plan. Both log `Learning iteration` lines.
  Early-stop checks begin once they pass iteration 5,000.
- Nothing ran on the GPU from ~12:03 to 22:16 UTC (no wake-up in between; last idle_stop.log line 12:18).

## Needs a human
- The machine sat idle ~10 h after T5 finished (no wake-up after 12:00). Worth checking why the watcher didn't
  fire, so T10/T11 aren't left unattended overnight.
- If you want the T8/T9 `model_299.pt` files in the repo, say so (they're on the server).
- The T7 and T12 clips are ready to watch.
