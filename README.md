# Does a dexterous policy survive a change of physics?

**Status: work in progress. Lift trained on both engines; Reorient training; cross-evaluation next.**

A policy that only works in one physics solver has learned the solver, not the task.
This project trains a dexterous manipulation policy (a Kuka arm with a four-finger Allegro hand)
in NVIDIA Isaac Lab on two physics engines, **PhysX** and **Newton** (MuJoCo Warp solver),
then runs each policy in the *other* engine to measure how much of what it learned is just the contact model.
Switching engines is a cheap, entirely virtual stand-in for the sim-to-real gap.

<!-- media/preview.gif goes here once recorded -->

## The task

Isaac Lab's **DexSuite** environments, on a Kuka arm with an Allegro hand:

| Task | ID | Goal |
|---|---|---|
| Lift | `Isaac-Dexsuite-Kuka-Allegro-Lift-v0` | Pick a cube off the table and hold it at a sampled target position |
| Reorient | `Isaac-Dexsuite-Kuka-Allegro-Reorient-v0` | Pick it up and also rotate it to a target orientation |

- **Observations:** robot joint state, object state, target, with a 5-step history (no cameras: `state` observations)
- **Actions:** joint position targets for 7 arm joints and 16 finger joints, tracked by PD controllers
- **Timing (identical on both engines):** physics at 120 Hz, policy at 60 Hz (decimation 2), 6 s episodes
- **Learning:** PPO (RSL-RL), 512 parallel environments
- **Object:** a single cube (`presets=cube`) on **both** engines. Newton doesn't support the multi-shape spawning the default uses, so the cube keeps the comparison fair.

## Plan

| Part | What | Output |
|---|---|---|
| 1 | Train Lift, then Reorient, on PhysX | Baseline policies, checkpoints, training-progress clips |
| 2 | Retrain on Newton (`physics=newton_mjwarp`) | Speed vs success trade-off |
| 3 | Cross-evaluate: each policy in the other engine | The 2×2 success-rate table |
| 4 | Robustness: sweep friction, mass, ADR on vs off; classify failures | Heatmap and failure analysis |

## Results

### Training (Parts 1–2)

Final training metrics, with exploration noise on (deterministic evaluation comes in Part 3):

| Task | Engine | Success rate | `abnormal_robot` terminations | ADR level | NaN crashes |
|---|---|---|---|---|---|
| Lift | PhysX | ~93–98% | ~2% | 0.99 | 0 |
| Lift | Newton | ~86% | ~14% | 0.98 | 1 (resumed from iteration 10,000) |
| Reorient | PhysX | ~4% | ~1% | 0.005 | 0 |
| Reorient | Newton | 0% (stopped at iteration 3,315 by plan) | ~10% | 0.0 | 0 |

**Finding so far:** at the same curriculum difficulty, Newton ends ~7× more episodes with the robot in an
abnormal state, and diverged to NaN once. Configs differ only in the solver block (see [`notes/log.md`](notes/log.md)).

### Cross-evaluation (Part 3)

| Success rate | Run in PhysX | Run in Newton |
|---|---|---|
| Trained in PhysX | **95.9%** (94.5–97.0) | **0.0%** (0.0–0.4) · 98% `abnormal_robot` |
| Trained in Newton | **0.0%** (0.0–0.4) · 23% `abnormal_robot`, 66% time-out | **87.0%** (84.9–88.9) |

Lift, final checkpoints (`model_14999.pt`), ~1,024 episodes per cell, 256 envs, deterministic policy (no exploration
noise), Play config (ADR at max difficulty), seed 42. Brackets: 95% Wilson interval. Details in
[`results/cross_eval.md`](results/cross_eval.md).

### Training cost (measured)

| Run | Engine | Envs | Time per iteration | Iterations | Wall clock | GPU |
|---|---|---|---|---|---|---|
| Lift timing run | PhysX | 512 | ~2.0 s | 300 | 10 min | 1× L40S |
| Lift full run | PhysX | 512 | ~2.15 s (alone) | 15,000 | ~11.5 h (GPU shared from 13:06) | 1× L40S |
| Lift full run | Newton | 512 | ~2.1 s (shared) | 15,000 | ~6 h + resume after NaN crash | 1× L40S |

Speed figures from shared-GPU runs aren't a fair engine comparison; isolated benchmark runs are planned.

## Reproducing

See [`setup/ENVIRONMENT.md`](setup/ENVIRONMENT.md) for the exact software versions and cloud setup,
[`RUNS.md`](RUNS.md) for every training run and its exact command, and [`scripts/`](scripts/) for the scripts.

## How this project is run

Planning happens in a chat with Claude; the plan lives in [`PLAN.md`](PLAN.md). A Claude Code agent on the GPU
instance follows it: it starts the next runs, resumes crashed ones, backs up results and reports in
[`STATUS.md`](STATUS.md). Setup in [`setup/ENVIRONMENT.md`](setup/ENVIRONMENT.md#server-agent-claude-code-on-the-instance).

## Working notes

[`notes/log.md`](notes/log.md) is a dated log of what was tried, what broke and what was learned.
