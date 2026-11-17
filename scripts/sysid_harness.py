"""T19 system-ID harness: replay PhysX's recorded joint targets in Newton with per-env finger parameters.

PhysX is the "real robot". This builds a Newton (MuJoCo Warp) Reorient Play env, robot only (cube parked), ADR max,
robot randomisation events off (as in scripts/step_response.py), with T19's fixed corrections:
  1. velocity-limit emulation: each finger joint's velocity is clipped to +-its velocity limit once per physics step
     (default --clamp_mode physics_step, like T25's --clamp_vel). The per-solver-substep variant (--clamp_mode substep:
     NewtonManager._step_solver wrapped with a Warp kernel, CUDA graph re-captured) crashed twice with a CUDA illegal
     memory access, so PLAN.md's fallback is the default.
  2. num_substeps (--num_substeps, default 8 until the T19 speed test picks one).

Use as a module (inside Isaac Lab's Python, launched with scripts/run_isaac.sh):
    from sysid_harness import run_with_harness
    def fit(h):            # h: Harness
        out = h.rollout(h.default_params())
        ...
    run_with_harness(fit)  # parses the CLI below, launches the app, builds the env, calls fit(h), closes

Harness API:
    default_params()  -> (N, 3) float32 numpy: [armature, damping_scale, effort_scale]; armature = current nominal mean
    param_bounds()    -> (lo, hi) numpy arrays of shape (3,)
    rollout(params)   -> dict, all joint arrays (N, signal, steps, 23) in PHYSX's joint order (by name):
        joint_pos, joint_vel, target              Newton
        physx_joint_pos, physx_joint_vel          PhysX reference for the same envs (ref env = ref_env[i])
        reset (N, signal) bool, reset_step (N, signal) int (-1 if none), abnormal (N, signal) bool
        physx_reset (N, signal) bool              envs whose PhysX reference itself reset (exclude them)
        signals ('a','b','c'), joint_names (PhysX order), finger (23,) bool, ref_env (N,)
    params are written with write_joint_{armature,damping,effort_limit}_to_sim_index on the 16 finger joints after
    every signal reset (robot randomisation events are off, so auto-resets don't change them).

CLI:  scripts/run_isaac.sh sysid_check sysid_harness.py --headless --check physics=newton_mjwarp presets=cube
"""

import argparse
import contextlib
import os
import sys

import gymnasium as gym
import numpy as np
import torch
import warp as wp

from isaaclab.envs import ManagerBasedRLEnvCfg

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import add_launcher_args, launch_simulation, setup_preset_cli
from isaaclab_tasks.utils.hydra import hydra_task_config

with contextlib.suppress(ImportError):
    import isaaclab_tasks_experimental  # noqa: F401

TASK = "Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0"
OBJECT_PARK = (0.3, 1.5, 1.5)
ROBOT_RANDOMISATION_EVENTS = ("joint_stiffness_and_damping", "joint_friction", "robot_physics_material")
SIGNALS = ("a", "b", "c")
BOUNDS_LO = np.array([0.01, 0.5, 0.5], dtype=np.float32)
BOUNDS_HI = np.array([0.1, 4.0, 2.0], dtype=np.float32)

parser = argparse.ArgumentParser(description="T19 Newton system-ID harness")
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--num_substeps", type=int, default=8)
parser.add_argument("--no_clamp", action="store_true", help="disable the velocity clamp (diagnostics)")
parser.add_argument("--clamp_mode", choices=("physics_step", "substep"), default="physics_step",
                    help="physics_step (default, T19 fallback) or substep (crashes with CUDA illegal memory access)")
parser.add_argument("--ref", type=str, default=os.path.expanduser("~/runs/step_response/t19_ref_physx.npz"),
                    help="PhysX recording from step_response.py --adr max --signals abc")
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--check", action="store_true", help="roll out default params, print RMS error and resets")
parser.add_argument("--repeats", type=int, default=0, help="sysid_fit.py: blocks of 64 envs per candidate (0 = env SYSID_REPEATS or 1)")
parser.add_argument("--out", type=str, default="", help="sysid_fit.py: output json (default results/sysid_robot.json)")
add_launcher_args(parser)
args_cli, remaining_args = setup_preset_cli(parser)
sys.argv = [sys.argv[0]] + remaining_args


