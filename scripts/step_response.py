# Copyright (c) 2022-2026, The Isaac Lab Project Developers. SPDX-License-Identifier: BSD-3-Clause (env loading)
"""Robot-only step-response test (T18): the same open-loop joint position targets in either physics engine.

No policy. Reorient Play env, `presets=cube`, ADR difficulty forced to 0 (no observation noise, gravity term at its
ADR-0 value), and the startup events that randomise the *robot* (actuator gains, joint friction, robot material) are
switched off so the robot parameters are the nominal ones. The cube is moved out of reach (see OBJECT_PARK) after each
reset. The action term's apply_actions is replaced so the articulation gets exactly our absolute joint targets.

Signals (120 control steps each, robot reset to its default pose with zero velocity before each one):
  a  step: env i steps joint (i % 23) by +STEP rad (−STEP if + would leave the soft limits); other joints held.
  b  sine: all 16 finger joints, default + 0.2 sin(2π·1Hz·t); arm held.
  c  replay: the joint targets from T17's physx→physx trace (~/runs/traces/reorient_physx_in_physx.npz), mapped by
     joint *name*, as offsets from that trace's first recorded joint positions, added to the default pose.
All targets are clipped to the soft joint limits.

Saved (one .npz per engine), arrays in THIS engine's joint order, plus `joint_names` to compare by name:
  <sig>_joint_pos, <sig>_joint_vel, <sig>_target        (steps, envs, joints)
  <sig>_reset                                          (steps, envs) 1 if the env reset during the signal (invalid)
  a_joint (envs,) joint index stepped, a_sign (envs,), default_joint_pos, soft_joint_pos_limits, joint_vel_limits,
  stiffness, damping, armature, friction (envs, joints) as read from robot.data, gravity, step_dt.

Run: scripts/run_isaac.sh step_response_physx step_response.py --headless --out ~/runs/step_response/physx.npz \
         physics=physx presets=cube
"""

import argparse
import contextlib
import os
import sys

import gymnasium as gym
import numpy as np
import torch

from isaaclab.envs import ManagerBasedRLEnvCfg

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import add_launcher_args, launch_simulation, setup_preset_cli
from isaaclab_tasks.utils.hydra import hydra_task_config

with contextlib.suppress(ImportError):
    import isaaclab_tasks_experimental  # noqa: F401

TASK = "Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0"
OBJECT_PARK = (0.3, 1.5, 1.5)  # env-local; inside object_out_of_bound's box, > 1.5 m from the robot base
ROBOT_RANDOMISATION_EVENTS = ("joint_stiffness_and_damping", "joint_friction", "robot_physics_material")

parser = argparse.ArgumentParser(description="Open-loop joint step responses, no policy.")
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--steps", type=int, default=120)
parser.add_argument("--step_size", type=float, default=0.3)
parser.add_argument("--sine_amp", type=float, default=0.2)
parser.add_argument("--sine_hz", type=float, default=1.0)
parser.add_argument("--trace", type=str, default=os.path.expanduser("~/runs/traces/reorient_physx_in_physx.npz"))
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--out", type=str, required=True)
add_launcher_args(parser)
args_cli, remaining_args = setup_preset_cli(parser)
sys.argv = [sys.argv[0]] + remaining_args
PRESET_ARGS = " ".join(remaining_args)


def _t(x) -> torch.Tensor:
    return x.torch if hasattr(x, "torch") else x


def _np(x) -> np.ndarray:
    return _t(x).detach().float().cpu().numpy().copy()


