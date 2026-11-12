# Plan

This file is the contract between the planning chat and the server agent.

- **Humans own this file** (Sara, and Claude in the planning chat). To change direction, edit it and push.
- **The server agent may only:** change a task's `status`, fill in `run_folder` and `result`, and add dated lines under
  "Agent notes" at the bottom. It never adds, removes or rewrites tasks or rules.
- Statuses: `todo` (start when its requirements are met) · `running` · `done` · `blocked` (needs a human; don't start) ·
  `hold` (deliberately paused; don't start) · `failed` (gave up after the crash policy; needs a human).

## Rules

- At most **2** GPU jobs at the same time. A task marked `exclusive` needs the GPU to itself.
- Defaults for every training run: 512 envs, seed 42, `presets=cube`, 15,000 iterations. Never change rewards, configs
  or these defaults unless a task here says so. **Exception (decided Thu 12 Nov): Reorient from T8 on uses 4,096 envs**
  (NVIDIA's default for Reorient), via `--envs 4096`. Lift stays at 512.
- Crash policy for training runs:
  - NaN / simulation divergence: resume from the latest checkpoint for the remaining iterations. At most **2**
    automatic resumes per task; after that set the task to `failed` and explain in STATUS.md.
  - Any other crash (out of memory, import error, missing file, ...): don't retry. Set `failed` and explain.
- When a training run finishes: back it up (see CLAUDE.md), record final metrics, set `done`.
- Start `todo` tasks in the order listed, as soon as their requirements are met.

## Tasks

### T1 · Lift · PhysX baseline
- status: done
- command: `scripts/train.sh lift physx`
- run_folder: `2026-11-11_11-08-26`
- result: training success ~93–98%, abnormal_robot ~2%, ADR 0.99

### T2 · Lift · Newton
- status: done
- command: `scripts/train.sh lift newton` (+ resume after NaN at 10,234)
- run_folder: `2026-11-11_13-06-41` (+ resume folder, see RUNS.md)
- result: training success ~86%, abnormal_robot ~14%, ADR 0.98, 1 NaN crash

### T3 · Reorient · PhysX baseline
- status: done
- command: `scripts/train.sh reorient physx`
- started: Wed 11 Nov 23:21, log `~/runs/reorient_physx_full.log`
- run_folder: `2026-11-11_23-23-11`
- result: training success ~4% (last-500 mean 4.2%), abnormal_robot ~1%, ADR 0.005; plateaued from ~3,000 its

### T4 · Reorient · Newton (512 envs)
- status: running
- command: `scripts/train.sh reorient newton`
- started: Thu 12 Nov ~09:31, log `~/runs/reorient_newton_full.log`, run_folder `2026-11-12_09-31-46`
- **stop condition (decided Thu 12 Nov):** at the first wake-up at or after iteration **3,000**, stop it with
  `scripts/stop_run.sh <pid>`. It isn't worth finishing: like T3 it runs 512 envs, which is likely too few for
  Reorient. Before stopping, record in `notes/log.md` the early-termination phase as a table every 250 iterations
  (abnormal_robot, mean episode length, mean reward, success) and whether it recovered, compared with T2 (Lift Newton)
  over the same iterations. Back it up like a finished run (latest checkpoint, configs, last 60 log lines), and set
  status `done` with result "stopped at iteration N by plan".
- result:

### T5 · Speed benchmark (exclusive)
- status: todo
- requires: T4, T8 and T9 not `running` or `todo`, and no other GPU job running (exclusive)
- commands, one after the other, each alone on the GPU:
  1. `scripts/train.sh lift physx 300`
  2. `scripts/train.sh lift newton 300`
- on done: write `results/speed_benchmark.md` with, for each engine, the median "Iteration time", "Steps per second",
  "Collection time" and "Learning time" over iterations 100–299, plus GPU name. No checkpoints to back up.
- run_folder:
- result:

### T6 · Cross-evaluation · Lift 2×2
- status: todo
- requires: at most one other GPU job running. Run the evaluations **one at a time**.
- checkpoints (repo copies, final policies): PhysX `checkpoints/lift_physx/model_14999.pt`,
  Newton `checkpoints/lift_newton/model_14999.pt`.
- step 1, smoke test (16 envs, 32 episodes, a couple of minutes each):
  `scripts/eval.sh smoke lift physx physx checkpoints/lift_physx/model_14999.pt`, then
  `scripts/eval.sh smoke lift physx newton checkpoints/lift_physx/model_14999.pt`.
  Check `results/cross_eval_smoke.csv` has a row per run with `episodes` ≥ 32 and a plausible `success_rate`.
  If `scripts/evaluate.py` fails, you may fix **mechanical** bugs in it (imports, API names, argument handling,
  reading `extras`), never what it measures. Record each fix in `notes/log.md`. After two failed fix attempts, set
  `blocked` and put the error excerpt in STATUS.md.
- step 2, the four cells, 1,024 episodes each, one after another (each takes minutes, not hours):
  1. `scripts/eval.sh lift physx physx checkpoints/lift_physx/model_14999.pt`
  2. `scripts/eval.sh lift physx newton checkpoints/lift_physx/model_14999.pt`
  3. `scripts/eval.sh lift newton newton checkpoints/lift_newton/model_14999.pt`
  4. `scripts/eval.sh lift newton physx checkpoints/lift_newton/model_14999.pt`
- on done: write `results/cross_eval.md` with the 2×2 table (success rate with 95% interval, and the
  `term_abnormal_robot` fraction in each cell), add "Finding 2" to `notes/log.md` with the numbers, fill in the
  README's cross-evaluation table, and commit `results/cross_eval.csv` and `results/cross_eval_smoke.csv`.
  Don't commit anything `evaluate.py` may have written next to the checkpoints.
- result:

### T7 · Record training-progress videos · Lift
- status: todo
- requires: no `scripts/eval.sh` job running, and at most one other GPU job.
- commands (each records several checkpoints in the background; wait for the one before to finish):
  1. `scripts/record_videos.sh lift physx 2026-11-11_11-08-26 250 1000 3000 8000 14999`
  2. `scripts/record_videos.sh lift newton 2026-11-11_13-06-41 250 1000 3000 8000 10000`
  3. `scripts/record_videos.sh lift newton <Lift Newton resume folder, see RUNS.md> 14999`
- clips land in `~/runs/videos/lift_<engine>/model_<N>.mp4`. **Don't commit the .mp4 files.** Write
  `results/videos.md` listing each clip with its size and checkpoint, and note anything visible in the logs.
  If no video is produced (camera/rendering error), set `blocked` with the error excerpt in STATUS.md.
- result:

### T8 · Reorient timing run · PhysX · 4,096 envs (exclusive)
- status: todo
- requires: T4 not `running`, and no other GPU job running (exclusive)
- command: `scripts/train.sh reorient physx 300 --envs 4096`
- while it runs, check `nvidia-smi` a few times and note peak GPU memory and utilisation.
- on done: write the numbers into `results/reorient_4096_timing.md`: median "Iteration time", "Steps per second",
  "Collection time", "Learning time" over iterations 100–299; peak GPU memory; success/ADR at 300; and the estimate
  for 15,000 iterations in hours and dollars (at $3.65/hr). If it crashes (e.g. out of memory), record the error and
  set `failed`; don't retry.
- run_folder:
- result:

### T9 · Reorient timing run · Newton · 4,096 envs (exclusive)
- status: todo
- requires: T8 not `running` or `todo`, and no other GPU job running (exclusive)
- command: `scripts/train.sh reorient newton 300 --envs 4096`
- same measurements as T8, added to `results/reorient_4096_timing.md` as a second column.
- **then stop and ask:** put the two full-run estimates under "Needs a human" in STATUS.md. Do not start T10 or T11;
  the planning chat decides iterations and budget from these numbers.
- run_folder:
- result:

### T10 · Reorient · PhysX · 4,096 envs (full run)
- status: hold
- command: decided after T8/T9 (likely `scripts/train.sh reorient physx <iters> --envs 4096`)

### T11 · Reorient · Newton · 4,096 envs (full run)
- status: hold
- command: decided after T8/T9 (likely `scripts/train.sh reorient newton <iters> --envs 4096`)

## Agent notes

<!-- The server agent adds dated one-line notes here, newest last. -->
- 2026-11-12 10:10 UTC: T3 finished normally (no Traceback); backed up model_14999.pt, configs, final excerpt; set `done`. T4 resumes used: 0/2.