def _t(x) -> torch.Tensor:
    return x.torch if hasattr(x, "torch") else x


@wp.kernel
def _clamp_qd(qd: wp.array(dtype=wp.float32), idx: wp.array(dtype=wp.int32), lim: wp.array(dtype=wp.float32)):
    i = wp.tid()
    d = idx[i]
    qd[d] = wp.clamp(qd[d], -lim[i], lim[i])


def install_substep_clamp(robot, joint_ids, env_count):
    """Clip the given robot joints' velocities to +-limit before every Newton solver substep. Returns #dofs."""
    from isaaclab_newton.physics.newton_manager import NewtonManager

    model = NewtonManager.get_model()
    labels = [lb.split("/")[-1] for lb in model.joint_label]
    worlds = model.joint_world.numpy()
    qd_start = model.joint_qd_start.numpy()
    names = list(robot.joint_names)
    vlim = _t(robot.data.joint_vel_limits).float().cpu().numpy()  # (envs, joints)
    lookup = {}
    for j, (lb, w) in enumerate(zip(labels, worlds)):
        lookup.setdefault((int(w), lb), []).append(j)
    idx, lim = [], []
    for e in range(env_count):
        for k in joint_ids:
            js = lookup.get((e, names[k]), [])
            assert len(js) == 1, (e, names[k], js)
            idx.append(int(qd_start[js[0]]))
            lim.append(float(vlim[e, k]))
    dev = model.device
    idx_wp = wp.array(np.array(idx, dtype=np.int32), dtype=wp.int32, device=dev)
    lim_wp = wp.array(np.array(lim, dtype=np.float32), dtype=wp.float32, device=dev)
    orig = NewtonManager.__dict__["_step_solver"].__func__

    def _step_solver(cls, state_0, state_1, control, contacts, substep_dt):
        wp.launch(_clamp_qd, dim=len(idx), inputs=[state_0.joint_qd, idx_wp, lim_wp], device=dev)
        orig(cls, state_0, state_1, control, contacts, substep_dt)

    NewtonManager._step_solver = classmethod(_step_solver)
    NewtonManager._clamp_arrays = (idx_wp, lim_wp)  # keep alive for the graph
    # Keep the first graph alive: destroying it frees memory-pool buffers that were allocated lazily during its
    # capture and are still referenced by the solver (suspected cause of smoke attempt 1's illegal memory access).
    NewtonManager._pre_clamp_graph = NewtonManager._graph
    wp.synchronize_device(dev)
    NewtonManager._capture_or_defer_graph()  # re-capture so the graph contains the clamp
    wp.synchronize_device(dev)
    return idx_wp, lim_wp