@hydra_task_config(TASK, "rsl_rl_cfg_entry_point")
def main(env_cfg: ManagerBasedRLEnvCfg, agent_cfg):
    with launch_simulation(env_cfg, args_cli):
        env_cfg.scene.num_envs = args_cli.num_envs
        env_cfg.seed = args_cli.seed
        env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
        env_cfg.curriculum.adr.params["init_difficulty"] = 0
        for name in ROBOT_RANDOMISATION_EVENTS:
            setattr(env_cfg.events, name, None)
        print(f"[STEP] ADR init_difficulty=0; disabled events {ROBOT_RANDOMISATION_EVENTS}; presets: {PRESET_ARGS}")

        env = gym.make(TASK, cfg=env_cfg, render_mode=None)
        u = env.unwrapped
        robot = u.scene["robot"]
        obj = u.scene["object"]
        term = u.action_manager.get_term(u.action_manager.active_terms[0])
        dev = u.device
        n, nj, T = args_cli.num_envs, robot.num_joints, args_cli.steps
        names = list(robot.joint_names)
        jids = term._joint_ids
        assert nj == 23, nj

        target = torch.zeros(n, nj, device=dev)

        def apply_fixed_target():
            robot.set_joint_position_target_index(target=target[:, jids] if not isinstance(jids, slice) else target,
                                                  joint_ids=jids)

        term.apply_actions = apply_fixed_target
        zero_action = torch.zeros(n, u.action_manager.total_action_dim, device=dev)

        u.reset()
        default = _t(robot.data.default_joint_pos).clone().float()
        lim = _t(robot.data.soft_joint_pos_limits).clone().float()
        lo, hi = lim[..., 0], lim[..., 1]

        def reset_all():
            u.reset()
            robot.write_joint_position_to_sim_index(position=default.clone())
            robot.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(default))
            pose = torch.cat([_t(obj.data.root_pos_w).clone(), _t(obj.data.root_quat_w).clone()], dim=-1)
            pose[:, :3] = u.scene.env_origins + torch.tensor(OBJECT_PARK, device=dev)
            obj.write_root_pose_to_sim_index(root_pose=pose)
            obj.write_root_velocity_to_sim_index(root_velocity=torch.zeros(n, 6, device=dev))

        def run(signal_fn, tag):
            reset_all()
            rec = {"joint_pos": [], "joint_vel": [], "target": [], "reset": []}
            for k in range(T):
                target[:] = torch.clamp(signal_fn(k), lo, hi)
                _, _, terminated, truncated, _ = u.step(zero_action)
                rec["joint_pos"].append(_np(robot.data.joint_pos))
                rec["joint_vel"].append(_np(robot.data.joint_vel))
                rec["target"].append(target.cpu().numpy().copy())
                rec["reset"].append((terminated | truncated).float().cpu().numpy())
            out = {f"{tag}_{k}": np.stack(v) for k, v in rec.items()}
            out[f"{tag}_reset"] = np.maximum.accumulate(out[f"{tag}_reset"], axis=0)  # invalid from first reset on
            bad = int((out[f"{tag}_reset"][-1] > 0).sum())
            err = np.abs(out[f"{tag}_joint_pos"][-1] - out[f"{tag}_target"][-1]).max()
            print(f"[STEP] signal {tag}: {T} steps, envs reset during signal: {bad}/{n}, max |pos-target| at end {err:.4f}")
            return out

        # (a) one joint per env
        a_joint = torch.arange(n, device=dev) % nj
        rows = torch.arange(n, device=dev)
        up = default[rows, a_joint] + args_cli.step_size <= hi[rows, a_joint]
        a_sign = torch.where(up, 1.0, -1.0)
        a_target = default.clone()
        a_target[rows, a_joint] += a_sign * args_cli.step_size
        res = run(lambda k: a_target, "a")

        # (b) finger sine
        finger = torch.tensor([not nm.startswith("iiwa7") for nm in names], device=dev)
        dt = u.step_dt

        def sine(k):
            s = args_cli.sine_amp * np.sin(2 * np.pi * args_cli.sine_hz * (k + 1) * dt)
            return default + s * finger.float()

        res.update(run(sine, "b"))

        # (c) replay T17 physx->physx targets, by joint name
        tr = np.load(args_cli.trace)
        tr_names = list(tr["joint_names"])
        perm = [tr_names.index(nm) for nm in names]
        fd = tr["first_done_step"]
        tr_T = tr["joint_pos_target"].shape[0]
        ok = np.where((fd < 0) | (fd >= T))[0]
        assert tr_T >= T and len(ok) > 0, (tr_T, fd)
        src = ok[np.arange(n) % len(ok)]
        tgt = tr["joint_pos_target"][:T][:, src][:, :, perm]  # (T, n, nj) this engine's order
        q0 = tr["joint_pos"][0][src][:, perm]
        c_targets = torch.tensor(tgt - q0[None], device=dev, dtype=torch.float32) + default[None]
        res.update(run(lambda k: c_targets[k], "c"))
        res["c_trace_env"] = src

        res["a_joint"] = a_joint.cpu().numpy()
        res["a_sign"] = a_sign.cpu().numpy()
        res["joint_names"] = np.array(names)
        res["default_joint_pos"] = default.cpu().numpy()
        res["soft_joint_pos_limits"] = lim.cpu().numpy()
        res["joint_vel_limits"] = _np(robot.data.joint_vel_limits)
        for attr in ("joint_stiffness", "joint_damping", "joint_armature", "joint_friction_coeff"):
            with contextlib.suppress(Exception):
                res[attr] = _np(getattr(robot.data, attr))
        with contextlib.suppress(Exception):
            res["gravity"] = np.array(u.sim.cfg.gravity)
        res["step_dt"] = np.array(dt)
        res["presets"] = np.array(PRESET_ARGS)
        os.makedirs(os.path.dirname(os.path.abspath(args_cli.out)), exist_ok=True)
        np.savez_compressed(args_cli.out, **res)
        print(f"[STEP] saved {args_cli.out}; keys: {sorted(res)}")
        env.close()


if __name__ == "__main__":
    main()
