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
  * Termination reasons from extras["log"]["Episode_Termination/<name>"] (counts of episodes ending that way).

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
                for key, value in log.items():
                    if key.startswith("Episode_Termination/"):
                        name = key.split("/", 1)[1]
                        terminations[name] = terminations.get(name, 0.0) + _as_float(value)
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
