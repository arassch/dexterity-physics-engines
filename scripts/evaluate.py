# Adapted from Isaac Lab 3.0.0 scripts/reinforcement_learning/rsl_rl/play_rsl_rl.py
# Copyright (c) 2022-2026, The Isaac Lab Project Developers. SPDX-License-Identifier: BSD-3-Clause
"""Evaluate an RSL-RL checkpoint of a DexSuite task in a chosen physics engine, and append one row to a CSV.

What it measures (the fair, deterministic version of the training-time numbers):
  * The task's *Play* config is used (e.g. Isaac-Dexsuite-Kuka-Allegro-Lift-Play-v0): ADR starts at its maximum
    difficulty, the hardest randomisation the policies were trained towards.
  * Actions are the policy mean (RSL-RL's inference policy): no exploration noise.
  * Fixed seed, fixed number of environments, and a fixed number of completed episodes.
  * Success uses the task's own test (dexsuite/mdp/rewards.py, success_reward): an episode succeeds if, at any step,
    thumb + one finger touch the object and it is within pos_std (and rot_std for Reorient) of the target.
    It is read from extras["log"]["Metrics/success_rate"], which the task writes for the episodes ending that step.
  * Termination reasons from the termination manager's per-step flags (counts of episodes ending that way).

The physics engine is chosen exactly like in training, with the Hydra preset: physics=physx or physics=newton_mjwarp.

Run from the Isaac Lab folder (scripts/eval.sh does this):
  ./isaaclab.sh -p /root/dexterity-physics-engines/scripts/evaluate.py \
      --task Isaac-Dexsuite-Kuka-Allegro-Lift-Play-v0 --checkpoint <path/model_N.pt> \
      --num_envs 256 --episodes 1024 --seed 42 --headless \
      --label lift --train_engine physx --eval_engine newton --csv <results/cross_eval.csv> \
      physics=newton_mjwarp presets=cube
"""

import argparse
import contextlib
import csv
import importlib.metadata as metadata
import json
import math
import os
import sys
import time
from datetime import datetime, timezone

ISAACLAB_DIR = os.environ.get("ISAACLAB_DIR", "/workspace/isaaclab")
sys.path.insert(0, os.path.join(ISAACLAB_DIR, "scripts", "reinforcement_learning", "rsl_rl"))

import gymnasium as gym  # noqa: E402
import torch  # noqa: E402
from packaging import version  # noqa: E402
from rsl_rl.runners import OnPolicyRunner  # noqa: E402

from isaaclab.envs import DirectMARLEnvCfg, DirectRLEnvCfg, ManagerBasedRLEnvCfg  # noqa: E402
from isaaclab.managers import SceneEntityCfg  # noqa: E402
from isaaclab.utils.assets import retrieve_file_path  # noqa: E402

from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg  # noqa: E402

import isaaclab_tasks  # noqa: F401, E402
from isaaclab_tasks.utils import add_launcher_args, launch_simulation, setup_preset_cli  # noqa: E402
from isaaclab_tasks.utils.hydra import hydra_task_config  # noqa: E402

import cli_args  # noqa: E402  (Isaac Lab's rsl_rl/cli_args.py, found via the sys.path entry above)

with contextlib.suppress(ImportError):
    import isaaclab_tasks_experimental  # noqa: F401

parser = argparse.ArgumentParser(description="Evaluate an RSL-RL checkpoint and append the result to a CSV.")
parser.add_argument("--task", type=str, required=True, help="Task name, normally the -Play-v0 variant.")
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point", help="Agent config entry point.")
parser.add_argument("--num_envs", type=int, default=256, help="Parallel environments.")
parser.add_argument("--episodes", type=int, default=1024, help="Completed episodes to evaluate.")
parser.add_argument("--seed", type=int, default=42, help="Environment seed.")
parser.add_argument("--label", type=str, default="", help="Free-text label for the CSV row, e.g. 'lift'.")
parser.add_argument("--train_engine", type=str, default="", help="Engine the checkpoint was trained in (label only).")
parser.add_argument("--eval_engine", type=str, default="", help="Engine used now (label only; the physics= preset decides).")
parser.add_argument("--csv", type=str, required=True, help="CSV file to append the result row to.")
parser.add_argument("--max_steps", type=int, default=20000, help="Safety cap on environment steps.")
parser.add_argument(
    "--match_order",
    type=str,
    default="",
    choices=["", "physx", "newton"],
    help="T23: make the action term and the joint/hand-tip observations use this (training) engine's joint and body "
    "order, matched by name. Orders come from --order_json (written by scripts/dump_order.py).",
)
parser.add_argument(
    "--order_json",
    type=str,
    default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "joint_order.json"),
)
parser.add_argument(
    "--robot_params",
    type=str,
    default="",
    help="T20 'fitted Newton' (Newton only): a sysid_robot.json (scripts/sysid_fit.py). Applies all three of: the "
    "per-physics-step finger velocity clamp, num_substeps from the json (8), and the json's `best` finger armature / "
    "damping_scale / effort_scale, re-applied after every reset (same calls as sysid_harness.py _apply_params).",
)
cli_args.add_rsl_rl_args(parser)
add_launcher_args(parser)
args_cli, remaining_args = setup_preset_cli(parser)
sys.argv = [sys.argv[0]] + remaining_args
PRESET_ARGS = " ".join(remaining_args)

