# Uses the same env setup as scripts/evaluate.py (adapted from Isaac Lab 3.0.0 play_rsl_rl.py).
"""T23 step 1: record, for one physics engine, the robot's joint and body names in articulation order, plus the
names the policy-facing terms resolve to (action term joints, proprio.hand_tips_state_b bodies), and merge them into
results/joint_order.json under the engine's key. No policy, no stepping: it builds the env and reads the managers.

The T17 traces only stored joint names, so the body order needs this extra run.

Run (once per engine):
  scripts/run_isaac.sh dump_order_physx dump_order.py --task Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0 \
      --engine physx --num_envs 4 --headless physics=physx presets=cube
  scripts/run_isaac.sh dump_order_newton dump_order.py --task Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0 \
      --engine newton --num_envs 4 --headless physics=newton_mjwarp presets=cube
"""

import argparse
import contextlib
import json
import os
import sys

import gymnasium as gym

from isaaclab.envs import DirectMARLEnvCfg, DirectRLEnvCfg, ManagerBasedRLEnvCfg

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import add_launcher_args, launch_simulation, setup_preset_cli
from isaaclab_tasks.utils.hydra import hydra_task_config

with contextlib.suppress(ImportError):
    import isaaclab_tasks_experimental  # noqa: F401

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser(description="Dump joint/body order of the robot for one engine.")
parser.add_argument("--task", type=str, required=True)
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point")
parser.add_argument("--engine", type=str, required=True, choices=["physx", "newton"], help="Key in the JSON file.")
parser.add_argument("--num_envs", type=int, default=4)
parser.add_argument("--out", type=str, default=os.path.join(REPO, "results", "joint_order.json"))
add_launcher_args(parser)
args_cli, remaining_args = setup_preset_cli(parser)
sys.argv = [sys.argv[0]] + remaining_args


def _names(all_names, ids):
    if isinstance(ids, slice):
        return list(all_names[ids])
    return [all_names[int(i)] for i in ids]


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg):
    with launch_simulation(env_cfg, args_cli):
        env_cfg.scene.num_envs = args_cli.num_envs
        env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
        env = gym.make(args_cli.task, cfg=env_cfg, render_mode=None)
        u = env.unwrapped
        robot = u.scene["robot"]
        act = u.action_manager.get_term("action")
        om = u.observation_manager
        proprio = dict(zip(om._group_obs_term_names["proprio"], om._group_obs_term_cfgs["proprio"]))
        tips_cfg = proprio["hand_tips_state_b"].params["body_asset_cfg"]
        entry = {
            "task": args_cli.task,
            "presets": " ".join(remaining_args),
            "joint_names": list(robot.joint_names),
            "body_names": list(robot.body_names),
            "action_joint_names": list(act._joint_names),
            "hand_tips_body_names": _names(robot.body_names, tips_cfg.body_ids),
        }
        print(f"[ORDER] {args_cli.engine}: {json.dumps(entry, indent=1)}")
        data = {}
        if os.path.exists(args_cli.out):
            with open(args_cli.out) as f:
                data = json.load(f)
        data[args_cli.engine] = entry
        with open(args_cli.out, "w") as f:
            json.dump(data, f, indent=1)
        print(f"[ORDER] wrote {args_cli.engine} to {args_cli.out}")
        env.close()


if __name__ == "__main__":
    main()
