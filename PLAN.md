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

- 2026-11-18 17:05 (Sara, planning chat): T21a/T21b never lifted, so change course. Stop T21b now (pid 19261, check
  with `ps` first), back up its last milestone checkpoint like a crash (`checkpoints/lift_newton_corr_dr/`, configs,
  last 60 log lines), and don't evaluate T21a or T21b: policies that never lift say nothing about transfer. Then run
  T21 step 2b below (corrected Newton **without the two grasp rewards**, as T22 B did in PhysX). That reward change is
  Sara's decision and applies only to step 2b.

- 2026-11-18 14:05 (planning chat): yes, run T21a and T21b to 8,000 regardless. 0.00 success at 3,700 is normal
  for Lift in Newton: the original run (T2) was also at 0 at 3,250 and reached 0.40 by 4,500 (notes/archive.md,
  T4 table). Mention in Finding 14 where each run's success first rises above 0.

- 2026-11-18 11:45 (planning chat): T21's shared run folder: take option 2 now. `scripts/stop_run.sh` accepts
  `scripts/train_clamped.py` from this commit on. Stop T21b (python pid 14025, check it with `ps` first) and restart
  it with the same command plus `--run_name corr_dr`, log `~/runs/lift_newton_corr_dr_8000_r2.log`. T21a keeps the
  folder `2026-11-18_11-24-37`; its checkpoints from the next milestone on are its own. From now on, whenever two
  training runs start together, give each a distinct `--run_name` and start them at least a minute apart.

- 2026-11-18 11:21 (Sara): T21 = option 1, sim-to-real on Lift with randomised finger parameters (and a
  no-randomisation control). The T26b ADR-max fit is not used: it fixes blow-ups by making the hand sluggish.

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
- status: done
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
- result: drift confirmed (ADR 10 → 8 → 2.5 by call 2, signal c; gravity −7.85 → −2.44); frozen: 10 / −9.81 throughout.
  Repeat test (frozen): no call effect, block std ≈ 4–5; default 62.6, old fit 54.5 blow-ups/64. ADR-max fit
  (`results/sysid_robot_adrmax.json`): armature 0.0923, damping ×0.545, effort ×1.206, 34.5 ± 6.0 vs default 65.5 ± 5.9
  blow-ups, but loss 1.24 vs 0.65; check: rise 0.199 s vs PhysX 0.086 s, overshoot 90 % vs 39 %, held-out blow-ups 16
  vs 18. Evals frozen vs drifting: P→fitted N 0.29 % vs 0.10 %, P→P 51.0 % vs 51.5 %. Finding 13.

