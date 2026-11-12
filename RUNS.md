# Training runs

Every run, with the exact command it was started with and where its output lives.
All runs: 512 environments unless the table says otherwise, seed 42, `presets=cube`, Isaac Lab 3.0.0 (see [`setup/ENVIRONMENT.md`](setup/ENVIRONMENT.md)).
Output folders are under `/workspace/isaaclab/logs/rsl_rl/dexsuite_kuka_allegro/` on the Brev instance.

| # | Task | Engine | Iterations | Run folder | Started | Status | Final training success |
|---|---|---|---|---|---|---|---|
| 1 | Lift | PhysX | 300 (timing) | `2026-11-11_10-38-19` | Wed 10:38 | Done | ~0–2% |
| 2 | Lift | PhysX | 15,000 | `2026-11-11_11-08-26` | Wed 11:08 | Done | ~93–98% |
| 3 | Lift | Newton | 15,000 (crashed at 10,234) | `2026-11-11_13-06-41` | Wed 13:06 | NaN crash | 73–89% at crash |
| 4 | Lift | Newton | +5,000 (resume of #3 from `model_10000.pt`) | `2026-11-11_23-21-33` | Wed ~23:22 | Done | ~86% |
| 5 | Reorient | PhysX | 15,000 | `2026-11-11_23-23-11` | Wed 23:21 | Done (Thu ~10:02, 38,365 s) | ~4% (mean of last 500 its: 4.2%) |
| 6 | Reorient | Newton | 15,000 (stopped at 3,315 by plan) | `2026-11-12_09-31-46` | Thu ~09:31 | Stopped Thu 10:49 (1 h 16 min) | 0% (abnormal_robot 0.10, ADR 0, reward 8.1, 1.09 s/it) |
| 7 | Reorient | PhysX | 300 (timing, **4,096 envs**, T8) | `2026-11-12_11-11-43` | Thu 11:11 | Done, 931.65 s (15.5 min) | Median iteration 3.19 s, 41.1k steps/s, ~9.3 GB; success 0, ADR 0, abnormal_robot 0.010, mean reward 3.63 at 299 |
| 8 | Reorient | Newton | 300 (timing, **4,096 envs**, T9) | `2026-11-12_11-32-53` | Thu 11:32 | Done, 520.61 s (8.7 min) | Median iteration 1.80 s, 72.8k steps/s, ~7.7 GB (early reading); success 0, ADR 0, abnormal_robot 0.079, mean reward 5.90 at 299 |
| 9 | Lift | PhysX | 300 (speed benchmark, T5, alone on GPU) | `2026-11-12_11-46-23` | Thu 11:46 | Done, 594.88 s | Median iteration 1.98 s, 8,293 steps/s |
| 10 | Lift | Newton | 300 (speed benchmark, T5, alone on GPU) | `2026-11-12_11-57-32` | Thu 11:57 | Done, 325.43 s | Median iteration 1.09 s, 15,073 steps/s; abnormal_robot 0.91 at 299 |
| 11 | Reorient | PhysX | 15,000 max (**4,096 envs**, T10, shares GPU with #12) | `2026-11-12_22-18-09` | Thu 22:18 | Running | — |
| 12 | Reorient | Newton | 15,000 max (**4,096 envs**, T11, shares GPU with #11) | `2026-11-12_22-19-43` | Thu 22:19 | Running | — |

Runs 2–3 and 4–5 shared one GPU, so their wall-clock times are not a fair speed comparison.

## Commands

With [`scripts/train.sh`](scripts/train.sh), each run is one line (run from the repo folder on the instance):

```bash
scripts/train.sh lift physx 300          # 1
scripts/train.sh lift physx              # 2
scripts/train.sh lift newton             # 3
scripts/train.sh lift newton 5000 --resume 2026-11-11_13-06-41 model_10000.pt   # 4 (iterations are additional)
scripts/train.sh reorient physx          # 5
scripts/train.sh reorient newton         # 6
scripts/train.sh reorient physx 300 --envs 4096   # 7
scripts/train.sh reorient newton 300 --envs 4096  # 8
scripts/train.sh lift physx 300                   # 9
scripts/train.sh lift newton 300                  # 10
scripts/train.sh reorient physx 15000 --envs 4096 # 11
scripts/train.sh reorient newton 15000 --envs 4096 # 12
```

The script expands to the command actually typed for each run, for example run 3:

```bash
cd /workspace/isaaclab
PYTHONUNBUFFERED=1 nohup ./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Dexsuite-Kuka-Allegro-Lift-v0 --headless \
  --num_envs 512 physics=newton_mjwarp presets=cube \
  --seed 42 agent.max_iterations=15000 \
  > ~/runs/lift_newton_full.log 2>&1 &
```

(Runs 1 and 2 were started before `PYTHONUNBUFFERED=1` was added; that only affects how promptly the log updates.)