class Harness:
    def __init__(self, env, ref_path, num_substeps, clamp):
        u = env.unwrapped
        self.u, self.robot, self.obj, self.dev = u, u.scene["robot"], u.scene["object"], u.device
        self.n = u.num_envs
        self.names = list(self.robot.joint_names)
        assert len(self.names) == 23, self.names
        self.finger_ids = [i for i, nm in enumerate(self.names) if not nm.startswith("iiwa7")]
        assert len(self.finger_ids) == 16
        self.term = u.action_manager.get_term(u.action_manager.active_terms[0])
        self.target = torch.zeros(self.n, 23, device=self.dev)
        jids = self.term._joint_ids

        self.clamp = clamp
        self.clamp_mode = args_cli.clamp_mode
        self.vlim = _t(self.robot.data.joint_vel_limits).clone().float()
        fmask = torch.zeros(23, dtype=torch.bool, device=self.dev)
        fmask[self.finger_ids] = True
        self.fmask = fmask
        step_clamp = clamp and self.clamp_mode == "physics_step"

        def apply_fixed_target():
            self.robot.set_joint_position_target_index(
                target=self.target if isinstance(jids, slice) else self.target[:, jids], joint_ids=jids)
            if step_clamp:  # T19 fallback: clip finger velocities once per physics step (as T25's --clamp_vel)
                v = _t(self.robot.data.joint_vel).clone().float()
                vc = torch.where(self.fmask, torch.clamp(v, -self.vlim, self.vlim), v)
                self.robot.write_joint_velocity_to_sim_index(velocity=vc)

        self.term.apply_actions = apply_fixed_target
        self.zero_action = torch.zeros(self.n, u.action_manager.total_action_dim, device=self.dev)
        u.reset()
        self.default = _t(self.robot.data.default_joint_pos).clone().float()
        self.nom_damping = _t(self.robot.data.joint_damping).clone().float()[:, self.finger_ids]
        self.nom_effort = _t(self.robot.data.joint_effort_limits).clone().float()[:, self.finger_ids]
        self.nom_armature = _t(self.robot.data.joint_armature).clone().float()[:, self.finger_ids]
        self.num_substeps = num_substeps
        if clamp and self.clamp_mode == "substep":
            idx, _ = install_substep_clamp(self.robot, self.finger_ids, self.n)
            print(f"[SYSID] per-substep velocity clamp installed on {idx.shape[0]} finger dofs")
        elif step_clamp:
            print(f"[SYSID] per-physics-step velocity clamp on {len(self.finger_ids)} finger joints x {self.n} envs; "
                  f"physics handles decimation: {getattr(u, '_physics_handles_decimation', '?')} "
                  f"(decimation {u.cfg.decimation})")

        # PhysX reference, mapped by name to this env's joint order and to PhysX order for output
        ref = np.load(ref_path)
        self.px_names = [str(s) for s in ref["joint_names"]]
        assert sorted(self.px_names) == sorted(self.names)
        self.to_px = [self.names.index(nm) for nm in self.px_names]  # newton index for each physx joint
        from_px = [self.px_names.index(nm) for nm in self.names]
        n_ref = ref["c_target"].shape[1]
        self.ref_env = np.arange(self.n) % n_ref
        self.T = ref["c_target"].shape[0]
        self.ref = {}
        for s in SIGNALS:
            r = self.ref_env
            self.ref[s] = dict(
                target=torch.tensor(ref[f"{s}_target"][:, r][:, :, from_px], device=self.dev),  # newton order
                joint_pos=ref[f"{s}_joint_pos"][:, r].transpose(1, 0, 2),  # (N, T, 23) physx order
                joint_vel=ref[f"{s}_joint_vel"][:, r].transpose(1, 0, 2),
                reset=ref[f"{s}_reset"][-1, r] > 0,
            )
        self.tm = u.termination_manager

    def default_params(self):
        p = np.empty((self.n, 3), dtype=np.float32)
        p[:, 0] = float(self.nom_armature.mean())
        p[:, 1] = 1.0
        p[:, 2] = 1.0
        return p

    @staticmethod
    def param_bounds():
        return BOUNDS_LO.copy(), BOUNDS_HI.copy()

    def _apply_params(self, p):
        p = torch.as_tensor(p, device=self.dev, dtype=torch.float32)
        f = self.finger_ids
        r = self.robot
        r.write_joint_armature_to_sim_index(armature=p[:, 0:1].expand(-1, len(f)).contiguous(), joint_ids=f)
        r.write_joint_damping_to_sim_index(damping=(self.nom_damping * p[:, 1:2]).contiguous(), joint_ids=f)
        r.write_joint_effort_limit_to_sim_index(limits=(self.nom_effort * p[:, 2:3]).contiguous(), joint_ids=f)

    def _reset(self, p):
        u, n = self.u, self.n
        u.reset()
        self.robot.write_joint_position_to_sim_index(position=self.default.clone())
        self.robot.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(self.default))
        pose = torch.cat([_t(self.obj.data.root_pos_w).clone(), _t(self.obj.data.root_quat_w).clone()], dim=-1)
        pose[:, :3] = u.scene.env_origins + torch.tensor(OBJECT_PARK, device=self.dev)
        self.obj.write_root_pose_to_sim_index(root_pose=pose)
        self.obj.write_root_velocity_to_sim_index(root_velocity=torch.zeros(n, 6, device=self.dev))
        self._apply_params(p)

    @torch.no_grad()
    def rollout(self, params):
        params = np.asarray(params, dtype=np.float32)
        assert params.shape == (self.n, 3), params.shape
        S, T, n = len(SIGNALS), self.T, self.n
        pos = np.zeros((n, S, T, 23), np.float32)
        vel = np.zeros_like(pos)
        tgt = np.zeros_like(pos)
        reset_step = -np.ones((n, S), np.int64)
        abnormal = np.zeros((n, S), bool)
        ab = "abnormal_robot" if "abnormal_robot" in self.tm.active_terms else None
        for si, s in enumerate(SIGNALS):
            self._reset(params)
            for k in range(T):
                self.target[:] = self.ref[s]["target"][k]
                _, _, term, trunc, _ = self.u.step(self.zero_action)
                done = (term | trunc).cpu().numpy()
                new = done & (reset_step[:, si] < 0)
                reset_step[new, si] = k
                if ab is not None:
                    abnormal[new, si] = self.tm.get_term(ab).cpu().numpy()[new] > 0
                pos[:, si, k] = _t(self.robot.data.joint_pos).float().cpu().numpy()[:, self.to_px]
                vel[:, si, k] = _t(self.robot.data.joint_vel).float().cpu().numpy()[:, self.to_px]
                tgt[:, si, k] = self.target.cpu().numpy()[:, self.to_px]
        px = self.ref
        return dict(
            joint_pos=pos, joint_vel=vel, target=tgt,
            physx_joint_pos=np.stack([px[s]["joint_pos"] for s in SIGNALS], 1),
            physx_joint_vel=np.stack([px[s]["joint_vel"] for s in SIGNALS], 1),
            reset=reset_step >= 0, reset_step=reset_step, abnormal=abnormal,
            physx_reset=np.stack([px[s]["reset"] for s in SIGNALS], 1),
            signals=SIGNALS, joint_names=self.px_names, ref_env=self.ref_env,
            finger=np.array([not nm.startswith("iiwa7") for nm in self.px_names]),
        )


