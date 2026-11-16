"""Summarise and plot the T17 traces (~/runs/traces/<task>_<train>_in_<eval>.npz).

For each cell it prints: how each env's first episode ended, the median step of the first `abnormal_robot`, the
3 joints that most often break the velocity condition (|joint_vel| > 2 * joint_vel_limit) at that step, and their
values there. abnormal_robot_state has only this one condition (dexsuite/mdp/terminations.py).

For each cross-engine cell it writes results/plots/trace_<cell>.png: for that cell's 3 joints, joint position target
vs actual over the recorded steps, for the same policy in both engines (env 0 of each trace). Joints are matched by
name: the two engines order them differently. Same seed, but the reset randomisation draws differ between engines, so
env 0 does not start from the same pose in both.

Run: scripts/run_isaac.sh plot_traces plot_traces.py [--task reorient] [--traces ~/runs/traces]
"""

import argparse
import os
from collections import Counter

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINES = ("physx", "newton")

parser = argparse.ArgumentParser()
parser.add_argument("--task", default="reorient")
parser.add_argument("--traces", default=os.path.expanduser("~/runs/traces"))
parser.add_argument("--plots", default=os.path.join(REPO, "results", "plots"))
args = parser.parse_args()


def load(train, ev):
    path = os.path.join(args.traces, f"{args.task}_{train}_in_{ev}.npz")
    return np.load(path, allow_pickle=False) if os.path.exists(path) else None


def summarise(cell, d):
    names = [str(n) for n in d["joint_names"]]
    ab = d["term_abnormal_robot"] > 0  # (steps, envs)
    steps, n_envs = ab.shape
    vlim = d["joint_vel_limits"]  # (envs, joints)
    first_ab = np.array([np.argmax(ab[:, e]) if ab[:, e].any() else -1 for e in range(n_envs)])
    term_names = [str(t) for t in d["term_names"]]
    fd = d["first_done_step"]
    reasons = Counter()
    for e in range(n_envs):
        s = int(fd[e])
        if s < 0:
            reasons["none within trace"] += 1
        else:
            reasons["+".join(t for t in term_names if d[f"term_{t}"][s, e] > 0) or "?"] += 1
    print(f"\n## {cell}  ({n_envs} envs, {steps} steps, dt {float(d['step_dt']):.4f} s)")
    print("first episode end:", dict(reasons))
    hit = first_ab >= 0
    # only count abnormal_robot when it ends the *first* episode
    first_ep = hit & (first_ab == fd)
    if not first_ep.any():
        print("abnormal_robot never ended a first episode")
        return None
    print(f"abnormal_robot ends first episode in {first_ep.sum()}/{n_envs} envs; step of first abnormal_robot: "
          f"median {np.median(first_ab[first_ep]):.0f}, min {first_ab[first_ep].min()}, max {first_ab[first_ep].max()}")
    breakers = Counter()
    rows = []
    for e in np.where(first_ep)[0]:
        s = first_ab[e]
        v = d["joint_vel"][s, e]
        ratio = np.abs(v) / vlim[e]
        for j in np.where(ratio > 2)[0]:
            breakers[j] += 1
        rows.append((e, s, ratio))
    top = [j for j, _ in breakers.most_common(3)]
    print("joints over 2x velocity limit at that step (count of envs):",
          ", ".join(f"{names[j]} {c}" for j, c in breakers.most_common(8)))
    for j in top:
        vals = [(e, s, d["joint_vel"][s, e, j], vlim[e, j], d["joint_pos"][s, e, j], d["joint_pos_target"][s, e, j],
                 d["applied_torque"][s, e, j]) for e, s, ratio in rows if ratio[j] > 2]  # envs where j breaks it
        med = np.median([[abs(x[2]), x[3], abs(x[2]) / x[3], abs(x[5] - x[4]), abs(x[6])] for x in vals], axis=0)
        lo, hi = d["soft_joint_pos_limits"][0, j]
        print(f"  {names[j]}: median at that step |vel| {med[0]:.2f} rad/s (limit {med[1]:.2f}, ratio {med[2]:.2f}), "
              f"|target-pos| {med[3]:.3f} rad, |applied torque| {med[4]:.2f} N·m; soft limits [{lo:.2f}, {hi:.2f}]")
    return [names[j] for j in top]


def plot(cell, train, top):
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib missing: install with scripts/pip_install.sh matplotlib")
        return
    traces = {ev: load(train, ev) for ev in ENGINES}
    # top holds joint *names*: PhysX and Newton order the joints differently, so map by name per trace
    fig, axes = plt.subplots(len(top), 1, figsize=(9, 2.6 * len(top)), sharex=True)
    axes = np.atleast_1d(axes)
    colours = {"physx": "tab:blue", "newton": "tab:orange"}
    for ax, jname in zip(axes, top):
        for ev, d in traces.items():
            if d is None:
                continue
            j = [str(n) for n in d["joint_names"]].index(jname)
            e = 0
            end = int(d["first_done_step"][e])
            n = d["joint_pos"].shape[0] if end < 0 else end + 1
            t = np.arange(n)
            ax.plot(t, d["joint_pos"][:n, e, j], color=colours[ev], label=f"{ev}: actual")
            ax.plot(t, d["joint_pos_target"][:n, e, j], color=colours[ev], ls="--", label=f"{ev}: target")
            if end >= 0:
                ax.axvline(end, color=colours[ev], ls=":", lw=1)
        ax.set_ylabel(f"{jname} [rad]")
        ax.grid(alpha=0.3)
    axes[0].legend(fontsize=8, ncol=2)
    axes[0].set_title(f"{args.task}: {train} policy, env 0, joint target vs actual (dotted: episode end)")
    axes[-1].set_xlabel("control step")
    fig.tight_layout()
    os.makedirs(args.plots, exist_ok=True)
    out = os.path.join(args.plots, f"trace_{cell}.png")
    fig.savefig(out, dpi=120)
    print(f"wrote {out}")


for train in ENGINES:
    for ev in ENGINES:
        d = load(train, ev)
        cell = f"{args.task}_{train}_in_{ev}"
        if d is None:
            print(f"\n## {cell}: no trace")
            continue
        top = summarise(cell, d)
        if top and ev != train:
            plot(cell, train, top)
