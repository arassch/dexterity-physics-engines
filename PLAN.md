# Plan

This file is the contract between the planning chat and the server agent.

- **Humans own this file** (Sara, and Claude in the planning chat). To change direction, edit it and push.
- **The server agent may only:** change a task's `status`, fill in `run_folder` and `result`, and add dated lines under
  "Agent notes" at the bottom. It never adds, removes or rewrites tasks or rules.
- Statuses: `todo` (start when its requirements are met) · `running` · `done` · `blocked` (needs a human; don't start) ·
  `hold` (deliberately paused; don't start) · `failed` (gave up after the crash policy; needs a human).

## Goal (Sara, Sun 15 Nov)

This project has two goals: end with **something to show** (video, figures, README and write-up), and **learn what
robotics roles ask for** along the way: simulation and system ID (Machenta, Wayve, NVIDIA), and RL, meaning reward
design, randomisation and distillation (DeepMind, Humanoid, Machenta Robot Learning). So:

- Every task ends with an output that can be shown: a figure, a table or a clip.
- Tasks marked **by Sara** are the core skills. The agent prepares their data and harness, then sets them `blocked`
  and waits; it doesn't write those parts.
- After each agent task, Sara reads its scripts and writes a short "What I learned" note in `notes/log.md`. The agent
  doesn't write these.

## Rules

- GPU job limits (changed Thu 12 Nov 10:47, to make better use of the machine): at most **2 training runs**
  (`scripts/train.sh`) **plus up to 4 evaluation/video jobs** (`scripts/eval.sh`, `scripts/record_videos.sh`) at the
  same time. A task marked `exclusive` still needs the GPU to itself (no other job of any kind). Don't start a new job
  if `nvidia-smi` shows more than 40 GB of the 46 GB in use.
- Defaults for every training run: 512 envs, seed 42, `presets=cube`, 15,000 iterations. Never change rewards, configs
  or these defaults unless a task here says so. **Exception (decided Thu 12 Nov): Reorient from T8 on uses 4,096 envs**
  (NVIDIA's default for Reorient), via `--envs 4096`. Lift stays at 512.
- Crash policy for training runs:
  - NaN / simulation divergence: resume from the latest checkpoint for the remaining iterations. At most **2**
    automatic resumes per task; after that set the task to `failed` and explain in STATUS.md.
  - Any other crash (out of memory, import error, missing file, ...): don't retry. Set `failed` and explain.
- When a training run finishes: back it up (see CLAUDE.md), record final metrics, set `done`.
- Start `todo` tasks in the order listed, as soon as their requirements are met.
- **Budget (decided Sun 15 Nov):** $150 for everything from Sun 15 Nov 16:00 UTC on, at $3.65/hr ≈ **41 instance-hours**,
  idle time included. At every wake-up, put "instance hours since 15 Nov 16:00 UTC" and "≈ $ spent" at the top of
  STATUS.md (from `uptime` and the start/stop times you can see in logs; say if it's an estimate). If the estimate
  passes **$120**, don't start any new task: write it under "Needs a human" and wait.
- **How to run the new scripts (T17–T20):** launch every new Python script with `scripts/run_isaac.sh <log_name> <script.py> [args]` (background, log in `~/runs/<log_name>.log`), never with `./isaaclab.sh` directly: that is the only way it is allowed, and the only way `idle_stop.sh` counts it as activity. Install packages only with `scripts/pip_install.sh cma` (or `matplotlib`). Test each new script on a few envs and steps first; after two failed fix attempts on one script, set the task `blocked` with the error in STATUS.md.

## Answers from humans

- 2026-11-17 16:42 (Sara, planning chat): T20 read. The rebase is finished and pushed (a9a0f53). Next is T26
  (repeatability), then the T21 gate; the planning chat's default for T21 is the sim-to-real Lift run (train in
  corrected Newton with randomisation around the fitted values, deploy in PhysX), decided after T26.

- 2026-11-16 16:35 (planning chat): T19 — the per-physics-step velocity clamp fallback is fine; don't debug the
  per-substep hook. Go ahead with `scripts/train_clamped.py` for the speed test (and later for T21's training).

- **2026-11-16 14:05 (Sara): one direction only from now on. PhysX is the "real robot" (ground truth); Newton (MuJoCo
  Warp) is the simulator we calibrate.** We stop trying to make transfer work both ways. Consequences:
  - Calibration data always comes from PhysX; parameters are only ever changed in Newton.
  - The experiment that matters is the sim-to-real one: **train in (calibrated) Newton, deploy in PhysX**. Report
    Newton → PhysX as the main transfer number; PhysX → Newton is a fidelity check of the calibrated simulator (a
    policy that works on the "real" robot should also work in a good simulator).
  - T25 diagnoses where Newton's robot differs from PhysX's, as before; read its results with PhysX as the reference.

- 2026-11-16 13:46 (Sara): contacts come second. Most PhysX → Newton blow-ups happen before the hand reaches the cube
  (notes/log.md, 13:45), so T18–T20 (drives only) go first. A contact-response test (press, slide, hold; a possible
  T24) is decided at the T21 gate, depending on how much T20 recovers. Don't start it before then.

- 2026-11-15 16:10: New phase. The finding that matters: in both tasks, PhysX policies hit `abnormal_robot` in Newton
  within ~23–35 control steps, before real contact with the cube. So the gap is probably in the **robot** (PD drives,
  armature, joint friction, limits, solver), not the cube. T17–T20 test that using evaluation only, with no training.
  T21 is the gate: stop and ask before any new training run.
- 2026-11-15 15:40: Fri 20:25 the instance was stopped by `idle_stop.sh` during the T13 evals (it ignored
  `scripts/evaluate.py`; fixed in e74f2f8). On restart: if `results/cross_eval.csv` lacks any of the four Reorient
  cells, rerun just the missing ones, then write T13 up as planned. Then T14 and T15.
- 2026-11-12 22:30: the 12:03–22:16 idle gap wasn't a watcher bug. The Claude token allowance ran out, so no wake-up
  could run, and Sara stopped the instance. Nothing to fix; drop it from "Needs a human". Leave the T8/T9 `model_299.pt`
  files on the server (no need in the repo). Sara has watched the T7/T12 clips (her notes are in `notes/log.md`).

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
- status: done
- command: `scripts/train.sh reorient newton`
- started: Thu 12 Nov ~09:31, log `~/runs/reorient_newton_full.log`, run_folder `2026-11-12_09-31-46`
- **stop condition (decided Thu 12 Nov):** at the first wake-up at or after iteration **3,000**, stop it with
  `scripts/stop_run.sh <pid>`. It isn't worth finishing: like T3 it runs 512 envs, which is likely too few for
  Reorient. Before stopping, record in `notes/log.md` the early-termination phase as a table every 250 iterations
  (abnormal_robot, mean episode length, mean reward, success) and whether it recovered, compared with T2 (Lift Newton)
  over the same iterations. Back it up like a finished run (latest checkpoint, configs, last 60 log lines), and set
  status `done` with result "stopped at iteration N by plan".
- result: stopped at iteration 3,315 by plan (success 0, abnormal_robot 0.10 after recovering from ~0.99, ADR 0; backed up model_3250.pt)

### T5 · Speed benchmark (exclusive)
- status: done
- requires: T4, T8 and T9 not `running` or `todo`, and no other GPU job running (exclusive)
- commands, one after the other, each alone on the GPU:
  1. `scripts/train.sh lift physx 300`
  2. `scripts/train.sh lift newton 300`
- on done: write `results/speed_benchmark.md` with, for each engine, the median "Iteration time", "Steps per second",
  "Collection time" and "Learning time" over iterations 100–299, plus GPU name. No checkpoints to back up.
- run_folder: command 1 `2026-11-12_11-46-23` (log `~/runs/lift_physx_300.log`); command 2 `2026-11-12_11-57-32` (log `~/runs/lift_newton_300.log`)
- result: median iteration PhysX 1.98 s vs Newton 1.09 s (8,293 vs 15,073 steps/s; collection 1.865 vs 0.978 s, learning 0.105 vs 0.109 s), L40S; see `results/speed_benchmark.md`

### T6 · Cross-evaluation · Lift 2×2
- status: done
- note (planning chat, 10:35): `scripts/eval.sh` and `scripts/record_videos.sh` are in the allow-list in
  `scripts/agent_tick.sh` since commit bbcf783; your 10:30 wake-up started before you pulled it. No watcher restart
  needed. Go ahead with T6, then T7. Stopping T4 at 3,000 still takes priority when you see it.
- requires: the GPU job limits above. The four step-2 cells may run **at the same time** (they're independent).
- checkpoints (repo copies, final policies): PhysX `checkpoints/lift_physx/model_14999.pt`,
  Newton `checkpoints/lift_newton/model_14999.pt`.
- step 1, smoke test (16 envs, 32 episodes, a couple of minutes each):
  `scripts/eval.sh smoke lift physx physx checkpoints/lift_physx/model_14999.pt`, then
  `scripts/eval.sh smoke lift physx newton checkpoints/lift_physx/model_14999.pt`.
  Check `results/cross_eval_smoke.csv` has a row per run with `episodes` ≥ 32 and a plausible `success_rate`.
  If `scripts/evaluate.py` fails, you may fix **mechanical** bugs in it (imports, API names, argument handling,
  reading `extras`), never what it measures. Record each fix in `notes/log.md`. After two failed fix attempts, set
  `blocked` and put the error excerpt in STATUS.md.
- step 2, the four cells, 1,024 episodes each, started together (each takes minutes, not hours):
  1. `scripts/eval.sh lift physx physx checkpoints/lift_physx/model_14999.pt`
  2. `scripts/eval.sh lift physx newton checkpoints/lift_physx/model_14999.pt`
  3. `scripts/eval.sh lift newton newton checkpoints/lift_newton/model_14999.pt`
  4. `scripts/eval.sh lift newton physx checkpoints/lift_newton/model_14999.pt`
- on done: write `results/cross_eval.md` with the 2×2 table (success rate with 95% interval, and the
  `term_abnormal_robot` fraction in each cell), add "Finding 2" to `notes/log.md` with the numbers, fill in the
  README's cross-evaluation table, and commit `results/cross_eval.csv` and `results/cross_eval_smoke.csv`.
  Don't commit anything `evaluate.py` may have written next to the checkpoints.
- result: PhysX→PhysX 95.9%, PhysX→Newton 0.0% (98% abnormal_robot), Newton→Newton 87.0%, Newton→PhysX 0.0%; see `results/cross_eval.md`

### T7 · Record training-progress videos · Lift
- status: done
- requires: the GPU job limits above; may run alongside the T6 cells.
- commands (each records several checkpoints in the background; wait for the one before to finish):
  1. `scripts/record_videos.sh lift physx 2026-11-11_11-08-26 250 1000 3000 8000 14999`
  2. `scripts/record_videos.sh lift newton 2026-11-11_13-06-41 250 1000 3000 8000 10000`
  3. `scripts/record_videos.sh lift newton <Lift Newton resume folder, see RUNS.md> 14999`
- clips land in `~/runs/videos/lift_<engine>/model_<N>.mp4`. **Don't commit the .mp4 files.** Write
  `results/videos.md` listing each clip with its size and checkpoint, and note anything visible in the logs.
  If no video is produced (camera/rendering error), set `blocked` with the error excerpt in STATUS.md.
- result: 11 clips (PhysX 5, Newton 6), no errors; list in `results/videos.md`

### T12 · Transfer clips · Lift (policy in the other engine)
- status: done
- why: sanity-check Finding 2 (0% success across engines both ways) by eye, and the key shot for the video.
- requires: the GPU job limits above (it waits while an exclusive task like T8 runs); start it before T9.
- commands (record one at a time):
  1. PhysX policy in Newton: `scripts/record_videos.sh lift newton 2026-11-11_11-08-26 --out lift_physx_policy_in_newton 14999`
  2. Newton policy in PhysX: `scripts/record_videos.sh lift physx 2026-11-11_23-21-33 --out lift_newton_policy_in_physx 14999`
- clips land in `~/runs/videos/lift_physx_policy_in_newton/` and `~/runs/videos/lift_newton_policy_in_physx/`.
  Don't commit the .mp4 files. Add them to `results/videos.md`, and describe in `notes/log.md` anything the logs show
  (e.g. how many resets happen within the clip). If no video is produced, set `blocked` with the error excerpt.
- result: 2 clips, no errors (PhysX→Newton 556,607 B, Newton→PhysX 786,306 B); see `results/videos.md`

### T8 · Reorient timing run · PhysX · 4,096 envs (exclusive)
- status: done
- requires: T4 not `running`, and no other GPU job running (exclusive)
- command: `scripts/train.sh reorient physx 300 --envs 4096`
- while it runs, check `nvidia-smi` a few times and note peak GPU memory and utilisation.
- on done: write the numbers into `results/reorient_4096_timing.md`: median "Iteration time", "Steps per second",
  "Collection time", "Learning time" over iterations 100–299; peak GPU memory; success/ADR at 300; and the estimate
  for 15,000 iterations in hours and dollars (at $3.65/hr). If it crashes (e.g. out of memory), record the error and
  set `failed`; don't retry.
- run_folder: `2026-11-12_11-11-43` (log `~/runs/reorient_physx_300_4096envs.log`)
- result: median iteration 3.19 s (collection 2.91 s, learning 0.27 s), 41.1k steps/s, peak ~9.3 GB; success 0, ADR 0 at 300; 15,000 its ≈ 13.3 h ≈ $48.5; see `results/reorient_4096_timing.md`

### T9 · Reorient timing run · Newton · 4,096 envs (exclusive)
- status: done
- requires: T8 and T12 not `running` or `todo`, and no other GPU job running (exclusive)
- command: `scripts/train.sh reorient newton 300 --envs 4096`
- same measurements as T8, added to `results/reorient_4096_timing.md` as a second column.
- **then stop and ask:** put the two full-run estimates under "Needs a human" in STATUS.md. Do not start T10 or T11;
  the planning chat decides iterations and budget from these numbers.
- run_folder: `2026-11-12_11-32-53` (log `~/runs/reorient_newton_300_4096envs.log`)
- result: median iteration 1.80 s (collection 1.53 s, learning 0.27 s), 72.8k steps/s, ~7.7 GB; success 0, ADR 0 at 300; 15,000 its ≈ 7.5 h ≈ $27.4 (likely low, still drifting up); see `results/reorient_4096_timing.md`

### T10 · Reorient · PhysX · 4,096 envs (full run)
- status: done
- decided Thu 12 Nov 11:54: run T10 and T11 **at the same time**, 15,000 iterations max, with the early-stop rule below.
- requires: T5 not `running` or `todo` (T5 is exclusive). Start T10 and T11 in the same wake-up, one right after
  the other (wait ~1 minute between them so they don't load at the same moment).
- command: `scripts/train.sh reorient physx 15000 --envs 4096`
- **early-stop rule** (check at every wake-up once the run is past iteration 5,000): compare the mean
  `Metrics/success_rate` over the last 500 iterations with the mean over the 500 iterations that ended 2,000
  iterations earlier (e.g. at 7,000: iterations 6,500–7,000 vs 4,500–5,000). If it improved by **less than 2
  percentage points**, stop the run with `scripts/stop_run.sh <pid>` and treat it as finished. Write both means and
  the decision in `notes/log.md` each time you check after 5,000, so the record shows why it stopped.
- crash policy and backup as in the rules and CLAUDE.md, but back up into `checkpoints/reorient_physx_4096/`,
  `configs/reorient_physx_4096/` and `results/log_excerpts/reorient_physx_4096_final.txt` (the 512-env T3 run keeps
  the `reorient_physx` names). Result: final/stop iteration, success (last-500 mean), abnormal_robot, ADR, reward,
  iteration time while sharing the GPU.
- run_folder: `2026-11-12_22-18-09` (log `~/runs/reorient_physx_15000_4096envs.log`)
- result: finished all 15,000 its (78,164 s, 0 resumes); training success last-500 mean 49.8%, abnormal_robot ~0.013, ADR 0.501, reward ~9.6, 6.6 s/it sharing the GPU / 3.1 s/it alone; backed up model_14999.pt

### T11 · Reorient · Newton · 4,096 envs (full run)
- status: done
- same decision, requirements, early-stop rule and crash policy as T10; start together with T10.
- command: `scripts/train.sh reorient newton 15000 --envs 4096`
- back up into `checkpoints/reorient_newton_4096/`, `configs/reorient_newton_4096/`,
  `results/log_excerpts/reorient_newton_4096_final.txt`.
- run_folder: `2026-11-12_22-19-43` (log `~/runs/reorient_newton_15000_4096envs.log`)
- result: finished all 15,000 its (57,142 s); training success last-500 mean 64.7%, abnormal_robot ~0.30, ADR 0.853, reward ~9.1, ~3.9 s/it sharing the GPU; backed up model_14999.pt

### T13 · Cross-evaluation · Reorient 2×2
- status: done
- requires: T10 and T11 both `done` (finished or stopped early). Same GPU job limits as T6.
- the same procedure as T6 step 2 (no smoke test needed), with the task `reorient` and the 4,096-env checkpoints:
  1. `scripts/eval.sh reorient physx physx checkpoints/reorient_physx_4096/<final>.pt`
  2. `scripts/eval.sh reorient physx newton checkpoints/reorient_physx_4096/<final>.pt`
  3. `scripts/eval.sh reorient newton newton checkpoints/reorient_newton_4096/<final>.pt`
  4. `scripts/eval.sh reorient newton physx checkpoints/reorient_newton_4096/<final>.pt`
- on done: add a Reorient section to `results/cross_eval.md` (same table format as Lift), "Finding 3" in
  `notes/log.md`, and the README.
- result: PhysX→PhysX 51.5%, PhysX→Newton 0.0% (94% abnormal_robot), Newton→Newton 64.9%, Newton→PhysX 0.0%; see `results/cross_eval.md`

### T14 · Record training-progress videos · Reorient
- status: done
- why: the "watch it learn" shot for Reorient, and to check by eye what 50% (PhysX) vs 65% (Newton, 30% abnormal
  resets) success looks like.
- requires: T13 `done` (don't compete with its evals). Commands 1 and 2 may run at the same time.
- commands:
  1. `scripts/record_videos.sh reorient physx 2026-11-12_22-18-09 1000 5000 10000 14999`
  2. `scripts/record_videos.sh reorient newton 2026-11-12_22-19-43 1000 5000 10000 14999`
- clips land in `~/runs/videos/reorient_<engine>/model_<N>.mp4`. Don't commit the .mp4 files. Add a Reorient section
  to `results/videos.md` (same table as Lift). If no video is produced, set `blocked` with the error excerpt.
- result: 8 clips (PhysX 4, Newton 4), no errors; see `results/videos.md`

### T15 · Transfer clips · Reorient (policy in the other engine)
- status: done
- requires: T13 `done`. May run alongside T14.
- commands (one at a time):
  1. PhysX policy in Newton: `scripts/record_videos.sh reorient newton 2026-11-12_22-18-09 --out reorient_physx_policy_in_newton 14999`
  2. Newton policy in PhysX: `scripts/record_videos.sh reorient physx 2026-11-12_22-19-43 --out reorient_newton_policy_in_physx 14999`
- add both to `results/videos.md`; note in `notes/log.md` anything the logs show, next to the T13 numbers.
- result: 2 clips, no errors (PhysX→Newton 565,901 B, Newton→PhysX 586,896 B); see `results/videos.md`

### T16 · Replay in Unreal (run by hand, not by the agent)
- status: running
- why: show the same motion in Unreal Engine, first as USD playback, then driven by a Control Rig.
- done so far (Sun 15 Nov, by hand): `scripts/export_episode.sh` for the four Reorient cells (home and away, both
  engines), files in `~/runs/exports/` and in Sara's Dropbox; `scripts/make_usd_animation.py` builds the USD
  animations on her computer. See `unreal/README.md`.
- Mon 16 Nov 15:34 (Sara): Unreal renders done for PhysX and Newton Reorient (home cells), with the shared camera
  and key light (`lights.usda`). Videos in Sara's Dropbox (`demo_files/unreal/.../VideoCaptures`).
- Mon 16 Nov: USD Stage playback works in Unreal (four Reorient animations, plain colour materials, shared
  `lights.usda`). Still to do by hand when the server is up: the two Lift exports,
  `scripts/export_episode.sh lift physx physx checkpoints/lift_physx/model_14999.pt` and
  `scripts/export_episode.sh lift newton newton checkpoints/lift_newton/model_14999.pt`.
- the server agent does nothing for T16.
- result:

### T17 · Why does `abnormal_robot` fire? (eval only)
- status: done
- why: say exactly which condition ends PhysX → Newton episodes, on which joints, and after how many steps.
- requires: the GPU job limits above. About 30 min of GPU.
- step 1: read `abnormal_robot_state` in Isaac Lab
  (`isaaclab_tasks/manager_based/manipulation/dexsuite/mdp/terminations.py`) and copy into `notes/log.md` exactly what it
  checks and its thresholds.
- step 2: write `scripts/trace_episode.py`, adapted from `scripts/evaluate.py` (same loading, Play config, deterministic
  policy, seed 42). For 16 envs and the first 120 control steps (or until each env's first episode ends), save per step and
  per env: `joint_pos`, `joint_vel`, joint position targets (the processed actions), applied joint torques if the
  articulation exposes them, the soft joint limits, and the per-step termination flags. Save as
  `~/runs/traces/<task>_<train>_in_<eval>.npz`; commit nothing large. Add `scripts/trace_episode.sh` like `eval.sh`.
- step 3: run it for four Reorient cells with the 4,096-env checkpoints: physx→physx, physx→newton, newton→newton,
  newton→physx.
- step 4: write `results/abnormal_robot_diagnosis.md`, keeping it short: for each cell, the median step of the first
  `abnormal_robot`, which sub-condition fired (joint limit, velocity, ...), and the 3 joints that most often break it,
  with the values at that step. Add `scripts/plot_traces.py`, which writes `results/plots/trace_<cell>.png`: for those 3
  joints, target vs actual position over the first 120 steps, both engines on one plot.
- result: only condition is |joint_vel| > 2× limit; PhysX→Newton 14/16 envs, median step 16 (10–35), hand joints only (index_3, middle_1, index_0 …) at 2.6–5.5× limit; PhysX→PhysX 0/16. Engines order hand joints differently (see `results/abnormal_robot_diagnosis.md`)

### T23 · Cross-evaluate with joints matched by name (eval only) · before T18
- status: done
- why: T17 found that PhysX and Newton order the 16 hand joints differently (by level vs by finger). The action term
  (`joint_names=[".*"]`) and the joint observations follow each engine's own order, so in T6/T13 a policy moved to
  the other engine most likely read and drove the wrong hand joints. This task measures transfer with that bug removed.
  Everything after it (T18–T20) depends on the answer.
- requires: the GPU job limits above (eval jobs; may run alongside T22's two training runs).
- step 1: write `results/joint_order.json` from the T17 traces (`scripts/joint_order.py`): for each engine, the 23 joint
  names and the robot body names in articulation order, plus the bodies the `hand_tips_state_b` observation uses
  (`palm_link`, `.*_tip`) in the order each engine resolves them.
- step 2: add `--match_order <engine>` to `scripts/evaluate.py` (and pass it through `scripts/eval.sh` as an optional
  last argument). It makes the run use the *training* engine's order by name, after the config is loaded and before
  the env is built, without changing anything else it measures:
  - action term: `env_cfg.actions.action.joint_names = <training engine's 23 names>`, `preserve_order = True`
  - observations `proprio.joint_pos` and `proprio.joint_vel`: `asset_cfg = SceneEntityCfg("robot", joint_names=<same
    list>, preserve_order=True)`
  - `proprio.hand_tips_state_b`: `body_asset_cfg.body_names = <training engine's tip-body order>`, `preserve_order=True`
  - check every other term that takes a joint or body list (observations, actions; rewards don't matter at eval) and
    list in `notes/log.md` which ones you changed and which were order-independent.
  - at startup print the resolved joint names of the action term and of `joint_pos`, and the hand-tip body names, and
    fail if they don't equal the training engine's lists.
- step 3: smoke test (16 envs, 32 episodes): physx→newton with `--match_order physx`; check the printed lists.
- step 4: 1,024 episodes each, label `reorient_matched` and `lift_matched`, all with `--match_order <train engine>`:
  Reorient physx→newton, newton→physx, and the controls physx→physx, newton→newton (these must match T13 within
  their intervals, or something else changed); the same four for Lift (T1/T2 final checkpoints).
- on done: add a "Joints matched by name" table to `results/cross_eval.md` next to the original ones, "Finding 7" in
  `notes/log.md` (with the numbers), and a line in the README's cross-evaluation section saying the original
  cross-engine cells were confounded by the joint order. If the away cells are no longer ~0%, say so plainly in
  STATUS.md under "Needs a human": the planning chat will revise T18–T20.
- result: away cells still ~0% with joints matched (Lift P→N 0.2% [2/1,027], N→P 0%; Reorient P→N 0%, N→P 0%);
  controls reproduce T6/T13. Finding 7; `results/cross_eval.md` "Joints matched by name"; `results/joint_order.json`.

### T18 · Robot-only step-response test (eval only, no policy)
- status: done
- why: this is our "real-world dataset". Treat PhysX as reality and record how each joint responds to the same command
  in both engines, with no cube involved.
- requires: T17 and T23 `done`. About 30 min of GPU. Compare and replay joints **by name** (`results/joint_order.json`), never by index.
- write `scripts/step_response.py`: Reorient env (Play config, `presets=cube`), 64 envs, ADR at 0 (no randomisation) so
  the robot parameters are the nominal ones. Move the cube far from the hand by resetting it out of reach (if that isn't
  possible, keep the hand far from the table). From the default pose, for each of these signals in turn, send open-loop
  joint position targets: (a) a step of +0.3 rad on one joint at a time (23 joints, other joints held), (b) a 1 Hz sine of
  0.2 rad amplitude on all finger joints together, (c) the first 120 steps of action targets recorded by T17's physx→physx
  trace, replayed open-loop. Record `joint_pos` and `joint_vel` for 120 steps per signal.
- run it on both engines. Save `~/runs/step_response/<engine>.npz`.
- write `results/step_response.md`: for each joint, the rise time (10–90%), overshoot and steady-state error in each engine,
  and the RMS position difference between the engines for signals (a)–(c). Plots in `results/plots/step_<joint>.png`
  for the 6 joints with the biggest difference.
- result: small signals match: mean RMS PhysX−Newton 0.0045 rad (a, steps), 0.0030 rad (b, finger sine); nominal
  stiffness/damping/armature/friction read identical. (c) the PhysX policy's targets replayed open-loop, no cube:
  **28/64 Newton envs reset (steps 15–44), 0/64 PhysX**; RMS before reset 0.067 rad. Finding 8; `results/step_response.md`.

### T25 · Why does Newton blow up on large commands, robot only? (eval only) · before T19
- status: done
- why: T18 (Finding 8) showed the four parameters T19 would fit are already equal, and small commands track within
  ~0.005 rad, yet replaying the PhysX policy's targets with no cube resets 28/64 Newton robots. So the cause is
  something that only shows up under large, fast, all-finger commands. Leading suspect (planning chat): **velocity
  limits**. `abnormal_robot` fires at |v| > 2× the limit (12.6 rad/s for the hand); if PhysX clamps joint velocity at
  the limit (6.28 rad/s) as part of its solver and Newton/MuJoCo doesn't, PhysX can almost never trip it and Newton can.
  Other suspects: effort-limit handling (fingers saturate at 0.5 N·m), the integrator, finger self-collision.
- requires: the GPU job limits above (eval only; may run alongside T22).
- step 1 (no GPU): from `~/runs/step_response/{physx,newton}.npz` (signal c, before any reset) and the T17 traces,
  per engine and per finger joint: max and 99th percentile of |joint_vel| / velocity limit, the fraction of steps at
  0.98–1.02 of the limit (a clamp shows up as flat tops at exactly 1.0), and the fraction of steps where
  |applied_torque| is at the effort limit. Plot |v|/limit over time for the 3 worst joints, both engines on one plot,
  in `results/plots/vel_limit_<joint>.png`.
- step 2 (no GPU): find how Isaac Lab hands velocity and effort limits to each engine, and whether each engine enforces
  them (PhysX articulation joint max velocity; Newton / MuJoCo Warp joint or actuator limits). Quote the relevant lines
  with file:line in `notes/log.md`.
- step 3: rerun T18 signal (c) on both engines with gravity as in the Play config (the policies are evaluated at ADR
  max, where gravity is on), e.g. a `--adr max` option on `scripts/step_response.py`. Record the termination term per
  env this time.
- step 4 (only if step 1 or 2 points at velocity limits): rerun Newton signal (c) with the velocity clamp emulated: after
  every physics step if the API allows a callback, otherwise every control step, clip each joint's velocity to ±its
  limit with `write_joint_velocity_to_sim`. Count resets. Same for an effort-limit idea if step 1 points there.
- on done: `results/blowup_diagnosis.md` (short: the table from step 1, what each engine enforces, step 3 and step 4
  reset counts), "Finding 9" in `notes/log.md`, and under "Needs a human" a proposal for what T19 should fit instead
  (for example an emulated velocity limit, or an effort-limit scale). Don't change T19 yourself.
- result: PhysX caps finger velocity at the limit (max 1.01×), Newton doesn't (max 2.0× no cube). Signal c at ADR max:
  Newton 47/64 `abnormal_robot`, PhysX 0. With the velocity clamp emulated every physics step: 34/64 (only the late
  resets go away). Finding 9; `results/blowup_diagnosis.md`. Newton source check of `joint_velocity_limit` not done (no read access).

### T25b · Where does the one-substep kick come from? (eval only) · before T19
- status: done
- why: T25 (Finding 9) showed a per-substep velocity clamp removes only 13/47 Newton blow-ups; the rest jump past 2×
  the limit within one 1/120 s substep. That is > 1,500 rad/s², far more than a 0.5 N·m drive can give a joint with
  0.01 kg·m² armature (~50 rad/s²), so the kick most likely comes from a **constraint force**, not the drives.
- requires: the GPU job limits above (eval only; may run alongside T22). Use `scripts/step_response.py`, signal (c),
  64 envs, `--adr max`, both engines, with and without `--clamp_vel` where it says so.
- test 1, self-collision: rerun with collisions between the robot's own links (finger–finger, finger–palm) turned off
  in both engines, if Isaac Lab exposes it for each engine (articulation `enabled_self_collisions` or the engine's
  collision filter). Count `abnormal_robot` resets.
- test 2, joint limits: at each Newton reset step, record which joints are within 0.02 rad of their position limits
  (soft or hard), and their velocity. Compare with the same steps in PhysX. If most blow-ups coincide with a joint at
  its limit, that's MuJoCo's soft joint-limit constraint (its solref/solimp).
- test 3, time step: rerun Newton with more substeps (e.g. 4 and 8 instead of 2) at the same control rate, with and
  without `--clamp_vel`. If resets fall sharply, the integrator is too coarse for these links.
- test 4 (no GPU), finish T25 step 2: read the `newton` package source (now readable: the agent may read, never edit,
  files under Isaac Sim's `kit/python`) and quote with file:line whether the MuJoCo Warp solver uses
  `joint_velocity_limit`, how joint limits and their softness are passed (solref/solimp or equivalent), and how
  armature and effort limits reach MuJoCo.
- on done: `results/blowup_diagnosis.md` gets a "T25b" section (a table: test, setting, resets out of 64), "Finding 10"
  in `notes/log.md`, and under "Needs a human" a concrete proposal for T19's parameters (what to fit, with ranges).
  Don't change T19 yourself.
- result: Newton `abnormal_robot` of 64: defaults 47, self-collision off 47, 4/8 substeps 36/37, clamp at 2/4/8
  substeps 34/25/17 (PhysX 0 throughout). Only 4/47 blow-ups have a joint at a position limit. Source: MuJoCo Warp
  ignores `joint_velocity_limit` (`solver_mujoco.py:298-299, 4309-4310`); joint limits use solref (−1e4, −10).
  Finding 10; `results/blowup_diagnosis.md` T25b section, `results/t25b_tests.md`.

### T19 · System-ID: harness (agent), then the fit (by Sara)
- status: running
- Tue 17 Nov 15:38: Sara's `scripts/sysid_fit.py` is written (make_grid, refine_grid, score_candidate,
  choose_best; penalty level fixed from the default run) and running by hand on 1,024 envs (16 candidates per call),
  log `~/runs/sysid_fit.log`. The PhysX reference is now also in the repo: `results/sysid/t19_ref_physx.npz`
  (use it if `~/runs/step_response/` is missing, e.g. on a fresh instance). The agent doesn't touch the fit; when
  `results/sysid_robot.json` appears, report it in STATUS.md and wait for Sara to set T19 `done`.
- rewritten Mon 16 Nov 15:55 from T25b (Finding 10). PhysX is the "real robot"; only Newton changes.
- why: make Newton's robot respond like PhysX's to the policy's fast finger commands, so that a policy trained in
  Newton works in PhysX (T21). T25b: MuJoCo Warp ignores joint velocity limits, and the coarse step lets fingers
  overshoot within one substep. A velocity clamp plus 8 substeps cut robot-only blow-ups from 47/64 to 17/64.
- requires: T25b `done`. GPU limits above.
- **fixed corrections (not fitted), applied in every Newton run from here on:**
  1. velocity limit emulation: clip each finger joint's velocity to ±its limit at every *solver substep* if the
     Newton/Isaac Lab API allows a per-substep hook; otherwise at every physics step (as in T25's `--clamp_vel`).
     Say in `notes/log.md` which one you managed.
  2. `num_substeps`: measure Newton's training speed (s/iteration, Lift 512 envs, 50 iterations, like T5) at 2, 4
     and 8 substeps with the clamp, and pick the smallest that keeps signal-c blow-ups within 2 of the 8-substep count.
     Record the choice and the speed cost in `results/sysid_settings.md`.
- **fitted parameters (one shared set for all 16 finger joints; arm untouched, stiffness untouched):**
  `armature` (0.01–0.1 kg·m²), `damping_scale` (0.5–4 × nominal), `effort_scale` (0.5–2 × the effort limit).
  Optional 4th, only if Sara asks: joint-limit `ke` (1e3–1e5).
- **agent part:** write `scripts/sysid_harness.py` (module + small CLI) that
  1. loads PhysX's recorded trajectories for signals (a), (b), (c) (T18/T25b; re-record at ADR max with gravity if the
     stored ones were at ADR 0, so both engines see the same conditions),
  2. builds a Newton env with N envs (64 or 128), ADR max, the fixed corrections above, cube parked,
  3. provides `rollout(params)`: `params` shape (N, 3), one set per env, applied with the articulation's
     `write_joint_*_to_sim` calls after every reset; replays (a)–(c); returns a dict with `joint_pos`, `joint_vel`
     (N, signal, steps, 23, joints **by name** in PhysX's order), `reset` (N, signal: did it hit abnormal_robot, and
     at which step), and the matching PhysX arrays,
  4. provides `default_params()` and `param_bounds()`,
  5. `--check`: roll out the default params in every env and print, per signal, the RMS joint-position difference
     to PhysX and the number of resets. With the fixed corrections it should be close to T25b's best row.
  Then set this task `blocked` and write "T19 harness ready for Sara" under "Needs a human". Don't write a loss or an
  optimiser.
- **Sara's part (by hand):** `scripts/sysid_fit.py`: her loss (how far Newton's trajectories are from PhysX's, plus a
  penalty for resets) and a **grid search, then a finer grid** over `rollout()` (her design, notes/log.md 16 Nov 18:20;
  replaces CMA-ES: only 3 parameters), each candidate scored on all 64 references (num_envs = 64 × K), capped at 2 h
  of GPU. Outputs `results/sysid_robot.json`
  (best params, loss per generation), `results/plots/sysid_loss.png`, and step-response plots for PhysX, default Newton
  and fitted Newton. Then "Finding 11" in `notes/log.md`. Sara sets T19 `done`.
- result: harness ready (`scripts/sysid_harness.py`). Fixed corrections: per-physics-step finger velocity clamp (the
  substep hook crashed), num_substeps 8 (signal-c abnormal_robot 26/19/16 of 64 at 2/4/8; 1.31 s/iter vs 1.11 at 4),
  see `results/sysid_settings.md`. `--check` at 8: RMS a 0.027, b 0.022, c 0.100 rad, c abnormal_robot 16/64.
  Training wrapper `scripts/train_clamped.py`. Waiting for Sara's fit.

### T20 · Check the fitted robot, then cross-evaluate with it (eval only)
- status: done
- why: fidelity check of the calibrated simulator (PhysX is the "real robot", see Answers from humans 16 Nov 14:05).
  Does a policy that works on the real robot also work in the calibrated Newton, with no retraining? Also run the
  Newton-trained policies in PhysX with nothing changed, as the uncalibrated sim-to-real baseline for T21.
- requires: `results/sysid_robot.json` in the repo (Sara's fit, 17 Nov 15:45: armature 0.0131, damping_scale 1.149,
  effort_scale 1.591 on the 16 finger joints; 0 blow-ups vs 22 with defaults). T19 itself stays `running` until Sara
  sets it `done`; don't wait for that.
- **"fitted Newton" always means all three together:** the per-physics-step finger velocity clamp, `num_substeps` 8,
  and the parameters from `results/sysid_robot.json` (`best`), applied to the finger joints after every reset with the
  same calls as `scripts/sysid_harness.py` (`_apply_params`). Robot randomisation events off is NOT part of it: keep the
  task's events, but re-apply the fitted values after each reset so they win. Check and print the applied values once.
- step 1, sanity checks of the fit (harness only, a few minutes):
  1. step response: with `scripts/sysid_harness.py`, roll out PhysX vs default Newton vs fitted Newton on signal (a);
     per finger joint, rise time (10–90 %) and overshoot. Table in `results/sysid_check.md`, and plots for 3 joints
     (`results/plots/sysid_step_<joint>.png`). Flag it in STATUS.md if fitted overshoot is far below PhysX's (a
     sluggish hand).
  2. held-out episodes: signal (c) is built from the T17 trace episodes. Rerun Sara's grid search
     (`scripts/sysid_fit.py`, unchanged functions) using only references from 10 of the 15 episodes, then count
     blow-ups of that best point on the other 5. Report both in `results/sysid_check.md`. If you need a harness option
     to restrict references, add it without changing the defaults.
- step 2, cross-evaluation: add `--robot_params results/sysid_robot.json` (applies all three, as above) to
  `scripts/evaluate.py`; always `--match_order <train engine>` (T23). 1,024 episodes each:
  - Reorient PhysX policy in fitted Newton; Lift PhysX policy in fitted Newton (the fidelity checks)
  - Newton → Newton with fitted Newton, both tasks (control: does fitting break Newton's own policy?)
  - Newton policies in PhysX, unchanged (baseline for T21; reuse T23's matched-order rows if they're identical setups)
- add the rows to `results/cross_eval.csv` with label `reorient_fitted` / `lift_fitted`, a "Fitted robot" table in
  `results/cross_eval.md`, and "Finding 11" in `notes/log.md` (the fit, the checks, the cross-evaluation). Then T21's gate.
- result: step response barely changed (overshoot PhysX 38.5%, default 44.5%, fitted 44.4%; not sluggish). Held-out:
  the full fit's 0 blow-ups don't reproduce (28 vs default 26 when re-run); fit on 10 episodes → 0 train, 5/20 held-out c.
  PhysX → fitted Newton: Lift 1.0%, Reorient 0.1% (abnormal_robot 88.7% / 70.9%). Newton → fitted Newton: Lift 94.8%
  (vs 86.9%), Reorient 65.6% (vs 63.9%). Newton → PhysX = T23 rows, 0%. `results/sysid_check.md`, `results/cross_eval.md`, Finding 11.

### T26 · How noisy are the blow-up counts? (eval only, ~10 min) · before T21
- status: done (follow-up in T26b: the call effect is most likely ADR demotion)
- why: T20 found the fit's "22 → 0 blow-ups" doesn't reproduce (same params: 28 vs 26 for defaults in another run).
  If blow-up counts vary run to run by more than the gap between candidates, the grid's minimum is mostly luck (the
  winner's curse). Measure the noise before refitting or training on the fit.
- requires: nothing running on the GPU. Harness defaults (fixed corrections, 8 substeps, ADR max), all 64 references.
- candidates (4): default; Sara's full fit (`results/sysid_robot.json` best); the T20 train-episodes best
  (armature 0.0110, damping 1.149, effort 1.149); and one grid point that scored 0 blow-ups in both T19 and T20
  (from `results/sysid_check.json`).
- measure two kinds of noise, with Sara's `score_candidate` unchanged:
  1. **within a call:** one `rollout()` with 1,024 envs where each candidate gets 4 blocks of 64 envs (same params,
     same references, different env indices). Are the 4 blocks identical or not?
  2. **between calls:** repeat that rollout 5 times (5 calls, same params array). Same question across calls.
  Also once: the same candidate in the same env block, two separate calls (is the simulator bit-for-bit deterministic?).
- report in `results/sysid_repeat.md`: per candidate, blow-ups and loss (mean, std, min, max) within a call and between
  calls; whether identical inputs give identical outputs; and a one-paragraph answer: is the difference between the
  candidates bigger than the noise?
- then, if the within-call blocks do vary (so averaging inside one call works): **rerun Sara's fit with averaging**,
  `SYSID_REPEATS=4 SYSID_OUT=<repo>/results/sysid_robot_r4.json scripts/run_isaac.sh sysid_fit_r4 sysid_fit.py --headless
  --num_envs 1024 physics=newton_mjwarp presets=cube` (4 blocks per candidate, scores averaged, `*_std` per row; about
  4× slower, ~25 min). If the blocks are identical, don't rerun: report that only between-call repeats would help and
  write under "Needs a human". Don't edit Sara's four functions.
- on done: "Finding 12" in `notes/log.md`, and the comparison (single-run fit vs averaged fit, if run) in STATUS.md
  for the T21 gate. Don't start T21.
- result: measured, `results/sysid_repeat.md`, Finding 12. The rollout call number dominates: call 1 gives +25–30 blow-ups to every candidate; from call 3 on default 5, full fit 0, T20 best ~5, zero point ~0 (block std ≈ 1; nothing bit-identical). Averaged refit NOT run: the `SYSID_REPEATS=4 ...` env-prefixed command is outside the agent's allowed commands, and it would still score the default in call 1 (see STATUS.md).

### T26b · Freeze ADR at max, then redo the reference, the repeat test and the fit · before T21
- status: todo
- why (planning chat, from T26): the "call-1 effect" is most likely **ADR demotion**. The Play configs start ADR at
  `max_difficulty` (10) but don't set `promotion_only`, so `DifficultyScheduler` lowers the difficulty by 1 on every
  reset of an env that didn't succeed (`mdp/curriculums.py`). With the cube parked nothing ever succeeds, so each
  signal reset (and each blow-up reset) lowers it; within ~2 calls it reaches 0. The difficulty scales
  `variable_gravity` from 0 to −9.81 (`adr_curriculum.py`) and the observation noises. So call 1 ran with gravity
  (≈ −7.3, as T25b saw) and calls ≥ 3 ran with **no gravity**: every grid point of the fit was scored without gravity,
  while the default and the penalty level came from call 1 with gravity. The PhysX reference recorded by
  `step_response.py --adr max` drifted the same way across signals a → b → c.
- requires: nothing on the GPU.
- step 1, verify: in `sysid_harness.py`, `step_response.py` and `sysid_repeat.py`, print at the start of every signal
  the ADR difficulty (mean and min/max over envs; `DifficultyScheduler.current_adr_difficulties` / `difficulty_frac`)
  and the sim gravity. Run `sysid_repeat.py` once as in T26 (2 calls are enough) and confirm the drift and the gravity
  change. Write the numbers in `results/sysid_repeat.md` (new section "ADR drift").
- step 2, freeze: add `--freeze_adr` (default **on** in these three scripts) that sets
  `env_cfg.curriculum.adr.params["promotion_only"] = True` (with init = max, the difficulty then stays at max) and check
  the printed difficulty and gravity stay constant over all signals and calls.
- step 3, redo with ADR frozen at max:
  1. re-record the PhysX reference: `results/sysid/t19_ref_physx_adrmax.npz` (keep the old file; commit the new one)
  2. `sysid_repeat.py` (as T26, 5 calls): is there still a call effect? within/between-call noise?
  3. Sara's fit, unchanged functions, with averaging only if step 3.2 shows noise worth averaging:
     `scripts/run_isaac.sh sysid_fit_adrmax sysid_fit.py --headless --num_envs 1024 --ref <new npz> --out <repo>/results/sysid_robot_adrmax.json [--repeats 4] physics=newton_mjwarp presets=cube`
     (`--repeats` and `--out` are now harness flags, so no env vars are needed)
  4. `sysid_check.py` with the new reference and new fit (step response, held-out episodes).
- step 4, the evaluations: the same demotion happens in `evaluate.py` with the Play config: cells where the policy fails
  (all away cells) drift towards difficulty 0 (no gravity, no noise) during the 1,024 episodes; home cells stay near
  max. Log the mean difficulty at the end of each eval from now on. Add `--freeze_adr` to `evaluate.py` (default **off**,
  so earlier rows stay comparable) and rerun just two cells with it on, Reorient PhysX → fitted Newton (old fit) and
  PhysX → PhysX, to see how much the drift mattered.
- on done: "Finding 13" in `notes/log.md` (the mechanism, the evidence, which earlier results it affects and how),
  and in STATUS.md under "Needs a human": old fit vs ADR-max fit, blow-ups default vs fit with ADR frozen, and the two
  eval cells. Don't start T21.
- result:

### T21 · Gate: stop and ask
- status: blocked
- after T20, write under "Needs a human" in STATUS.md: the T20 numbers, hours and $ used since 15 Nov, and the hours left.
  The planning chat then decides the next runs. The default is now the **sim-to-real run on Lift: train in calibrated
  Newton (512 envs, ~8,000 iterations), then evaluate in PhysX**, compared with the uncalibrated Newton policy in PhysX.
  Teacher–student on Lift and the robustness heatmap come after, budget allowing. Don't start any training before that
  decision.

### T22 · Reward experiment · Lift · PhysX (two variants, 3,000 iterations)
- status: done
- run_folder: check `2026-11-16_12-44-30`; A `2026-11-16_12-45-44` (log `~/runs/lift_physx_3000_noactpen.log`); B `2026-11-16_12-46-44` (log `~/runs/lift_physx_3000_nograsp.log`)
- why: show how rewards shape behaviour (reward design is the RL skill every robot-learning role asks about), and
  test whether a less smooth policy transfers to Newton even worse. This task changes reward weights, but only through
  the exact `--override` lines below.
- requires: the GPU job limits above. May run alongside T17–T19 (it uses the two training slots); start A and B together.
- step 0, check: `scripts/train.sh lift physx 5 --tag check --override env.rewards.action_l2.weight=0`. In the new run
  folder's `params/env.yaml`, `action_l2` must show `weight: 0` (or `0.0`). If it doesn't, set `blocked` with the yaml
  excerpt in STATUS.md, and don't start A or B.
- variant A, no smoothness penalties:
  `scripts/train.sh lift physx 3000 --tag noactpen --override env.rewards.action_l2.weight=0 --override env.rewards.action_rate_l2.weight=0`
- variant B, no grasp rewards:
  `scripts/train.sh lift physx 3000 --tag nograsp --override env.rewards.good_finger_contact.weight=0 --override env.rewards.contact_count.weight=0`
- baseline: T1's `checkpoints/lift_physx/model_3000.pt`, the normal rewards at the same iteration count. No training.
- on done (each variant): back it up as in CLAUDE.md into `checkpoints/lift_physx_<tag>/` and `configs/lift_physx_<tag>/`.
  Then evaluate with `scripts/eval.sh`, 1,024 episodes each: A in PhysX, A in Newton, B in PhysX, and the T1
  `model_3000.pt` baseline in PhysX and in Newton. Record clips with `scripts/record_videos.sh lift physx <run_folder> <final N>`
  for A and B, and `scripts/record_videos.sh lift physx 2026-11-11_11-08-26 3000` for the baseline.
- write `results/reward_experiment.md`: one table (variant, success, abnormal_robot, object_out_of_bound, time_out,
  and the mean |action| and mean |action rate| if the logs give them). Plus "Finding 6" in `notes/log.md`, describing
  what each variant does instead, from the logs. Sara watches the clips and adds her description.
- result: A (`noactpen`, model_2999) training success 0.00 throughout, ADR 0.0002; evals PhysX 0.0%, Newton 0.0% (98.5% abnormal_robot). B (`nograsp`, model_2999) training 0.93, ADR 0.99; PhysX 90.2%. Baseline model_3000: PhysX 7.9%, Newton 0.0%. Clips in `~/runs/videos/lift_physx_{noactpen,nograsp,baseline3000}/`. `results/reward_experiment.md`, Finding 6. Sara's clip description still to add.

## Agent notes

<!-- The server agent adds dated one-line notes here, newest last. -->
- 2026-11-12 10:10 UTC: T3 finished normally (no Traceback); backed up model_14999.pt, configs, final excerpt; set `done`. T4 resumes used: 0/2.
- 2026-11-12 10:49 UTC: T6 smoke tests done; fixed termination counting in evaluate.py (1 fix, see notes/log.md). Stopped T4 at 3,315 by plan, backed up model_3250.pt, set `done`. Started T6 step 2 cell 1 (physx→physx).
- 2026-11-12 10:56 UTC: T6 cells 2–4 started in parallel (new job rule); all four done by 10:54 data timestamps, results written, set `done`. Started T7 command 1 (lift physx videos).
- 2026-11-12 11:13 UTC: T7 commands 1–2 found finished; ran command 3 (Lift Newton resume, model_14999); 11 clips, set `done`. GPU idle, so started T8 (reorient physx 300, 4,096 envs, exclusive); iterating.
- 2026-11-12 11:31 UTC: T8 finished normally (931.65 s); backed up configs + final excerpt (no checkpoint, timing run), wrote `results/reorient_4096_timing.md`, set `done`. Started T12 command 1 (PhysX policy in Newton).
- 2026-11-12 11:36 UTC: T12 both clips recorded (no errors), set `done`. GPU idle, so started T9 (reorient newton 300, 4,096 envs, exclusive); iterating.
- 2026-11-12 11:48 UTC: T9 finished normally (520.61 s); backed up configs + final excerpt (no checkpoint, timing run), added Newton column to `results/reorient_4096_timing.md`, set `done`. T10/T11 left on hold as T9 says. T5 requirements now met (GPU idle), so started T5 command 1 (lift physx 300, folder `2026-11-12_11-46-23`); iterating.
- 2026-11-12 12:00 UTC: T5 command 1 finished normally (594.88 s). Started T5 command 2 (lift newton 300, folder `2026-11-12_11-57-32`); iterating. T10/T11 wait for T5.
- 2026-11-12 22:25 UTC: T5 command 2 found finished normally (325.43 s); wrote `results/speed_benchmark.md`, set T5 `done`. Started T10 (folder `2026-11-12_22-18-09`) and T11 (folder `2026-11-12_22-19-43`), both iterating. Resumes used: T10 0/2, T11 0/2.
- 2026-11-13 14:14 UTC: T11 finished normally at 15,000 (57,142 s, 0 resumes); backed up model_14999.pt, configs, final excerpt; set `done`. T10 continues alone (check #7 +10.8 pp); T13 waits for T10.
- 2026-11-13 20:10 UTC: T10 finished normally at 15,000 (78,164 s, 0 resumes); backed up model_14999.pt, configs, final excerpt; set `done`. Started T13, all four Reorient cross-eval cells in parallel.
- 2026-11-15 15:45 UTC: T14 cmd 2 (Newton, 4 clips) and T15 cmd 1 (PhysX→Newton clip) finished without errors; started T15 cmd 2 (Newton policy in PhysX). T14 cmd 1 still recording.
- 2026-11-15 15:45 UTC: T13: all four rows were already in `cross_eval.csv` (no reruns); wrote results/cross_eval.md Reorient section, Finding 3, README; set `done`. Started T14 commands 1 and 2 and T15 command 1 (3 video jobs).
- 2026-11-15 15:50 UTC: T14 cmd 1 (PhysX, 4 clips) and T15 cmd 2 (Newton→PhysX clip) finished without errors; wrote Reorient sections in `results/videos.md`; set T14 and T15 `done`. No `todo` tasks left; GPU idle.
- 2026-11-16 13:08 UTC: T22 step 0 passed (after fixing train.sh's override pattern to allow digits); started A (`noactpen`) and B (`nograsp`). T17 done: traces, diagnosis, plots; found that PhysX and Newton order the hand joints differently. T18 not started yet (next wake-up). Resumes used: T22 A 0/2, B 0/2.
- 2026-11-16 13:12 UTC: T23 started: steps 1–3 done (`scripts/dump_order.py`, `results/joint_order.json`, `evaluate.py --match_order`, smoke test passed the name check). Started the 4 Reorient `reorient_matched` cells; the 4 Lift cells come next. T22 A/B training, ~iter 320/3000.
- 2026-11-16 13:22 UTC: T23 done: all 8 matched cells finished (no errors); cross-engine cells still ~0%, controls match T6/T13. Wrote cross_eval.md table, Finding 7, README line. T18 not started (out of time this wake-up).
- 2026-11-16 13:55 UTC: T18 done: wrote `scripts/step_response.py` + `scripts/analyze_step_response.py` (1 fix: signal-a env→joint map differs by name between engines), smoke tests passed, ran 64 envs on both engines. Small signals match; open-loop policy replay blows up 28/64 Newton envs with no cube (Finding 8). T19 left for next wake-up so the planning chat can see Finding 8 first.
- 2026-11-16 14:51 UTC: T25 done: committed step 1 (left uncommitted by an earlier wake-up), step 2 code read (PhysX side only), added `--adr max`, `--signals`, `--clamp_vel` and per-env termination terms to `step_response.py`, smoke-tested, ran signal c at ADR max on both engines and the clamped Newton run. Finding 9. T22 A/B still training (0/2 resumes each).
- 2026-11-16 15:50 UTC: T25b done: added `--no_self_collision`, `--num_substeps`, and pre-reset/per-physics-step recording to `step_response.py`, plus `scripts/t25b_analysis.py`; smoke test, then 8 signal-c runs (≤ 4 at a time), and read the newton source. Finding 10. T19 proposal in STATUS.md. T22 A/B still training.
- 2026-11-16 16:20 UTC: T19 started: recorded PhysX reference a+b+c at ADR max (`~/runs/step_response/t19_ref_physx.npz`), wrote `scripts/sysid_harness.py` (clamp once per solver substep via a wrapped `NewtonManager._step_solver`), 8-env smoke check launched, not yet verified. T22 A/B still training (0/2 resumes each).
- 2026-11-16 16:35 UTC: T22 B finished normally (model_2999, 0 resumes), backed up; evals started: B in PhysX (running), T1 baseline in Newton (done, 0.0%). T19: per-substep clamp smoke failed again after a fix (keep the pre-clamp graph alive), so 2/2 attempts used; `--no_clamp` smoke passes. Next: the per-physics-step fallback from T19 step 1.
- 2026-11-16 16:31 UTC: T22 B-in-PhysX eval done (90.2%); started the baseline `model_3000.pt` in PhysX eval. T19: switched `sysid_harness.py` to the per-physics-step clamp (PLAN fallback); 8-env smoke passed (c: 1/8 abnormal_robot vs 3/8 unclamped); started the 64-env `--check`.
- 2026-11-16 17:00 UTC: T22 A finished normally (0 resumes), backed up (by the previous wake-up, committed now); evals A PhysX/Newton 0.0%; recorded the 3 clips (with `--out` names); wrote `results/reward_experiment.md` + Finding 6; T22 `done`. T19: 64-env checks at 8/4/2 substeps, wrote `scripts/train_clamped.py` (smoke OK), speed runs 2/4/8; chose 8 substeps (`results/sysid_settings.md`); T19 `blocked` for Sara's fit.
- 2026-11-17 15:56 UTC: T20 started: wrote `scripts/sysid_check.py` (step 1: step response + held-out grid search, Sara's functions imported unchanged), `evaluate.py --robot_params` and `eval.sh ... <match> fitted`; both smoke tests passed (applied values checked). Running: `sysid_check` (1,024 envs) and 3 fitted evals (Reorient P→N, Lift P→N, Reorient N→N); Lift N→N next. Newton→PhysX unchanged reuses T23's matched rows (identical setup).
- 2026-11-17 16:03 UTC: T20 done: sysid_check and all 4 fitted evals finished without errors; wrote `results/sysid_check.md`, cross_eval.md "Fitted robot", Finding 11. T21 gate reported in STATUS.md (T21 stays `blocked`).
- 2026-11-17 16:48 UTC: T26 measured: wrote `scripts/sysid_repeat.py`, smoke (512 envs) + full run (1,024 envs, 5 calls), `results/sysid_repeat.md`, Finding 12. Averaged refit not started (env-var command not allowed for the agent; call-1 effect needs a decision); T26 `blocked`.
