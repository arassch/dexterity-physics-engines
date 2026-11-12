# Project: does a dexterous policy survive a change of physics?

Portfolio project. We train Isaac Lab's DexSuite tasks (Kuka arm + Allegro hand: Lift, Reorient) with PPO on two physics
engines, **PhysX** and **Newton** (MuJoCo Warp), then cross-evaluate each policy in the other engine.
Read `README.md` for the story, `PLAN.md` for what to do, `RUNS.md` for every run, `notes/log.md` for findings so far.

## If you are the server agent

You run on the Brev GPU instance, woken by `scripts/agent_watch.sh`. Your job is in `scripts/agent_prompt.md`.
**`PLAN.md` decides what you do.** Never start work that isn't a task there. If something is unclear, don't guess:
write the question under "Needs a human" in `STATUS.md` and leave the task alone.

## The machine

- NVIDIA Brev "Isaac Launchable", AWS `g6e.4xlarge`, 1× L40S (48 GB), us-east-1. Costs **$3.65/hr while running**.
- You are inside the VS Code container as a non-root user: no `sudo`, no `apt`, no `tmux`. `$HOME` is `/root`.
- Isaac Lab: `/workspace/isaaclab` (version 3.0.0; exact package versions in `setup/ENVIRONMENT.md`).
- Run outputs: `/workspace/isaaclab/logs/rsl_rl/dexsuite_kuka_allegro/<start-time>/` with `model_<N>.pt` every 250
  iterations and `params/env.yaml`, `params/agent.yaml`. Lift and Reorient runs share this parent folder.
- Training logs (stdout): `~/runs/<name>.log`. `scripts/train.sh` names them `<task>_<engine>_<iters>[_resume].log`;
  older runs used names like `lift_physx_full.log` (see RUNS.md).
- `scripts/idle_stop.sh` may be running: it stops the instance after 20 idle minutes with no training. Leave it alone.

## How to do things

- **Start a training run:** `scripts/train.sh <lift|reorient> <physx|newton> [iterations]` from the repo root.
  It runs in the background with `nohup` and returns immediately.
- **Resume after a crash:** `scripts/train.sh <task> <engine> <remaining_iters> --resume <run_folder> <model_N.pt>`.
  On resume, iterations are *additional*: use 15000 minus the checkpoint's iteration number. A resume writes to a
  **new** run folder.
- **Find a run's folder:** the log prints `log_dir: ...`; or `grep -l` the task name in
  `.../<folder>/params/env.yaml`; or match start times. Never pick "the first folder that contains physx": the
  300-iteration runs also match.
- **Is it running?** `pgrep -af "reinforcement_learning/train.py"` lists runs with their full command line.
- **Progress:** `scripts/check_progress.sh <log>`. Iteration blocks contain `Learning iteration N/M`,
  `Metrics/success_rate`, `Episode_Termination/abnormal_robot`, `Curriculum/adr`, `Iteration time`.
- **Crash signatures** at the end of a log: `ValueError: The observation group 'proprio' ... contains NaN values`
  (simulation divergence), `CUDA out of memory`, any `Traceback`, then `[ERROR] Command failed`.
- **Stop a run:** `scripts/stop_run.sh <pid>`. It only stops Isaac Lab training processes.

## Backing up a finished training run

Repo size matters (checkpoints are ~25 MB each). For each finished run:
1. Copy only the **final** checkpoint to `checkpoints/<task>_<engine>/` (milestones stay on the server).
2. Copy `params/env.yaml` and `params/agent.yaml` to `configs/<task>_<engine>/`.
3. Save the last 60 log lines to `results/log_excerpts/<task>_<engine>_final.txt`. For a crash, also save the last
   120 lines to `results/log_excerpts/<task>_<engine>_crash_<n>.txt`.
4. Record final metrics (success rate, abnormal_robot, ADR, mean reward, iteration time) in `RUNS.md`, the README
   training table, and a dated entry in `notes/log.md`.
Never commit a file over 50 MB, anything under `logs/`, or full training logs.

## Git

- Always `git pull --rebase` before you start changing files, and again right before `git push`.
- Small, descriptive commits. Never force-push, never rewrite history, never `git reset --hard`.
- The planning chat also pushes to `main`. If a rebase conflicts in a file you didn't mean to change, keep their
  version and redo your change.

## Writing findings

Write numbers you measured, not impressions. Training-time success rates include exploration noise; say so.
If something surprises you (a crash, a big gap between engines, a metric moving the wrong way), add it to
`notes/log.md` with the numbers and log lines that show it, and mention it in `STATUS.md`.

## Never

- Run `brev`, `sudo`, `rm`, `curl`/`wget`, or anything that creates, stops or deletes cloud resources.
- Change reward functions, environment configs, or the training defaults in `PLAN.md`.
- Run more GPU jobs than `PLAN.md` allows.
- Rewrite tasks or rules in `PLAN.md`.