### T21 · Sim-to-real on Lift: train in corrected Newton, with and without randomised fingers, deploy in PhysX
- status: running
- run_folder: T21a `2026-11-18_11-24-37` (log `~/runs/lift_newton_corr_8000.log`); T21b `2026-11-18_11-46-21_corr_dr` (restarted, log `~/runs/lift_newton_corr_dr_8000_r2.log`; see RUNS.md #16–18); T21c `2026-11-18_17-04-21_corr_nograsp` (log `~/runs/lift_newton_corr_nograsp_3000.log`); T21d `2026-11-18_17-05-09_corr_dr_nograsp` (log `~/runs/lift_newton_corr_dr_nograsp_3000.log`)
- model: opus
- decided Wed 18 Nov 11:21 (Sara, option 1 after T26b). PhysX is the "real robot". T26b showed three shared finger
  parameters can't make Newton's hand behave like PhysX's (the best blow-up count comes with a sluggish hand), so
  instead of trusting one fitted point we **randomise** the finger parameters during training (domain randomisation),
  the standard approach when system identification can't pin the parameters down.
- requires: nothing else on the GPU. The two training runs may run at the same time (the 2-run limit).
- step 1, code (in `scripts/train_clamped.py`, no change to rewards or the task config): add `--finger_dr` that, on every
  reset of an env, samples one armature, damping scale and effort scale **per env** (shared by its 16 finger joints)
  and writes them with the same calls as `sysid_harness.py` (`_apply_params`): armature log-uniform 0.01–0.05,
  damping_scale log-uniform 0.75–2.0, effort_scale log-uniform 1.0–2.0 (all relative to the nominal values; the
  defaults 0.01 / 1 / 1 are inside, the sluggish T26b point is not). Print the sampled ranges once, and check on a
  5-iteration smoke run that the written values vary across envs and stay inside the ranges.
- step 2, train (Lift, 512 envs, seed 42, `presets=cube`, **8,000 iterations**, Newton, the fixed corrections: clamp
  + `--num_substeps 8`; normal training ADR, not frozen):
  - **T21a**: corrected Newton, no randomisation (`train_clamped.py ... --num_substeps 8`)
  - **T21b**: corrected Newton + `--finger_dr`
  Start both together (about 1.3 s/iteration alone at 8 substeps, so roughly 3–5 h side by side). Same crash policy
  and backups as other training runs (`checkpoints/lift_newton_corr/`, `checkpoints/lift_newton_corr_dr/`).
- **result of step 2** (Wed 18 Nov): T21a 0.00 training success at every checkpoint to 8,000 (touches the cube, never
  lifts); T21b 0.00 at ~5,000, stopped by Sara's 17:05 decision. Not evaluated.
- **step 2b**, train again without the grasp rewards (Sara, 17:05). Same setup as step 2 (Lift, 512 envs, seed 42,
  `presets=cube`, Newton, clamp + `--num_substeps 8`, normal ADR) but **3,000 iterations** and the two T22 B overrides
  `env.rewards.good_finger_contact.weight=0 env.rewards.contact_count.weight=0` appended to the command:
  - **T21c**: `scripts/run_isaac.sh lift_newton_corr_nograsp_3000 train_clamped.py --num_substeps 8 --task
    Isaac-Dexsuite-Kuka-Allegro-Lift-v0 --headless --num_envs 512 physics=newton_mjwarp presets=cube --seed 42
    agent.max_iterations=3000 --run_name corr_nograsp env.rewards.good_finger_contact.weight=0
    env.rewards.contact_count.weight=0`
  - **T21d**: the same plus `--finger_dr`, `--run_name corr_dr_nograsp`, log `lift_newton_corr_dr_nograsp_3000`.
  Start T21d at least a minute after T21c. Smoke-check first (5 iterations, 64 envs, both overrides): the log's
  reward table must show those two terms at weight 0 or missing; if an override is rejected, stop and ask. Before
  starting, check in the log of each run that the two weights really are 0. Backups to
  `checkpoints/lift_newton_corr_nograsp/` and `checkpoints/lift_newton_corr_dr_nograsp/`. Then steps 3–4 on **T21c and
  T21d** instead of T21a/T21b (skip a run that ends with 0.00 training success, and say so).
- step 3, evaluate the final checkpoints, 1,024 episodes each, `--match_order newton`, `--freeze_adr` on (and the same
  for the comparison row):
  - each policy **in PhysX** (the sim-to-real number), and in its own training setup (corrected Newton, with
    `--finger_dr` for T21b) as the "home" number;
  - the comparison: the original Newton Lift policy (`checkpoints/lift_newton/model_14999.pt`) in PhysX with
    `--freeze_adr` (today 0% with drifting ADR).
  Label `lift_sim2real` in `results/cross_eval.csv`, a "Sim-to-real (Lift)" table in `results/cross_eval.md`.
- step 4: clips with `scripts/record_videos.sh` of T21c and T21d in PhysX (final checkpoint), for the video.
- on done: "Finding 14" in `notes/log.md` (T21a/b: 0 success at 2k / 4k / 8k and why we changed course; T21c/d: success at 1k / 2k / 3k, abnormal_robot; the PhysX numbers),
  the README's results section, and under "Needs a human" the table. Then stop: no further training without a decision.
- result:

## Agent notes

Older notes are in `PLAN_done.md`.

- 2026-11-16 16:31 UTC: T22 B-in-PhysX eval done (90.2%); started the baseline `model_3000.pt` in PhysX eval. T19: switched `sysid_harness.py` to the per-physics-step clamp (PLAN fallback); 8-env smoke passed (c: 1/8 abnormal_robot vs 3/8 unclamped); started the 64-env `--check`.
- 2026-11-16 17:00 UTC: T22 A finished normally (0 resumes), backed up (by the previous wake-up, committed now); evals A PhysX/Newton 0.0%; recorded the 3 clips (with `--out` names); wrote `results/reward_experiment.md` + Finding 6; T22 `done`. T19: 64-env checks at 8/4/2 substeps, wrote `scripts/train_clamped.py` (smoke OK), speed runs 2/4/8; chose 8 substeps (`results/sysid_settings.md`); T19 `blocked` for Sara's fit.
- 2026-11-17 15:56 UTC: T20 started: wrote `scripts/sysid_check.py` (step 1: step response + held-out grid search, Sara's functions imported unchanged), `evaluate.py --robot_params` and `eval.sh ... <match> fitted`; both smoke tests passed (applied values checked). Running: `sysid_check` (1,024 envs) and 3 fitted evals (Reorient P→N, Lift P→N, Reorient N→N); Lift N→N next. Newton→PhysX unchanged reuses T23's matched rows (identical setup).
- 2026-11-17 16:03 UTC: T20 done: sysid_check and all 4 fitted evals finished without errors; wrote `results/sysid_check.md`, cross_eval.md "Fitted robot", Finding 11. T21 gate reported in STATUS.md (T21 stays `blocked`).
- 2026-11-17 16:48 UTC: T26 measured: wrote `scripts/sysid_repeat.py`, smoke (512 envs) + full run (1,024 envs, 5 calls), `results/sysid_repeat.md`, Finding 12. Averaged refit not started (env-var command not allowed for the agent; call-1 effect needs a decision); T26 `blocked`.
- 2026-11-18 10:45 UTC: T26b steps 1, 2, 3.1, 3.2 and 4 were already committed (51e3ea1). Started step 3.3: `sysid_fit.py --repeats 4` with ADR frozen (`sysid_fit_adrmax2`; the first launch failed on a relative `--ref` path).
- 2026-11-18 10:58 UTC: T26b done: fit finished (`results/sysid_robot_adrmax.json`), ran `sysid_check.py --tag adrmax` (`results/sysid_check_adrmax.md`), Finding 13. T21 not started.
- 2026-11-18 11:24 UTC: T21 step 1: added `--finger_dr` to `train_clamped.py`; 64-env 5-iteration smoke run passed (`~/runs/t21_smoke_dr.log`: values read back vary across envs, all inside the ranges). Step 2: started T21a and T21b (8,000 its). They share run folder `2026-11-18_11-24-37` (same start second); `stop_run.sh` refuses `train_clamped.py`, so I couldn't restart one. 0 resumes so far.
- 2026-11-18 11:46 UTC: per the 11:45 answer, stopped T21b (pid 14025, at iter 368) and restarted it with `--run_name corr_dr` (folder `2026-11-18_11-46-21_corr_dr`, log `lift_newton_corr_dr_8000_r2.log`); learning iterations confirmed. T21a untouched. 0 resumes for both.
- 2026-11-18 16:58 UTC: T21a finished normally at 8,000 (success 0.00 throughout, 0 resumes); backed up to `checkpoints/lift_newton_corr/model_7999.pt` + configs + log excerpt. T21b still running (~4,970/8,000, 0 resumes). Evals wait for T21b.
- 2026-11-18 17:10 UTC: per the 17:05 answer, stopped T21b (pid 19261, at iter 5,134, success 0.00); backed up `checkpoints/lift_newton_corr_dr/model_5000.pt` + configs + last 60 log lines. Step 2b: smoke (64 envs, 5 its, `~/runs/t21c_smoke.log`) shows both grasp weights 0; started T21c (17:04) and T21d (17:05, `--finger_dr`), both logs show weight 0 and learning iterations. 0 resumes each.
- 2026-11-18 19:05 UTC: T21c finished normally at 3,000 (training success 0.90, ADR 0.98, abnormal_robot 0.077, 0 resumes); backed up `checkpoints/lift_newton_corr_nograsp/model_2999.pt` + configs + last 60 log lines. T21d still running (~2,095/3,000, 0 resumes). Step 3 evals wait for T21d.
- 2026-11-18 19:58 UTC: T21d finished normally at 3,000 (training success 0.92, 0 resumes); backed up `checkpoints/lift_newton_corr_dr_nograsp/model_2999.pt` + configs + log excerpt. Step 3: added `--label/--tag` to `eval.sh` (smoke OK); PhysX cells T21c / T21d / original Newton Lift all 0.0% (`lift_sim2real`). Home cells not run (no corrected-Newton eval option yet). Step 4: started the two PhysX clips.
