"""Train with RSL-RL in Newton with T19's fixed corrections: finger velocity clamp + chosen num_substeps.

A thin wrapper around Isaac Lab's `scripts/reinforcement_learning/rsl_rl/train_rsl_rl.py` (what
`./isaaclab.sh train --rl_library rsl_rl` runs). It changes nothing else: before the env is created it sets
`env_cfg.sim.physics.num_substeps`, and after, it wraps the action term's `apply_actions` (called once per physics
step) so that, after the normal joint targets are set, the 16 finger joint velocities are clipped to ±their velocity
limits. This is the same per-physics-step clamp as `sysid_harness.py --clamp_mode physics_step` (T19 fallback).

Usage (always through run_isaac.sh):
  scripts/run_isaac.sh <log> train_clamped.py --num_substeps 4 --task Isaac-Dexsuite-Kuka-Allegro-Lift-v0 \
      --headless --num_envs 512 physics=newton_mjwarp presets=cube --seed 42 agent.max_iterations=50
Own options (removed before the rest goes to train_rsl_rl.py): --num_substeps N (default 8), --no_clamp.
"""

import sys
from pathlib import Path

ISAACLAB_DIR = Path("/workspace/isaaclab")
RL_ROOT = ISAACLAB_DIR / "scripts" / "reinforcement_learning"


def _pop_args(argv):
    num_substeps, clamp, rest = 8, True, []
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
        else:
            rest.append(argv[i])
        i += 1
    return num_substeps, clamp, rest


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


def main():
    num_substeps, clamp, rest = _pop_args(sys.argv[1:])
    sys.path.insert(0, str(RL_ROOT))
    from common import import_local_module  # noqa: E402  (Isaac Lab's scripts/reinforcement_learning/common.py)

    mod = import_local_module("isaaclab_rl_train_rsl_rl", RL_ROOT / "rsl_rl" / "train_rsl_rl.py")
    orig_create = mod.create_isaaclab_env

    def create_with_corrections(task, env_cfg, args_cli, **kw):
        assert hasattr(env_cfg.sim.physics, "num_substeps"), f"Newton only: {type(env_cfg.sim.physics)}"
        env_cfg.sim.physics.num_substeps = num_substeps
        print(f"[CLAMP] num_substeps={num_substeps}, clamp={clamp}")
        env = orig_create(task, env_cfg, args_cli, **kw)
        if clamp:
            install_step_clamp(env)
        return env

    mod.create_isaaclab_env = create_with_corrections
    mod.run(rest)


if __name__ == "__main__":
    main()
