# Replaying the simulations in Unreal

Isaac Lab runs the policy; we record the motion and replay it in Unreal Engine. No physics runs in Unreal: it shows
exactly what PhysX or Newton did.

## 1. Record on the server (`scripts/export_episode.sh`)

Each export plays a checkpoint for 720 control steps (12 s, two episodes) in 4 environments and writes
`~/runs/exports/<task>_<train>_in_<play>.json`. PhysX playback also writes `<same>.usd`, the flattened scene (robot,
cube, table, ground) with all its meshes. About 1–2 minutes each, alone or alongside other jobs.

```
cd ~/dexterity-physics-engines
scripts/export_episode.sh reorient physx  physx  checkpoints/reorient_physx_4096/model_14999.pt    # home, + scene
scripts/export_episode.sh reorient newton newton checkpoints/reorient_newton_4096/model_14999.pt   # home
scripts/export_episode.sh reorient physx  newton checkpoints/reorient_physx_4096/model_14999.pt    # transfer fail
scripts/export_episode.sh reorient newton physx  checkpoints/reorient_newton_4096/model_14999.pt   # transfer fail
```

### Recording format (JSON)

- `meta`: `joint_names` (23: 7 `iiwa7_joint_*`, 16 Allegro), `body_names`, `control_dt` (1/60 s), `env_origins`,
  units (metres, Z up, right-handed), quaternion order **qx qy qz qw** (Isaac Lab 3), and `usd` (scene file and the
  prim path of every body) for PhysX playback.
- `frames[t].envs[i]`: `joint_pos`, `body_pos`/`body_quat` (env-local), `object_pos`/`object_quat`,
  `goal_pos`/`goal_quat`, `pos_err` (m), `rot_err` (rad), and `episode_end` (termination names) on the step an episode
  ended. The next frame is the reset.

## 2a. Quick playback: USD Stage (`scripts/make_usd_animation.py`)

Runs on your own computer: `pip install usd-core`, then

```
python3 make_usd_animation.py reorient_physx_in_physx.json reorient_physx_in_physx.usd reorient_physx_in_physx_anim.usda --env 0
# a Newton playback has no scene of its own: borrow the PhysX one
python3 make_usd_animation.py reorient_newton_in_newton.json reorient_physx_in_physx.usd reorient_newton_anim.usda \
    --usd_from reorient_physx_in_physx.json --env 0
```

Keep the `.usda` next to the `.usd` it sublayers. In Unreal: enable the **USD Importer** plugin, add a **USD Stage**
actor, set its Root Layer to the `.usda`, and play the stage's Level Sequence (60 fps). Each robot link is animated as
a rigid transform; a translucent green cube marks the target. Tested on a synthetic scene only so far; the first real
run will show whether every link prim was matched (the export log prints `matched N/M body prims`).

## 2b. Portfolio version: Control Rig (planned)

Import the Kuka + Allegro as a skeletal mesh, then drive its 23 joints from `joint_pos` with a Control Rig in
Sequencer, and the cube/target from their poses. Unreal is left-handed with centimetres: x_ue = 100·x, y_ue = −100·y,
z_ue = 100·z, and quaternions (qx, −qy, qz, −qw).
