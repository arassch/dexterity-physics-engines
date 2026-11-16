# Adapted from scripts/evaluate.py (itself from Isaac Lab 3.0.0 play_rsl_rl.py)
# Copyright (c) 2022-2026, The Isaac Lab Project Developers. SPDX-License-Identifier: BSD-3-Clause
"""Trace the first control steps of a DexSuite policy in a chosen physics engine (T17).

Same loading as evaluate.py: Play config, deterministic policy (mean action), seed 42. For every env and every
control step up to --steps, saves the robot state *at the moment terminations are computed* (before the env resets
the finished envs), so the values at the step where `abnormal_robot` fires are the ones that triggered it:

  joint_pos, joint_vel, joint_pos_target, applied_torque, computed_torque   (steps, envs, joints)
  actions (raw policy output), processed_actions (action term output)       (steps, envs, joints)
  term_<name> (per-step termination flags)                                  (steps, envs)
  soft_joint_pos_limits (envs, joints, 2), joint_vel_limits (envs, joints), joint_names
  first_done_step (envs,): first step at which the env's first episode ended (-1 if not within --steps)

abnormal_robot_state (dexsuite/mdp/terminations.py) fires when any |joint_vel| > 2 * joint_vel_limits.

Run with scripts/trace_episode.sh, or:
  scripts/run_isaac.sh trace_reorient_physx_in_newton trace_episode.py --task Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0 \
      --checkpoint <model.pt> --out ~/runs/traces/reorient_physx_in_newton.npz --headless physics=newton_mjwarp presets=cube
"""

import argparse
import contextlib
import importlib.metadata as metadata
import os
import sys

ISAACLAB_DIR = os.environ.get("ISAACLAB_DIR", "/workspace/isaaclab")
sys.path.insert(0, os.path.join(ISAACLAB_DIR, "scripts", "reinforcement_learning", "rsl_rl"))

import gymnasium as gym  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from packaging import version  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

from isaaclab.envs import DirectMARLEnvCfg, DirectRLEnvCfg, ManagerBasedRLEnvCfg  # noqa: E402
from isaaclab.utils.assets import retrieve_file_path  # noqa: E402

from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg  # noqa: E402

import isaaclab_tasks  # noqa: F401, E402
from isaaclab_tasks.utils import add_launcher_args, launch_simulation, setup_preset_cli  # noqa: E402
from isaaclab_tasks.utils.hydra import hydra_task_config  # noqa: E402

import cli_args  # noqa: E402

with contextlib.suppress(ImportError):
    import isaaclab_tasks_experimental  # noqa: F401

parser = argparse.ArgumentParser(description="Trace joint states of the first control steps of a policy.")
parser.add_argument("--task", type=str, required=True, help="Task name, normally the -Play-v0 variant.")
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point", help="Agent config entry point.")
parser.add_argument("--num_envs", type=int, default=16, help="Parallel environments.")
parser.add_argument("--steps", type=int, default=120, help="Control steps to record.")
parser.add_argument("--seed", type=int, default=42, help="Environment seed.")
parser.add_argument("--out", type=str, required=True, help="Output .npz path.")
cli_args.add_rsl_rl_args(parser)
add_launcher_args(parser)
args_cli, remaining_args = setup_preset_cli(parser)
sys.argv = [sys.argv[0]] + remaining_args
PRESET_ARGS = " ".join(remaining_args)

installed_version = metadata.version("rsl-rl-lib")


def _t(x) -> torch.Tensor:
    """ProxyArray (warp-backed) or tensor -> torch tensor."""
    return x.torch if hasattr(x, "torch") else x


