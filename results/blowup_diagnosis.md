# T25: why does Newton blow up on large commands, robot only?

PhysX is the reference ("real robot"). Signal (c) is the T18 open-loop replay of the PhysX Reorient policy's joint
targets with no cube (`scripts/step_response.py`), 64 envs, 120 control steps. Joints are compared by name.

## Step 1: |joint_vel| / velocity limit (details in `results/blowup_step1.md`)

The limits are the same in both engines: arm 10 rad/s, fingers 6.283 rad/s. `abnormal_robot` fires above 2.0.

| source | engine | finger max | finger p99 (worst joint) | finger frac > 1.02 | finger frac at effort limit |
|---|---|---|---|---|---|
| T18 signal c (no cube, ADR 0) | PhysX | 1.01 | 1.00 | 0.0000 | n/a |
| T18 signal c (no cube, ADR 0) | Newton | 2.00 | 1.34 | 0.0104 | n/a |
| T17 policy trace | PhysX | 1.38 | 1.00 | 0.0003 | 0.495 |
| T17 policy trace | Newton | 22.61 | 2.06 | 0.0290 | 0.332 |

With no cube, PhysX finger velocities are capped at exactly the limit: they have flat tops at 1.00–1.01, and none
of 7,680 samples is above 1.02. Newton goes past the same limit. Effort saturation is *more* common in PhysX, so the
data doesn't point at effort-limit handling.

## Step 2: what each engine gets

- PhysX: Isaac Lab writes the limit into the engine as the articulation's max joint velocity,
  `isaaclab_physx/assets/articulation/articulation.py:1578` (`root_view.set_dof_max_velocities(...)`).
- Newton: the same number is bound to the model attribute `joint_velocity_limit`
  (`isaaclab_newton/assets/articulation/articulation_data.py:1497`). Isaac Lab itself only uses it to check that the
  default velocities are within it (`articulation.py:3950`). Whether the MuJoCo Warp solver reads it is **not
  checked**: the `newton` package is in Isaac Sim's site-packages, which the agent can't read. The data says it
  doesn't clamp.

## Step 3: signal (c) with gravity on (ADR max, Play config)

At ADR max, `variable_gravity` sets g_z ≈ −7.2 to −7.4 m/s² (logged per run), not −9.81. Termination terms were
recorded per env.

| engine | envs reset (of 64) | first-reset term | first-reset steps |
|---|---|---|---|
| PhysX | 3 | `object_out_of_bound` ×3, `abnormal_robot` 0 | 100, 103, 117 |
| Newton | **47** | `abnormal_robot` ×47 | 13–40 (most at 13–24) |

With gravity on, Newton is worse than in T18 at ADR 0 (28/64). The 3 PhysX resets are the parked cube, not the
robot: with gravity on it falls out of the bounds box.

## Step 4: Newton with the velocity limit emulated

Before every `sim.step` call (Newton doesn't handle decimation here, so this is every physics substep, 2 per control
step), each joint's velocity is clipped to ±its limit with `write_joint_velocity_to_sim_index` (`--clamp_vel`).
Over 240 calls, 3,776 joint-samples were clipped.

| Newton signal (c), ADR max | envs reset (of 64) | first-reset steps |
|---|---|---|
| no clamp | 47 | 13–40 |
| velocity clamped every physics step | **34** | 13–21 (the same envs and steps as without the clamp) |

The clamp removes only the later resets (steps 22–40). In the other 34 envs, the velocity goes from at most the limit
to more than 2× the limit **within one physics substep** (1/120 s), after the clamp. So the missing velocity limit
explains part of the gap, not all of it. Something inside one Newton substep gives the fingers a large impulse.
Candidates, none tested yet: a joint position-limit constraint (MuJoCo's soft limit), finger–finger
self-collision contacts, or the drive's implicit integration at these gains.