def check(h: Harness):
    out = h.rollout(h.default_params())
    print(f"[SYSID] check: {h.n} envs, num_substeps={h.num_substeps}, clamp={h.clamp} ({h.clamp_mode}), "
          f"nominal finger armature mean {float(h.nom_armature.mean()):.4f}, "
          f"damping mean {float(h.nom_damping.mean()):.4f}, effort mean {float(h.nom_effort.mean()):.4f}")
    for si, s in enumerate(SIGNALS):
        ok = ~out["physx_reset"][:, si]
        valid = np.ones((h.n, h.T), bool)
        for e in range(h.n):
            if out["reset_step"][e, si] >= 0:
                valid[e, out["reset_step"][e, si]:] = False
        m = valid & ok[:, None]
        d = (out["joint_pos"][:, si] - out["physx_joint_pos"][:, si])[..., out["finger"]]
        rms = float(np.sqrt((d[m] ** 2).mean())) if m.any() else float("nan")
        print(f"[SYSID] signal {s}: finger RMS |q_newton - q_physx| {rms:.4f} rad over valid steps; "
              f"resets {int(out['reset'][:, si].sum())}/{h.n} (abnormal_robot {int(out['abnormal'][:, si].sum())}); "
              f"PhysX ref resets {int((~ok).sum())}")


def run_with_harness(callback, num_envs=None):
    @hydra_task_config(TASK, "rsl_rl_cfg_entry_point")
    def _main(env_cfg: ManagerBasedRLEnvCfg, agent_cfg):
        with launch_simulation(env_cfg, args_cli):
            env_cfg.scene.num_envs = num_envs or args_cli.num_envs
            env_cfg.seed = args_cli.seed
            env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
            for name in ROBOT_RANDOMISATION_EVENTS:
                setattr(env_cfg.events, name, None)
            assert hasattr(env_cfg.sim.physics, "num_substeps"), f"Newton only: {type(env_cfg.sim.physics)}"
            env_cfg.sim.physics.num_substeps = args_cli.num_substeps
            print(f"[SYSID] ADR init_difficulty={env_cfg.curriculum.adr.params['init_difficulty']}, "
                  f"num_substeps={args_cli.num_substeps}, clamp={not args_cli.no_clamp}")
            env = gym.make(TASK, cfg=env_cfg, render_mode=None)
            h = Harness(env, args_cli.ref, args_cli.num_substeps, clamp=not args_cli.no_clamp)
            callback(h)
            env.close()

    _main()


if __name__ == "__main__":
    if args_cli.check:
        run_with_harness(check)
    else:
        print("nothing to do: pass --check, or import run_with_harness from your own script")