installed_version = metadata.version("rsl-rl-lib")


def _as_float(x) -> float:
    if isinstance(x, torch.Tensor):
        return float(x.float().mean().item()) if x.numel() > 1 else float(x.item())
    return float(x)


def _apply_match_order(env_cfg, engine: str, order_json: str) -> dict:
    """Make every policy-facing term that depends on joint or body order follow `engine`'s order, by name.

    Order-dependent terms in the DexSuite Kuka-Allegro state config (checked for T23):
      actions.action (RelativeJointPositionAction, joint_names [".*"])  -> changed
      observations.proprio.joint_pos / joint_vel (default asset_cfg = all joints, articulation order) -> changed
      observations.proprio.hand_tips_state_b (body_names ["palm_link", ".*_tip"]) -> changed
    Order-independent: policy.actions (last_action, already in action-term order), policy.object_quat_b,
      policy.target_object_pose_b, proprio.contact (sensor names in a fixed list).
    """
    with open(order_json) as f:
        order = json.load(f)[engine]
    joints = list(order["joint_names"])
    tips = list(order["hand_tips_body_names"])
    env_cfg.actions.action.joint_names = joints
    env_cfg.actions.action.preserve_order = True
    proprio = env_cfg.observations.proprio
    for term in (proprio.joint_pos, proprio.joint_vel):
        term.params["asset_cfg"] = SceneEntityCfg("robot", joint_names=joints, preserve_order=True)
    tips_cfg = proprio.hand_tips_state_b.params["body_asset_cfg"]
    tips_cfg.body_names = tips
    tips_cfg.preserve_order = True
    return order


def _check_match_order(u_env, order: dict) -> None:
    """Print the resolved names and fail if they are not the training engine's lists."""
    robot = u_env.scene["robot"]
    act_names = list(u_env.action_manager.get_term("action")._joint_names)
    om = u_env.observation_manager
    proprio = dict(zip(om._group_obs_term_names["proprio"], om._group_obs_term_cfgs["proprio"]))

    def names(all_names, ids):
        return list(all_names[ids]) if isinstance(ids, slice) else [all_names[int(i)] for i in ids]

    resolved = {
        "action": act_names,
        "joint_pos": names(robot.joint_names, proprio["joint_pos"].params["asset_cfg"].joint_ids),
        "joint_vel": names(robot.joint_names, proprio["joint_vel"].params["asset_cfg"].joint_ids),
        "hand_tips_state_b": names(robot.body_names, proprio["hand_tips_state_b"].params["body_asset_cfg"].body_ids),
    }
    expected = {"action": order["joint_names"], "joint_pos": order["joint_names"], "joint_vel": order["joint_names"],
                "hand_tips_state_b": order["hand_tips_body_names"]}
    print(f"[EVAL] match_order: this engine's articulation joint order: {list(robot.joint_names)}")
    for key, got in resolved.items():
        print(f"[EVAL] match_order: {key} resolved to {got}")
        if got != list(expected[key]):
            raise RuntimeError(f"match_order: {key} resolved to {got}, expected {list(expected[key])}")
    print("[EVAL] match_order: all resolved lists equal the training engine's lists")


def _t(x) -> torch.Tensor:
    return x.torch if hasattr(x, "torch") else x


