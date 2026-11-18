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

Older answers are in `PLAN_done.md`.

## Tasks

Finished tasks are in `PLAN_done.md` (full text and results). Read a task there only when an open task
refers to it. Index:

- T1 · Lift · PhysX baseline: done
- T2 · Lift · Newton: done
- T3 · Reorient · PhysX baseline: done
- T4 · Reorient · Newton (512 envs): done
- T5 · Speed benchmark (exclusive): done
- T6 · Cross-evaluation · Lift 2×2: done
- T7 · Record training-progress videos · Lift: done
- T12 · Transfer clips · Lift (policy in the other engine): done
- T8 · Reorient timing run · PhysX · 4,096 envs (exclusive): done
- T9 · Reorient timing run · Newton · 4,096 envs (exclusive): done
- T10 · Reorient · PhysX · 4,096 envs (full run): done
- T11 · Reorient · Newton · 4,096 envs (full run): done
- T13 · Cross-evaluation · Reorient 2×2: done
- T14 · Record training-progress videos · Reorient: done
- T15 · Transfer clips · Reorient (policy in the other engine): done
- T17 · Why does `abnormal_robot` fire? (eval only): done
- T23 · Cross-evaluate with joints matched by name (eval only) · before T18: done
- T18 · Robot-only step-response test (eval only, no policy): done
- T25 · Why does Newton blow up on large commands, robot only? (eval only) · before T19: done
- T25b · Where does the one-substep kick come from? (eval only) · before T19: done
- T20 · Check the fitted robot, then cross-evaluate with it (eval only): done
- T26 · How noisy are the blow-up counts? (eval only, ~10 min) · before T21: done
- T22 · Reward experiment · Lift · PhysX (two variants, 3,000 iterations): done

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

### T19 · System-ID: harness (agent), then the fit (by Sara)
- status: running (Sara sets it `done`; the agent doesn't touch the fit)
- harness done (`scripts/sysid_harness.py`, fixed corrections: per-physics-step finger velocity clamp, `num_substeps`
  8, see `results/sysid_settings.md`). Sara's fit done (`scripts/sysid_fit.py`, `results/sysid_robot.json`), but it
  was scored mostly with ADR drifted to 0 (no gravity): T26b redoes it with ADR frozen at max. Full original text of
  this task is in `PLAN_done.md`.
- the fit's parameters (one shared set for the 16 finger joints): `armature` (0.01–0.1), `damping_scale` (0.5–4),
  `effort_scale` (0.5–2). Flags: `--ref <npz>`, `--out <json>`, `--repeats N`.

### T26b · Freeze ADR at max, then redo the reference, the repeat test and the fit · before T21
- status: running
- model: opus
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

## Agent notes

Older notes are in `PLAN_done.md`.

- 2026-11-16 16:31 UTC: T22 B-in-PhysX eval done (90.2%); started the baseline `model_3000.pt` in PhysX eval. T19: switched `sysid_harness.py` to the per-physics-step clamp (PLAN fallback); 8-env smoke passed (c: 1/8 abnormal_robot vs 3/8 unclamped); started the 64-env `--check`.
- 2026-11-16 17:00 UTC: T22 A finished normally (0 resumes), backed up (by the previous wake-up, committed now); evals A PhysX/Newton 0.0%; recorded the 3 clips (with `--out` names); wrote `results/reward_experiment.md` + Finding 6; T22 `done`. T19: 64-env checks at 8/4/2 substeps, wrote `scripts/train_clamped.py` (smoke OK), speed runs 2/4/8; chose 8 substeps (`results/sysid_settings.md`); T19 `blocked` for Sara's fit.
- 2026-11-17 15:56 UTC: T20 started: wrote `scripts/sysid_check.py` (step 1: step response + held-out grid search, Sara's functions imported unchanged), `evaluate.py --robot_params` and `eval.sh ... <match> fitted`; both smoke tests passed (applied values checked). Running: `sysid_check` (1,024 envs) and 3 fitted evals (Reorient P→N, Lift P→N, Reorient N→N); Lift N→N next. Newton→PhysX unchanged reuses T23's matched rows (identical setup).
- 2026-11-17 16:03 UTC: T20 done: sysid_check and all 4 fitted evals finished without errors; wrote `results/sysid_check.md`, cross_eval.md "Fitted robot", Finding 11. T21 gate reported in STATUS.md (T21 stays `blocked`).
- 2026-11-17 16:48 UTC: T26 measured: wrote `scripts/sysid_repeat.py`, smoke (512 envs) + full run (1,024 envs, 5 calls), `results/sysid_repeat.md`, Finding 12. Averaged refit not started (env-var command not allowed for the agent; call-1 effect needs a decision); T26 `blocked`.
- 2026-11-18 10:45 UTC: T26b steps 1, 2, 3.1, 3.2 and 4 were already committed (51e3ea1). Started step 3.3: `sysid_fit.py --repeats 4` with ADR frozen (`sysid_fit_adrmax2`; the first launch failed on a relative `--ref` path).
