# Does a dexterous policy survive a change of physics?

**Status: work in progress (Part 1 of 4: PhysX baseline training).**

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

### Cross-evaluation (Part 3)

| Success rate | Run in PhysX | Run in Newton |
|---|---|---|
| Trained in PhysX | _tbd_ | _tbd_ |
| Trained in Newton | _tbd_ | _tbd_ |

### Training cost (measured)

| Run | Engine | Envs | Time per iteration | Iterations | Wall clock | GPU |
|---|---|---|---|---|---|---|
| Lift timing run | PhysX | 512 | ~2.0 s | 300 | 10 min | 1× L40S |
| Lift full run | PhysX | 512 | _tbd_ | 15,000 | _tbd_ (~8.3 h expected) | 1× L40S |

## Reproducing

See [`setup/ENVIRONMENT.md`](setup/ENVIRONMENT.md) for the exact software versions and cloud setup,
and [`scripts/`](scripts/) for every command that was run.

## Working notes

[`notes/log.md`](notes/log.md) is a dated log of what was tried, what broke and what was learned.