def _install_fitted_robot(u_env, fit: dict) -> dict:
    """T20 'fitted Newton': velocity clamp every physics step + fitted finger params after every reset.

    The clamp and the parameter writes are the same calls as scripts/sysid_harness.py (apply_fixed_target,
    _apply_params). The task's robot events stay on; the startup actuator-gain randomisation is overridden on the
    finger joints because the fitted damping (nominal x damping_scale) is written after every reset. Nominal finger
    damping comes from that event term's stored defaults (else the current values); nominal effort limit from the
    articulation at build time (no event changes it).
    """
    robot = u_env.scene["robot"]
    dev = u_env.device
    names = list(robot.joint_names)
    finger_ids = [i for i, nm in enumerate(names) if not nm.startswith("iiwa7")]
    assert len(finger_ids) == 16, names
    best = fit["best"]
    arm, d_scale, e_scale = float(best["armature"]), float(best["damping_scale"]), float(best["effort_scale"])

    nom_damping = None
    with contextlib.suppress(Exception):
        term = u_env.event_manager.get_term_cfg("joint_stiffness_and_damping").func
        nom_damping = term.default_joint_damping.clone().float()[:, finger_ids]
    src = "event term defaults"
    if nom_damping is None:
        nom_damping, src = _t(robot.data.joint_damping).clone().float()[:, finger_ids], "articulation (no event term)"
    nom_effort = _t(robot.data.joint_effort_limits).clone().float()[:, finger_ids]
    damping = (nom_damping * d_scale).contiguous()
    effort = (nom_effort * e_scale).contiguous()
    armature = torch.full_like(damping, arm)

    def apply(env_ids=None):
        if env_ids is None:
            ids, sl = None, slice(None)
        else:
            ids = torch.as_tensor(env_ids, device=dev, dtype=torch.long)
            if ids.numel() == 0:
                return
            sl = ids
        robot.write_joint_armature_to_sim_index(armature=armature[sl].contiguous(), joint_ids=finger_ids, env_ids=ids)
        robot.write_joint_damping_to_sim_index(damping=damping[sl].contiguous(), joint_ids=finger_ids, env_ids=ids)
        robot.write_joint_effort_limit_to_sim_index(limits=effort[sl].contiguous(), joint_ids=finger_ids, env_ids=ids)

    orig_reset_idx = u_env._reset_idx

    def _reset_idx(env_ids, *a, **kw):
        res = orig_reset_idx(env_ids, *a, **kw)
        apply(env_ids)
        return res

    u_env._reset_idx = _reset_idx
    apply(None)

    # velocity clamp on the finger joints, once per physics step, after the action term writes its targets
    vlim = _t(robot.data.joint_vel_limits).clone().float()
    fmask = torch.zeros(len(names), dtype=torch.bool, device=dev)
    fmask[finger_ids] = True
    term = u_env.action_manager.get_term("action")
    orig_apply = term.apply_actions

    def apply_actions():
        orig_apply()
        v = _t(robot.data.joint_vel).clone().float()
        robot.write_joint_velocity_to_sim_index(velocity=torch.where(fmask, torch.clamp(v, -vlim, vlim), v))

    term.apply_actions = apply_actions

    got = {
        "armature": _t(robot.data.joint_armature).float()[:, finger_ids],
        "damping": _t(robot.data.joint_damping).float()[:, finger_ids],
        "effort_limit": _t(robot.data.joint_effort_limits).float()[:, finger_ids],
    }
    info = {k: (float(v.min()), float(v.max())) for k, v in got.items()}
    print(f"[EVAL] robot_params: fitted {best['armature']:.4f} / x{d_scale:.3f} / x{e_scale:.3f}; nominal finger damping "
          f"from {src}: mean {float(nom_damping.mean()):.4f}, effort mean {float(nom_effort.mean()):.4f}")
    print(f"[EVAL] robot_params: applied on 16 finger joints x {u_env.num_envs} envs (min, max): {info}; "
          f"velocity clamp at +-limit (finger limits {float(vlim[:, finger_ids].min()):.3f}..."
          f"{float(vlim[:, finger_ids].max()):.3f} rad/s) every physics step; "
          f"num_substeps {getattr(u_env.cfg.sim.physics, 'num_substeps', '?')}")
    for k, want in (("armature", armature), ("damping", damping), ("effort_limit", effort)):
        if not torch.allclose(got[k], want, rtol=1e-4, atol=1e-6):
            raise RuntimeError(f"robot_params: {k} not applied: got {info[k]}, want {float(want.min())}..{float(want.max())}")
    return info


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

        order = None
        if args_cli.match_order:
            order = _apply_match_order(env_cfg, args_cli.match_order, args_cli.order_json)

        fit = None
        if args_cli.robot_params:
            with open(args_cli.robot_params) as f:
                fit = json.load(f)
            if not hasattr(env_cfg.sim.physics, "num_substeps"):
                raise RuntimeError(f"--robot_params is Newton only; physics cfg is {type(env_cfg.sim.physics)}")
            env_cfg.sim.physics.num_substeps = int(fit.get("num_substeps", 8))

        env = gym.make(args_cli.task, cfg=env_cfg, render_mode=None)
        if order is not None:
            _check_match_order(env.unwrapped, order)
        if fit is not None:
            _install_fitted_robot(env.unwrapped, fit)
        env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

        print(f"[EVAL] Loading checkpoint: {checkpoint}")
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
        runner.load(checkpoint)
        policy = runner.get_inference_policy(device=env.unwrapped.device)
        new_api = version.parse(installed_version) >= version.parse("4.0.0")
        policy_nn = None if new_api else runner.alg.policy

        episodes = 0
        successes = 0.0
        terminations: dict[str, float] = {}
        steps = 0
        nan_steps = 0
        t0 = time.time()
        obs = env.get_observations()

        with torch.inference_mode():
            while episodes < args_cli.episodes and steps < args_cli.max_steps:
                actions = policy(obs)
                obs, _, dones, extras = env.step(actions)
                if new_api:
                    policy.reset(dones)
                else:
                    policy_nn.reset(dones)
                steps += 1

                if torch.isnan(actions).any():
                    nan_steps += 1

                n_done = int(dones.sum().item())
                if n_done == 0:
                    continue
                log = extras.get("log", {}) or {}
                rate = log.get("Metrics/success_rate")
                if rate is not None:
                    successes += _as_float(rate) * n_done
                # extras["log"]["Episode_Termination/<name>"] is a mean over *all* envs of each env's last episode,
                # not a count for the episodes ending now, so count from the termination manager's per-step flags.
                done_mask = dones.to(torch.bool).view(-1)
                term_mgr = env.unwrapped.termination_manager
                for name in term_mgr.active_terms:
                    count = int(term_mgr.get_term(name)[done_mask].sum().item())
                    terminations[name] = terminations.get(name, 0.0) + count
                episodes += n_done
                if steps % 50 == 0:
                    print(f"[EVAL] step {steps}: {episodes} episodes, success so far {successes / episodes:.3f}")

        elapsed = time.time() - t0
        success_rate = successes / episodes if episodes else float("nan")
        # 95% Wilson interval, so small differences between cells can be judged honestly
        if episodes:
            z = 1.96
            p = success_rate
            centre = (p + z * z / (2 * episodes)) / (1 + z * z / episodes)
            half = z * math.sqrt(p * (1 - p) / episodes + z * z / (4 * episodes * episodes)) / (1 + z * z / episodes)
            ci_low, ci_high = max(0.0, centre - half), min(1.0, centre + half)
        else:
            ci_low = ci_high = float("nan")

        row = {
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "label": args_cli.label,
            "task": args_cli.task,
            "train_engine": args_cli.train_engine,
            "eval_engine": args_cli.eval_engine,
            "checkpoint": checkpoint,
            "episodes": episodes,
            "success_rate": round(success_rate, 4),
            "ci95_low": round(ci_low, 4),
            "ci95_high": round(ci_high, 4),
            "num_envs": args_cli.num_envs,
            "seed": args_cli.seed,
            "steps": steps,
            "nan_action_steps": nan_steps,
            "seconds": round(elapsed, 1),
            "presets": PRESET_ARGS,
        }
        if args_cli.robot_params:  # recorded in the presets column (no new CSV column: the header isn't rewritten)
            row["presets"] = f"{PRESET_ARGS} robot_params={os.path.basename(args_cli.robot_params)}"
        for name, count in sorted(terminations.items()):
            row[f"term_{name}"] = round(count / episodes, 4) if episodes else ""

        os.makedirs(os.path.dirname(os.path.abspath(args_cli.csv)), exist_ok=True)
        existing_header = None
        if os.path.exists(args_cli.csv) and os.path.getsize(args_cli.csv) > 0:
            with open(args_cli.csv, newline="") as f:
                existing_header = next(csv.reader(f), None)
        fieldnames = existing_header or list(row.keys())
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)  # new termination type: appended column (header not rewritten)
        with open(args_cli.csv, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if existing_header is None:
                writer.writeheader()
            writer.writerow(row)

        print(f"[EVAL] RESULT {row}")
        if episodes < args_cli.episodes:
            print(f"[EVAL] WARNING: only {episodes} episodes completed before --max_steps {args_cli.max_steps}")
        env.close()


if __name__ == "__main__":
    main()
