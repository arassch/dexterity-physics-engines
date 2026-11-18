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
| 11 | Reorient | PhysX | 15,000 max (**4,096 envs**, T10, shares GPU with #12) | `2026-11-12_22-18-09` | Thu 22:18 | Done, 78,164 s (21.7 h), 0 crashes | Training success last-500 mean 49.8% (final 45.8%), abnormal_robot 500-it mean 0.013, ADR 0.501, mean reward 500-it mean 9.62 (final 9.66); 6.6 s/it sharing GPU (its 5,000–5,499), 3.14 s/it alone (last 500) |
| 12 | Reorient | Newton | 15,000 max (**4,096 envs**, T11, shares GPU with #11) | `2026-11-12_22-19-43` | Thu 22:19 | Done, 57,142 s (15.9 h), 0 crashes | Training success last-500 mean 64.7% (final 66.0%), abnormal_robot 500-it mean 0.300 (final 0.296), ADR 0.853, mean reward ~9.1 (final 9.47), ~3.9 s/it sharing GPU |
| 13 | Lift | PhysX | 5 (T22 step 0 check, `--override env.rewards.action_l2.weight=0`) | `2026-11-16_12-44-30` | Mon 12:44 | Done, 12.19 s | Check only: `params/env.yaml` shows `action_l2` `weight: 0` |
| 14 | Lift | PhysX | 3,000 (T22 A `noactpen`: action_l2 = action_rate_l2 = 0) | `2026-11-16_12-45-44` | Mon 12:45 | Done, 13,652 s (3.79 h), no crash | Final (iter 2999): success 0.00 (training, with exploration noise; 0.0 throughout), abnormal_robot 0.017, ADR 0.0002, mean reward 8.63, 2.33 s/iter. `checkpoints/lift_physx_noactpen/model_2999.pt`; log `~/runs/lift_physx_3000_noactpen.log` |
| 15 | Lift | PhysX | 3,000 (T22 B `nograsp`: good_finger_contact = contact_count = 0) | `2026-11-16_12-46-44` | Mon 12:46 | Done, 12,814 s (3.56 h), no crash | Final (iter 2999): success 0.93 (training, with exploration noise), abnormal_robot 0.017, ADR 0.986, mean reward 19.05, 4.25 s/iter. `checkpoints/lift_physx_nograsp/model_2999.pt`; log `~/runs/lift_physx_3000_nograsp.log` |
| 16 | Lift | Newton corrected (clamp + 8 substeps, T21a) | 8,000 | `2026-11-18_11-24-37` (shared with #17 until 11:46, see below) | Wed 11:24 | Done, 19,578 s (5.44 h), no crash | Final (iter 7999): success 0.00 (training, with exploration noise; 0.00 at 2k/4k/6k/8k), abnormal_robot 0.040, ADR 0.0002, mean reward 6.93, 2.46 s/iter (shared GPU). `checkpoints/lift_newton_corr/model_7999.pt`; log `~/runs/lift_newton_corr_8000.log` |
| 17 | Lift | Newton corrected + `--finger_dr` (T21b, first start) | 8,000 | `2026-11-18_11-24-37` (shared with #16) | Wed 11:24 | Stopped by hand at iter 368 (11:45, planning-chat decision), restarted as #18 | – |
| 18 | Lift | Newton corrected + `--finger_dr` (T21b restart, `--run_name corr_dr`) | 8,000 | `2026-11-18_11-46-21_corr_dr` | Wed 11:46 | Stopped by hand at iter 5,134 (17:05, Sara's decision: never lifted) | Last (iter 5134): success 0.00 (training, with exploration noise; 0.00 at 2k/4k/5k), abnormal_robot 0.020, ADR 0.0002, mean reward 6.70, 2.5 s/iter alone (3.7–3.9 shared). `checkpoints/lift_newton_corr_dr/model_5000.pt`; log `~/runs/lift_newton_corr_dr_8000_r2.log` |
| 19 | Lift | Newton corrected, no grasp rewards (T21c, `--run_name corr_nograsp`) | 3,000 | `2026-11-18_17-04-21_corr_nograsp` | Wed 17:04 | Done, 6,903 s (1.92 h), no crash | Final (iter 2999): success 0.90 (training, with exploration noise; 0.00 at 1k, 0.31 at 2k), abnormal_robot 0.077, ADR 0.977, mean reward 21.84, 2.51 s/iter (shared GPU). `checkpoints/lift_newton_corr_nograsp/model_2999.pt`; log `~/runs/lift_newton_corr_nograsp_3000.log` |
| 20 | Lift | Newton corrected + `--finger_dr`, no grasp rewards (T21d, `--run_name corr_dr_nograsp`) | 3,000 | `2026-11-18_17-05-09_corr_dr_nograsp` | Wed 17:05 | Running | – |

Runs 16–17: `scripts/run_isaac.sh lift_newton_corr[_dr]_8000 train_clamped.py --num_substeps 8 [--finger_dr] --task
Isaac-Dexsuite-Kuka-Allegro-Lift-v0 --headless --num_envs 512 physics=newton_mjwarp presets=cube --seed 42
agent.max_iterations=8000`, logs `~/runs/lift_newton_corr_8000.log` / `~/runs/lift_newton_corr_dr_8000.log`. Both
started in the same second, so they write to **one** run folder: `model_N.pt` from the slower run (#17) overwrites
#16's. Tensorboard event files are separate (pids 14022 = #16, 14025 = #17). Next time, pass `--run_name`.
#17 was stopped at iteration 368, so in `2026-11-18_11-24-37` `model_250.pt` (written 11:39) is #17's and
`model_0.pt`/`model_500.pt` onward are #16's. #18 = the same command as #17 plus
`--run_name corr_dr`, log `~/runs/lift_newton_corr_dr_8000_r2.log` (pid 19247).

Runs 19–20 (T21 step 2b): `scripts/run_isaac.sh lift_newton_corr[_dr]_nograsp_3000 train_clamped.py --num_substeps 8
[--finger_dr] --task Isaac-Dexsuite-Kuka-Allegro-Lift-v0 --headless --num_envs 512 physics=newton_mjwarp presets=cube
--seed 42 agent.max_iterations=3000 --run_name corr[_dr]_nograsp env.rewards.good_finger_contact.weight=0
env.rewards.contact_count.weight=0`. Both logs' reward tables show the two terms at weight 0. Started 48 s apart.

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
