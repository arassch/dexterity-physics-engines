# Plan

This file is the contract between the planning chat and the server agent.

- **Humans own this file** (Sara, and Claude in the planning chat). To change direction, edit it and push.
- **The server agent may only:** change a task's `status`, fill in `run_folder` and `result`, and add dated lines under
  "Agent notes" at the bottom. It never adds, removes or rewrites tasks or rules.
- Statuses: `todo` (start when its requirements are met) · `running` · `done` · `blocked` (needs a human; don't start) ·
  `hold` (deliberately paused; don't start) · `failed` (gave up after the crash policy; needs a human).

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
- the server agent does nothing for T16.
- result:

### T17 · Why does `abnormal_robot` fire? (eval only)
- status: todo
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
- result:

### T18 · Robot-only step-response test (eval only, no policy)
- status: todo
- why: this is our "real-world dataset". Treat PhysX as reality and record how each joint responds to the same command
  in both engines, with no cube involved.
- requires: T17 `done`. About 30 min of GPU.
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
- result:

### T19 · Fit Newton's robot parameters to PhysX (eval only)
- status: todo
- why: system identification. Find joint parameters that make Newton's robot track like PhysX's.
- requires: T18 `done`. About 2 h of GPU at most; stop at 2 h even if not converged and report.
- parameters, per joint group (arm 7, each finger 4 joints, thumb 4): a scale on PD stiffness, a scale on PD damping,
  armature, and joint friction. That's 4 × 5 = 20 numbers. Set them through the articulation's `write_joint_*_to_sim`
  calls, not by editing configs.
- method: CMA-ES (`scripts/pip_install.sh cma`; if it fails, write it under "Needs a human"). Each Newton env runs one
  candidate, so one generation is one parallel rollout of signals (a)–(c). The loss is the RMS joint-position difference
  against the PhysX recording from T18. Population size: the number of envs (64 or 128). Log the best loss for each
  generation.
- write `scripts/sysid_robot.py`. Output `results/sysid_robot.json` (best parameters, loss per generation) and
  `results/plots/sysid_loss.png`, plus two step-response plots that put PhysX, default Newton and fitted Newton on one plot.
- add "Finding 4" to `notes/log.md`: how much of the PhysX–Newton difference the fit removes (loss before vs after, per
  signal), and which parameters moved most.
- result:

### T20 · Cross-evaluate with the fitted robot (eval only)
- status: todo
- why: the headline test. Does the PhysX policy work in Newton once Newton's robot matches PhysX, with no retraining?
- requires: T19 `done`.
- add a `--robot_params results/sysid_robot.json` option to `scripts/evaluate.py` that applies the fitted parameters after
  reset (the same calls as T19). Don't change anything it measures.
- run 1,024 episodes each: Reorient PhysX policy in fitted Newton, Lift PhysX policy in fitted Newton, and Newton → Newton
  with fitted parameters (a control: does fitting break Newton's own policy?).
- add the rows to `results/cross_eval.csv` with label `reorient_fitted` / `lift_fitted`, a "Fitted robot" table in
  `results/cross_eval.md`, and "Finding 5" in `notes/log.md`.
- result:

### T21 · Gate: stop and ask
- status: blocked
- after T20, write under "Needs a human" in STATUS.md: the T20 numbers, hours and $ used since 15 Nov, and the hours left.
  The planning chat then decides the training runs (retraining Newton with fitted parameters, a robustness heatmap, or
  teacher–student). Don't start any training before that.

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
