"""Train with RSL-RL in Newton with T19's fixed corrections: finger velocity clamp + chosen num_substeps.

A thin wrapper around Isaac Lab's `scripts/reinforcement_learning/rsl_rl/train_rsl_rl.py` (what
`./isaaclab.sh train --rl_library rsl_rl` runs). It changes nothing else: before the env is created it sets
`env_cfg.sim.physics.num_substeps`, and after, it wraps the action term's `apply_actions` (called once per physics
step) so that, after the normal joint targets are set, the 16 finger joint velocities are clipped to ±their velocity
limits. This is the same per-physics-step clamp as `sysid_harness.py --clamp_mode physics_step` (T19 fallback).

Usage (always through run_isaac.sh):
  scripts/run_isaac.sh <log> train_clamped.py --num_substeps 4 --task Isaac-Dexsuite-Kuka-Allegro-Lift-v0 \
      --headless --num_envs 512 physics=newton_mjwarp presets=cube --seed 42 agent.max_iterations=50
Own options (removed before the rest goes to train_rsl_rl.py): --num_substeps N (default 8), --no_clamp,
--finger_dr (T21: per-env finger armature / damping scale / effort scale, log-uniform, resampled on every reset).
"""

import sys
from pathlib import Path

ISAACLAB_DIR = Path("/workspace/isaaclab")
RL_ROOT = ISAACLAB_DIR / "scripts" / "reinforcement_learning"


def _pop_args(argv):
    num_substeps, clamp, finger_dr, rest = 8, True, False, []
    i = 0
    while i < len(argv):
        if argv[i] == "--num_substeps":
            num_substeps = int(argv[i + 1])
            i += 2
            continue
        if argv[i].startswith("--num_substeps="):
            num_substeps = int(argv[i].split("=", 1)[1])
        elif argv[i] == "--no_clamp":
            clamp = False
        elif argv[i] == "--finger_dr":
            finger_dr = True
        else:
            rest.append(argv[i])
        i += 1
    return num_substeps, clamp, finger_dr, rest


# T21 finger domain randomisation: (low, high), sampled log-uniform per env on every reset.
# Armature is absolute (nominal 0.01); damping and effort are scales of the per-env nominal values.
FINGER_DR = {"armature": (0.01, 0.05), "damping_scale": (0.75, 2.0), "effort_scale": (1.0, 2.0)}


def _t(x):
    return x.torch if hasattr(x, "torch") else x


def install_step_clamp(env):
    import torch

    u = env.unwrapped
    robot = u.scene["robot"]
    names = list(robot.joint_names)
    finger_ids = [i for i, nm in enumerate(names) if not nm.startswith("iiwa7")]
    assert len(finger_ids) == 16, names
    fmask = torch.zeros(len(names), dtype=torch.bool, device=u.device)
    fmask[finger_ids] = True
    vlim = _t(robot.data.joint_vel_limits).clone().float()
    term = u.action_manager.get_term(u.action_manager.active_terms[0])
    orig_apply = term.apply_actions

    def apply_and_clamp():
        orig_apply()
        v = _t(robot.data.joint_vel).clone().float()
        robot.write_joint_velocity_to_sim_index(velocity=torch.where(fmask, torch.clamp(v, -vlim, vlim), v))

    term.apply_actions = apply_and_clamp
    print(f"[CLAMP] per-physics-step velocity clamp on {len(finger_ids)} finger joints x {u.num_envs} envs "
          f"(action term '{u.action_manager.active_terms[0]}', decimation {u.cfg.decimation}); "
          f"finger vel limit mean {float(vlim[:, finger_ids].mean()):.3f} rad/s")


