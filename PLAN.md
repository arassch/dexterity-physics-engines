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
  or these defaults unless a task here says so.
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
- status: running
- command: `scripts/train.sh reorient physx`
- started: Wed 11 Nov 23:21, log `~/runs/reorient_physx_full.log`
- run_folder:
- result:

### T4 · Reorient · Newton
- status: running
- command: `scripts/train.sh reorient newton`
- started: Thu 12 Nov ~09:35, log `~/runs/reorient_newton_full.log`. If there is no such process and no such log,
  it was never started: start it.
- run_folder:
- result:

### T5 · Speed benchmark (exclusive)
- status: todo
- requires: T3 and T4 not `running`, and no other GPU job running (exclusive)
- commands, one after the other, each alone on the GPU:
  1. `scripts/train.sh lift physx 300`
  2. `scripts/train.sh lift newton 300`
- on done: write `results/speed_benchmark.md` with, for each engine, the median "Iteration time", "Steps per second",
  "Collection time" and "Learning time" over iterations 100–299, plus GPU name. No checkpoints to back up.
- run_folder:
- result:

### T6 · Cross-evaluation · Lift 2×2
- status: blocked
- blocked on: `scripts/evaluate.py`, being written in the planning chat

### T7 · Record training-progress videos · Lift
- status: blocked
- blocked on: confirming the play/video command for this Isaac Lab version

## Agent notes

<!-- The server agent adds dated one-line notes here, newest last. -->