def _np(x) -> np.ndarray:
    return _t(x).detach().float().cpu().numpy().copy()


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    with launch_simulation(env_cfg, args_cli):
        agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
        agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, installed_version)
        env_cfg.scene.num_envs = args_cli.num_envs
        env_cfg.seed = args_cli.seed
        env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device

        checkpoint = retrieve_file_path(args_cli.checkpoint)
        env_cfg.log_dir = os.path.dirname(checkpoint)

        env = gym.make(args_cli.task, cfg=env_cfg, render_mode=None)
        env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
        uenv = env.unwrapped
        robot = uenv.scene["robot"]
        term_mgr = uenv.termination_manager
        action_term = uenv.action_manager.get_term(uenv.action_manager.active_terms[0])

        print(f"[TRACE] Loading checkpoint: {checkpoint}")
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
        runner.load(checkpoint)
        policy = runner.get_inference_policy(device=uenv.device)
        new_api = version.parse(installed_version) >= version.parse("4.0.0")
        policy_nn = None if new_api else runner.alg.policy

        # Snapshot robot state when terminations are computed, i.e. before finished envs are reset.
        snap: dict[str, np.ndarray] = {}
        original_compute = term_mgr.compute

        def compute_and_snapshot(*a, **kw):
            out = original_compute(*a, **kw)
            snap["joint_pos"] = _np(robot.data.joint_pos)
            snap["joint_vel"] = _np(robot.data.joint_vel)
            snap["joint_pos_target"] = _np(robot.data.joint_pos_target)
            snap["applied_torque"] = _np(robot.data.applied_torque)
            snap["computed_torque"] = _np(robot.data.computed_torque)
            for name in term_mgr.active_terms:
                snap[f"term_{name}"] = _np(term_mgr.get_term(name))
            return out

        term_mgr.compute = compute_and_snapshot

        rec: dict[str, list] = {}
        n = args_cli.num_envs
        first_done = np.full(n, -1, dtype=np.int64)
        obs = env.get_observations()
        with torch.inference_mode():
            for step in range(args_cli.steps):
                actions = policy(obs)
                obs, _, dones, _ = env.step(actions)
                if new_api:
                    policy.reset(dones)
                else:
                    policy_nn.reset(dones)
                for k, v in snap.items():
                    rec.setdefault(k, []).append(v)
                rec.setdefault("actions", []).append(_np(actions))
                rec.setdefault("processed_actions", []).append(_np(action_term.processed_actions))
                d = dones.to(torch.bool).view(-1).cpu().numpy()
                first_done[(first_done < 0) & d] = step
                if (first_done >= 0).all():
                    print(f"[TRACE] all envs finished their first episode by step {step}")
                    break

        out = {k: np.stack(v) for k, v in rec.items()}
        out["soft_joint_pos_limits"] = _np(robot.data.soft_joint_pos_limits)
        out["joint_vel_limits"] = _np(robot.data.joint_vel_limits)
        out["joint_names"] = np.array(robot.joint_names)
        out["term_names"] = np.array(list(term_mgr.active_terms))
        out["first_done_step"] = first_done
        out["step_dt"] = np.array(uenv.step_dt)
        out["checkpoint"] = np.array(checkpoint)
        out["presets"] = np.array(PRESET_ARGS)
        os.makedirs(os.path.dirname(os.path.abspath(args_cli.out)), exist_ok=True)
        np.savez_compressed(args_cli.out, **out)

        # short summary in the log
        names = list(robot.joint_names)
        for e in range(n):
            s = int(first_done[e])
            why = [t for t in term_mgr.active_terms if s >= 0 and out[f"term_{t}"][s, e] > 0]
            msg = f"[TRACE] env {e}: first episode end step {s} {why}"
            if s >= 0 and "abnormal_robot" in why:
                ratio = np.abs(out["joint_vel"][s, e]) / out["joint_vel_limits"][e]
                j = np.argsort(-ratio)[:3]
                msg += " top |v|/limit: " + ", ".join(f"{names[i]} {ratio[i]:.2f}" for i in j)
            print(msg)
        print(f"[TRACE] saved {args_cli.out} ({len(rec['actions'])} steps, {n} envs)")
        env.close()


if __name__ == "__main__":
    main()
