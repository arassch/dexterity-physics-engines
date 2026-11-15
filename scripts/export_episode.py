# Adapted from Isaac Lab 3.0.0 scripts/reinforcement_learning/rsl_rl/play_rsl_rl.py (via scripts/evaluate.py)
# Copyright (c) 2022-2026, The Isaac Lab Project Developers. SPDX-License-Identifier: BSD-3-Clause
"""Play an RSL-RL DexSuite checkpoint and record the motion, so it can be replayed outside Isaac Lab (e.g. Unreal).

For every control step (60 Hz) and every environment it records:
  * the 23 robot joint positions (7 Kuka arm + 16 Allegro hand), with joint names
  * every robot body (link) pose, env-local (env origin subtracted), with body names
  * the object (cube) pose and the target (goal) pose, env-local
  * position error and rotation error between object and target, and which termination ended an episode
Poses are (x, y, z) in metres plus a quaternion in Isaac Lab 3 order (qx, qy, qz, qw); Z is up.

With --stage_out (PhysX only: it needs the USD stage that Kit builds), it also saves the scene as one flattened USD
file, plus the USD prim path of every body, so scripts/make_usd_animation.py can turn the recording into a USD
animation that Unreal's USD Stage actor plays back.

Run from the Isaac Lab folder (scripts/export_episode.sh does this):
  ./isaaclab.sh -p /root/dexterity-physics-engines/scripts/export_episode.py \
      --task Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0 --checkpoint <model_N.pt> --num_envs 4 --steps 720 \
      --seed 42 --headless --out <recording.json> [--stage_out <scene.usd>] physics=physx presets=cube
"""

import argparse
import contextlib
import importlib.metadata as metadata
import json
import os
import sys

ISAACLAB_DIR = os.environ.get("ISAACLAB_DIR", "/workspace/isaaclab")
sys.path.insert(0, os.path.join(ISAACLAB_DIR, "scripts", "reinforcement_learning", "rsl_rl"))

import gymnasium as gym  # noqa: E402
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

parser = argparse.ArgumentParser(description="Record a policy's motion to JSON (and optionally the scene to USD).")
parser.add_argument("--task", type=str, required=True)
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point")
parser.add_argument("--num_envs", type=int, default=4)
parser.add_argument("--steps", type=int, default=720, help="Control steps to record (360 = one 6 s episode).")
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--out", type=str, required=True, help="Output JSON file.")
parser.add_argument("--stage_out", type=str, default="", help="Also export the flattened scene to this USD file.")
parser.add_argument("--label", type=str, default="")
cli_args.add_rsl_rl_args(parser)
add_launcher_args(parser)
args_cli, remaining_args = setup_preset_cli(parser)
sys.argv = [sys.argv[0]] + remaining_args
PRESET_ARGS = " ".join(remaining_args)
installed_version = metadata.version("rsl-rl-lib")


def _t(x) -> torch.Tensor:
    """Isaac Lab 3 data buffers expose a torch view as .torch; plain tensors pass through."""
    return x.torch if hasattr(x, "torch") else x


def _r(t: torch.Tensor, nd: int = 5):
    return [round(v, nd) for v in t.detach().float().cpu().view(-1).tolist()]


def _quat_angle(q1: torch.Tensor, q2: torch.Tensor) -> torch.Tensor:
    """Angle (rad) between two batches of unit quaternions, any component order as long as both match."""
    dot = (q1 * q2).sum(-1).abs().clamp(max=1.0)
    return 2.0 * torch.acos(dot)


