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

## T25b: where does the kick come from?

Same signal (c), 64 envs, 120 control steps, `--adr max`, no cube. New options in `scripts/step_response.py`:
`--no_self_collision`, `--num_substeps N`, and two new recordings: the joint state at the moment terminations are
computed (before the auto-reset overwrites it), and the state before every physics step. Tables and per-blow-up
rows: `results/t25b_tests.md` (from `scripts/t25b_analysis.py`). Logs: `~/runs/t25b_*.log`, data
`~/runs/step_response/t25b_*.npz`.

**Caveat on counts:** the 64 envs replay only **15 distinct** trace episodes (env e = env e+15 = …), so the counts
move in blocks of about 4. A difference of 4 envs is one trajectory.

| test | setting | envs reset (of 64) | `abnormal_robot` | first-reset steps (abnormal) |
|---|---|---|---|---|
| baseline | PhysX, defaults | 3 | 0 | – (3 × parked cube out of bounds) |
| baseline | Newton, defaults (2 solver substeps) | 47 | 47 | 13–40 (same as T25) |
| 1 self-collision | PhysX, self-collision off | 3 | 0 | – |
| 1 self-collision | Newton, self-collision off | 47 | 47 | 13–40 |
| 3 time step | Newton, 4 substeps | 40 | 36 | 13–40 |
| 3 time step | Newton, 8 substeps | 44 | 37 | 13–40 |
| 3 time step | Newton, 2 substeps + vel clamp (T25) | 34 | 34 | 13–21 |
| 3 time step | Newton, 4 substeps + vel clamp | 30 | 25 | 13–22 |
| 3 time step | Newton, 8 substeps + vel clamp | 25 | **17** | 16–21 |

With more substeps, Newton also has 4–8 `object_out_of_bound` resets (the parked cube falling, as in PhysX).
The clamp runs once per `sim.step` (1/120 s) in every row, not once per solver substep.

**Test 1, self-collision: no effect.** Newton still resets 47/64, with almost the same steps (one block 24 → 26).
The setting did reach Newton: the trajectories changed (max |pos − target| at the end 0.90 → 2.97). The PhysX result is
bit-identical (2.0457), so either PhysX has no finger self-contacts on this signal, or the setting didn't reach it.
Either way, self-collision isn't the source of the Newton kick.

**Test 2, joint limits: mostly not at a limit.** At the reset step, a joint above 2× its velocity limit (a "culprit")
was within 0.02 rad of its hard or soft limit in **4/47** blow-ups (all `ring_joint_1`, which sits at its limit
in PhysX too, with v = 0). One physics step earlier: **0/47**. Most culprits are 0.1–0.9 rad from either limit. For
comparison, 72% of Newton env-steps (92% in PhysX) have *some* finger joint within 0.02 rad of a limit, so being
near a limit is common and doesn't single out the blow-ups. Culprits: `index_joint_2` ×29, `index_joint_0` ×17,
`index_joint_3` ×17, `middle_joint_0` ×9, then ring/thumb joints. The index finger dominates. Also, in 6 of the 11
distinct trajectories that blow up, at least one culprit was **already above 2×** one physics step (1/120 s) before the check
(e.g. `index_joint_2` 7.8× the limit). `abnormal_robot` only samples once per control step, so "within one substep"
in T25 should be read as "within one control step".

**Test 3, time step: helps a bit alone, more with the clamp.** 4 or 8 substeps alone remove ~10 of 47 resets (≈ 2–3
trajectories), and 8 is no better than 4. Combined with the velocity clamp the count goes 34 → 25 → 17. So the
missing velocity limit and the integration step interact. The clamp works better when each 1/120 s step is split
into finer solver steps. At 8 substeps + clamp, 17 envs (about 4 trajectories) still blow up at steps 16–21.

**Test 4, the `newton` source** (`/isaac-sim/kit/python/lib/python3.12/site-packages/newton/_src/solvers/mujoco/solver_mujoco.py`;
read only):
- Velocity limit: **not used.** The class docstring says `joint_velocity_limit` and `joint_enabled` "are not supported"
  (`:298-299`). Where the MuJoCo model is built, the read is commented out: `# MoJoCo doesn't have velocity limit` /
  `# joint_velocity_limit = model.joint_velocity_limit.numpy()` (`:4309-4310`).
- Joint limits (revolute, `:5126-5138`): `range` = (`joint_limit_lower`, `joint_limit_upper`) in degrees, `limited`
  unless both are infinite. Softness: `solref_limit = (-joint_limit_ke, -joint_limit_kd)` when `ke > 0` (MuJoCo's
  negative convention means direct stiffness and damping, `:5134-5136`). `solimp_limit` and `margin` are set only if the
  USD has the custom `mjc:solimplimit` / `limit_margin` attributes (`:5118-5119`, `:5137-5138`). Measured in our model:
  `joint_limit_ke` = 1e4 and `joint_limit_kd` = 10 for every hand/arm joint, which are Newton's builder defaults
  (`newton/_src/sim/builder.py:452-453`). So the hand's limits use stiffness 1e4 N·m/rad and damping 10 N·m·s/rad.
- Armature: passed straight through as the MuJoCo joint `armature` (`:5112`).
- Effort limit: `actfrclimited=True`, `actfrcrange = ±joint_effort_limit` (`:5143-5146`), the joint-level clamp on the
  *summed* actuator force (P + D). The position actuator is `gainprm=[kp]`, `biasprm=[0, -kp, -kd]` (`:4976-4978`).

**Summary:** not self-collision, and not joint limits in most cases. The blow-ups shrink with a finer time step plus
the emulated velocity limit (47 → 17), so they come mostly from integrating fast finger motion without a velocity
cap. A residual of ~4 trajectories (index finger, steps 16–21) is still unexplained.