def install_finger_dr(env):
    """On every reset of an env, sample (armature, damping scale, effort scale) for that env, shared by its 16 finger
    joints, and write them with the same calls as sysid_harness.py `_apply_params` (plus env_ids)."""
    import math

    import torch

    u = env.unwrapped
    robot = u.scene["robot"]
    dev = u.device
    f = [i for i, nm in enumerate(robot.joint_names) if not nm.startswith("iiwa7")]
    assert len(f) == 16, robot.joint_names
    # Nominal values after the task's startup events (same as sysid_harness.py: per env, per finger joint).
    nom_damping = _t(robot.data.joint_damping).clone().float()[:, f]
    nom_effort = _t(robot.data.joint_effort_limits).clone().float()[:, f]
    nom_arm = _t(robot.data.joint_armature).clone().float()[:, f]
    lo = torch.tensor([math.log(FINGER_DR[k][0]) for k in FINGER_DR], device=dev)
    hi = torch.tensor([math.log(FINGER_DR[k][1]) for k in FINGER_DR], device=dev)
    cur = torch.zeros(u.num_envs, 3, device=dev)  # current sampled params per env
    ncalls = [0]

    def apply(env_ids):
        ids = torch.as_tensor(env_ids, device=dev, dtype=torch.long).reshape(-1)
        if ids.numel() == 0:
            return
        p = torch.exp(lo + (hi - lo) * torch.rand(ids.numel(), 3, device=dev))
        cur[ids] = p
        robot.write_joint_armature_to_sim_index(
            armature=p[:, 0:1].expand(-1, len(f)).contiguous(), joint_ids=f, env_ids=ids)
        robot.write_joint_damping_to_sim_index(
            damping=(nom_damping[ids] * p[:, 1:2]).contiguous(), joint_ids=f, env_ids=ids)
        robot.write_joint_effort_limit_to_sim_index(
            limits=(nom_effort[ids] * p[:, 2:3]).contiguous(), joint_ids=f, env_ids=ids)
        ncalls[0] += 1
        n = ncalls[0]
        if n <= 3 or n % 2000 == 0:
            # Read back what is in the sim data and compare with the ranges.
            arm = _t(robot.data.joint_armature).float()[:, f]
            dsc = _t(robot.data.joint_damping).float()[:, f] / nom_damping.clamp_min(1e-9)
            esc = _t(robot.data.joint_effort_limits).float()[:, f] / nom_effort.clamp_min(1e-9)
            msg = []
            for name, v in (("armature", arm), ("damping_scale", dsc), ("effort_scale", esc)):
                a, b = FINGER_DR[name]
                inside = bool(((v >= a * 0.999) & (v <= b * 1.001)).all())
                msg.append(f"{name} min {float(v.min()):.4f} max {float(v.max()):.4f} "
                           f"std-across-envs {float(v[:, 0].std()):.4f} inside={inside}")
            print(f"[FINGER_DR] reset call {n} ({ids.numel()} envs) read back: " + "; ".join(msg), flush=True)

    orig_reset_idx = u._reset_idx

    def reset_idx_with_dr(env_ids):
        orig_reset_idx(env_ids)
        apply(env_ids)

    u._reset_idx = reset_idx_with_dr
    apply(torch.arange(u.num_envs, device=dev))  # all envs once, before training starts
    print(f"[FINGER_DR] per-env log-uniform finger params on every reset: armature {FINGER_DR['armature']}, "
          f"damping_scale {FINGER_DR['damping_scale']}, effort_scale {FINGER_DR['effort_scale']}; "
          f"nominal armature mean {float(nom_arm.mean()):.4f}, damping mean {float(nom_damping.mean()):.4f}, "
          f"effort mean {float(nom_effort.mean()):.4f}; {u.num_envs} envs", flush=True)


def main():
    num_substeps, clamp, finger_dr, rest = _pop_args(sys.argv[1:])
    sys.path.insert(0, str(RL_ROOT))
    from common import import_local_module  # noqa: E402  (Isaac Lab's scripts/reinforcement_learning/common.py)

    mod = import_local_module("isaaclab_rl_train_rsl_rl", RL_ROOT / "rsl_rl" / "train_rsl_rl.py")
    orig_create = mod.create_isaaclab_env

    def create_with_corrections(task, env_cfg, args_cli, **kw):
        assert hasattr(env_cfg.sim.physics, "num_substeps"), f"Newton only: {type(env_cfg.sim.physics)}"
        env_cfg.sim.physics.num_substeps = num_substeps
        print(f"[CLAMP] num_substeps={num_substeps}, clamp={clamp}, finger_dr={finger_dr}")
        env = orig_create(task, env_cfg, args_cli, **kw)
        if clamp:
            install_step_clamp(env)
        if finger_dr:
            install_finger_dr(env)
        return env

    mod.create_isaaclab_env = create_with_corrections
    mod.run(rest)


if __name__ == "__main__":
    main()