def _export_stage(path: str, body_names: list[str]) -> dict:
    """Flatten the USD stage to one file and find each robot body's prim in env_0. PhysX/Kit only."""
    import omni.usd  # noqa: PLC0415

    stage = omni.usd.get_context().get_stage()
    stage.Export(path)
    robot_root = "/World/envs/env_0/Robot"
    found: dict[str, str] = {}
    for prim in stage.Traverse():
        p = str(prim.GetPath())
        if p.startswith(robot_root + "/") and prim.GetName() in body_names and prim.GetName() not in found:
            found[prim.GetName()] = p
    return {"stage_file": os.path.basename(path), "robot_root": robot_root, "object_prim": "/World/envs/env_0/Object",
            "env_prim": "/World/envs/env_0", "body_prims": found}


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
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
        runner.load(checkpoint)
        policy = runner.get_inference_policy(device=env.unwrapped.device)
        new_api = version.parse(installed_version) >= version.parse("4.0.0")
        policy_nn = None if new_api else runner.alg.policy

        uenv = env.unwrapped
        robot = uenv.scene["robot"]
        obj = uenv.scene["object"]
        command = uenv.command_manager.get_term("object_pose")
        origins = _t(uenv.scene.env_origins)
        term_mgr = uenv.termination_manager
        body_names = list(robot.body_names)

        meta = {
            "task": args_cli.task, "label": args_cli.label, "checkpoint": checkpoint, "presets": PRESET_ARGS,
            "seed": args_cli.seed, "num_envs": args_cli.num_envs, "control_dt": float(uenv.step_dt),
            "units": "metres, Z up, right-handed", "quat_order": "qx qy qz qw (Isaac Lab 3)",
            "joint_names": list(robot.joint_names), "body_names": body_names,
            "env_origins": [_r(o) for o in origins],
        }
        if args_cli.stage_out:
            try:
                meta["usd"] = _export_stage(args_cli.stage_out, body_names)
                print(f"[EXPORT] stage written to {args_cli.stage_out}; matched "
                      f"{len(meta['usd']['body_prims'])}/{len(body_names)} body prims")
            except Exception as e:  # noqa: BLE001  (Newton runs have no Kit stage; keep recording anyway)
                meta["usd_error"] = repr(e)
                print(f"[EXPORT] WARNING: stage export failed: {e!r}")

        frames = []
        obs = env.get_observations()
        with torch.inference_mode():
            for step in range(args_cli.steps):
                d = robot.data
                obj_pos = _t(obj.data.root_pos_w) - origins
                obj_quat = _t(obj.data.root_quat_w)
                goal_w = _t(command.pose_command_w)
                goal_pos = goal_w[:, :3] - origins
                goal_quat = goal_w[:, 3:7]
                body_pos = _t(d.body_pos_w) - origins.unsqueeze(1)
                body_quat = _t(d.body_quat_w)
                pos_err = (obj_pos - goal_pos).norm(dim=-1)
                rot_err = _quat_angle(obj_quat, goal_quat)
                frame = {"step": step, "t": round(step * meta["control_dt"], 4), "envs": []}
                for i in range(args_cli.num_envs):
                    frame["envs"].append({
                        "joint_pos": _r(_t(d.joint_pos)[i]),
                        "body_pos": [_r(p) for p in body_pos[i]], "body_quat": [_r(q) for q in body_quat[i]],
                        "object_pos": _r(obj_pos[i]), "object_quat": _r(obj_quat[i]),
                        "goal_pos": _r(goal_pos[i]), "goal_quat": _r(goal_quat[i]),
                        "pos_err": round(float(pos_err[i]), 4), "rot_err": round(float(rot_err[i]), 4),
                    })
                actions = policy(obs)
                obs, _, dones, _ = env.step(actions)
                (policy if new_api else policy_nn).reset(dones)
                done_mask = dones.to(torch.bool).view(-1)
                for i in torch.nonzero(done_mask).view(-1).tolist():
                    reasons = [n for n in term_mgr.active_terms if bool(term_mgr.get_term(n)[i])]
                    frame["envs"][i]["episode_end"] = reasons or ["unknown"]
                frames.append(frame)
                if step % 120 == 0:
                    print(f"[EXPORT] step {step}/{args_cli.steps}")

        os.makedirs(os.path.dirname(os.path.abspath(args_cli.out)), exist_ok=True)
        with open(args_cli.out, "w") as f:
            json.dump({"meta": meta, "frames": frames}, f, separators=(",", ":"))
        ends = sum(1 for fr in frames for e in fr["envs"] if "episode_end" in e)
        print(f"[EXPORT] wrote {args_cli.out}: {len(frames)} steps x {args_cli.num_envs} envs, {ends} episode ends")
        env.close()


if __name__ == "__main__":
    main()
