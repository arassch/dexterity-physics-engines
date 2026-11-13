# Status
Updated: 2026-11-13 20:12 UTC by the server agent (wake-up: state changed, T10 training process ended)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T13 cell 1 (PhysX policy → PhysX) | PhysX | eval, 1,024 eps | — | — | — | minutes |
| T13 cell 2 (PhysX policy → Newton) | Newton | eval, 1,024 eps | — | — | — | minutes |
| T13 cell 3 (Newton policy → Newton) | Newton | eval, 1,024 eps | — | — | — | minutes |
| T13 cell 4 (Newton policy → PhysX) | PhysX | eval, 1,024 eps | — | — | — | minutes |

GPU: 10.8 GB / 46 GB in use, 60% util, all four evals past policy loading, no errors so far.

## Since last update
- T10 (Reorient PhysX, 4,096 envs) **finished normally** at 15,000 (78,164 s, 0 resumes). Training-time last-500
  means: success 49.8%, abnormal_robot 0.013, reward 9.62; ADR 0.501 at the end. Still improving (+7.65 pp vs
  12,500–12,999). Backed up `checkpoints/reorient_physx_4096/model_14999.pt`, configs, final excerpt; set `done`.
- Started T13 (Reorient cross-eval): all four cells in parallel. Results get written on the next wake-up.

## Needs a human
- nothing
