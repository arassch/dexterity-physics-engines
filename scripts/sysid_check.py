"""T20 step 1: sanity checks of Sara's T19 fit (results/sysid_robot.json). Newton only, harness only, no policy.

1. step response (signal a): PhysX vs default Newton vs fitted Newton, per finger joint: rise time (10-90 %),
   overshoot, steady-state error. "default Newton" = the harness defaults, i.e. WITH T19's fixed corrections
   (per-physics-step finger velocity clamp, num_substeps 8) but nominal finger parameters; "fitted" adds the json's
   `best` parameters. Table -> results/sysid_check.md, plots of 3 joints -> results/plots/sysid_step_<joint>.png.
2. held-out episodes: signal (c) replays T17 trace episodes (the PhysX reference's `c_trace_env`). Rerun Sara's grid
   search (make_grid, refine_grid, score_candidate, choose_best from scripts/sysid_fit.py, unchanged) scoring only
   the reference envs whose (c) episode is one of the first 10 (sorted) episodes, then count the blow-ups of that best
   point on the reference envs of the other 5 episodes. Same rollouts as sysid_fit.py (each candidate on all 64
   references); only the env subset passed to score_candidate differs. Signals (a) and (b) of the same reference envs
   are in the subset too (score_candidate scores all three signals on one env set).

Run (Newton only, 1,024 envs = 16 candidates per call, ~23 calls):
    scripts/run_isaac.sh sysid_check sysid_check.py --headless --num_envs 1024 physics=newton_mjwarp presets=cube
Smoke: add --smoke (coarse grid 2 per axis, fine grid 2 per axis) and use --num_envs 128.
"""

import argparse
import json
import os
import sys
import time

_p = argparse.ArgumentParser(add_help=False)
_p.add_argument("--smoke", action="store_true")
_p.add_argument("--n_train_episodes", type=int, default=10)
_own, _rest = _p.parse_known_args()
sys.argv = [sys.argv[0]] + _rest

import numpy as np  # noqa: E402

from sysid_fit import PARAM_NAMES, REFS, choose_best, make_grid, refine_grid, score_candidate  # noqa: E402
from sysid_harness import args_cli, run_with_harness  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIT_JSON = os.path.join(REPO, "results", "sysid_robot.json")
OUT_MD = os.path.join(REPO, "results", "sysid_check.md")
OUT_JSON = os.path.join(REPO, "results", "sysid_check.json")
PLOTS = os.path.join(REPO, "results", "plots")
if _own.smoke:
    OUT_MD = os.path.expanduser("~/runs/sysid_check_smoke.md")
    OUT_JSON = os.path.expanduser("~/runs/sysid_check_smoke.json")
    PLOTS = os.path.expanduser("~/runs/sysid_check_smoke_plots")


def _f(v):
    return float(v) if np.ndim(v) == 0 else np.asarray(v).tolist()


# ------------------------------------------------------------------------------------------------ step response
def step_metrics(q, q0, tgt, dt):
    """q (T, E) positions of the stepped joint; q0, tgt (E,). Mean normalised response, as analyze_step_response.py."""
    x = (q - q0[None]) / (tgt - q0)[None]
    xm = x.mean(axis=1)
    t = (np.arange(len(xm)) + 1) * dt

    def first(th):
        idx = np.where(xm >= th)[0]
        return t[idx[0]] if len(idx) else np.nan

    rise = first(0.9) - first(0.1)
    over = max(0.0, float(xm.max()) - 1.0) * 100
    sse = float(np.abs(q[-10:] - tgt[None]).mean())
    return dict(rise=float(rise), over=over, sse=sse, curve=xm)


def step_check(out, ref, blocks, dt):
    """blocks: {"default": envs, "fitted": envs}. Signal a is index 0."""
    names = out["joint_names"]
    finger = out["finger"]
    a_joint = ref["a_joint"][out["ref_env"]]          # physx-order joint stepped by each env
    q0_all = ref["default_joint_pos"][out["ref_env"]]  # (N, 23) physx order
    tgt_all = out["target"][:, 0, -1]                  # (N, 23)
    rows = []
    for j in np.where(finger)[0]:
        row = dict(joint=str(names[j]))
        for label, envs in blocks.items():
            sel = envs[(a_joint[envs] == j) & ~out["physx_reset"][envs, 0]]
            ok = sel[~out["reset"][sel, 0]]
            if label == "default":  # PhysX reference for the same reference envs
                row["physx"] = step_metrics(out["physx_joint_pos"][sel, 0, :, j].T, q0_all[sel, j], tgt_all[sel, j], dt) \
                    if len(sel) else None
            row[label] = step_metrics(out["joint_pos"][ok, 0, :, j].T, q0_all[ok, j], tgt_all[ok, j], dt) \
                if len(ok) else None
            row[f"{label}_n"] = (len(ok), len(sel))
        rows.append(row)
    return rows


def plot_steps(rows, dt, picks):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(PLOTS, exist_ok=True)
    paths = []
    for r in rows:
        if r["joint"] not in picks:
            continue
        fig, ax = plt.subplots(figsize=(6, 3.5))
        for key, lab, ls in (("physx", "PhysX (reference)", "-"), ("default", "Newton default (clamp + 8 substeps)", "--"),
                             ("fitted", "Newton fitted", "-.")):
            if r.get(key) is not None:
                c = r[key]["curve"]
                ax.plot((np.arange(len(c)) + 1) * dt, c, ls, label=lab)
        ax.axhline(1.0, color="grey", lw=0.5)
        ax.set_xlabel("time (s)")
        ax.set_ylabel("normalised position (1 = target)")
        ax.set_title(f"{r['joint']}: +0.3 rad step (signal a), mean over envs")
        ax.legend(fontsize=8)
        fig.tight_layout()
        p = os.path.join(PLOTS, f"sysid_step_{r['joint']}.png")
        fig.savefig(p, dpi=120)
        plt.close(fig)
        paths.append(p)
    return paths


# ------------------------------------------------------------------------------------------------ held-out search
def blowups_per_signal(out, envs):
    valid = ~out["physx_reset"][envs]
    return [int((out["reset"][envs, s] & valid[:, s]).sum()) for s in range(3)]


def evaluate_split(h, candidates, train_off, held_off, level, first_out_cb=None):
    """Like sysid_fit.evaluate, but each candidate is scored on two subsets of its 64 reference envs."""
    k_per_call = h.n // REFS
    assert k_per_call >= 1 and h.n % REFS == 0, f"num_envs must be a multiple of {REFS}, got {h.n}"
    rows = []
    for start in range(0, len(candidates), k_per_call):
        batch = candidates[start:start + k_per_call]
        params = np.repeat(np.asarray(batch, np.float32), REFS, axis=0)
        if len(params) < h.n:
            params = np.concatenate([params, h.default_params()[: h.n - len(params)]], 0)
        t0 = time.time()
        out = h.rollout(params)
        if first_out_cb is not None and start == 0:
            level = first_out_cb(out)
        for j, p in enumerate(batch):
            tr, he = j * REFS + train_off, j * REFS + held_off
            st = score_candidate(out, tr, out["finger"], penalty_level=level)
            sh = score_candidate(out, he, out["finger"], penalty_level=level)
            rows.append({**dict(zip(PARAM_NAMES, map(float, p))),
                         **{k: _f(v) for k, v in st.items()},
                         **{f"held_{k}": _f(v) for k, v in sh.items()},
                         "held_blowups_abc": blowups_per_signal(out, he),
                         "train_blowups_abc": blowups_per_signal(out, tr)})
        print(f"[CHECK] candidates {start}-{start + len(batch) - 1}/{len(candidates)} in {time.time() - t0:.0f} s; "
              f"best so far (train): {choose_best(rows)}", flush=True)
    return rows, level


# ------------------------------------------------------------------------------------------------ main
def run(h):
    fit = json.load(open(FIT_JSON))
    fitted = np.array([fit["best"][n] for n in PARAM_NAMES], np.float32)
    default = h.default_params()[0]
    ref = np.load(args_cli.ref)
    dt = float(ref["step_dt"])
    lo, hi = h.param_bounds()
    print(f"[CHECK] {h.n} envs; default {default}; fitted (sysid_robot.json best) {fitted}", flush=True)

    # episode split over the 64 reference envs
    ep = np.asarray(ref["c_trace_env"])[:REFS]
    eps = np.unique(ep)
    train_eps, held_eps = eps[:_own.n_train_episodes], eps[_own.n_train_episodes:]
    train_off = np.where(np.isin(ep, train_eps))[0]
    held_off = np.where(np.isin(ep, held_eps))[0]
    print(f"[CHECK] {len(eps)} trace episodes {eps.tolist()}; train {train_eps.tolist()} ({len(train_off)} ref envs), "
          f"held-out {held_eps.tolist()} ({len(held_off)} ref envs)", flush=True)
    assert len(held_off) > 0

    # call 1: [default, fitted]: the step-response check, and the default run's penalty level on the train subset
    state = {}

    def first(out):
        state["step_rows"] = step_check(out, ref, {"default": np.arange(0, REFS), "fitted": np.arange(REFS, 2 * REFS)}, dt)
        base = score_candidate(out, train_off, out["finger"])
        print(f"[CHECK] default on train subset (level from survivors): {base}", flush=True)
        return base["level"]

    base_rows, level = evaluate_split(h, [default, fitted], train_off, held_off, None, first_out_cb=first)
    n_coarse, n_fine = (2, 2) if _own.smoke else (6, 5)
    coarse, _ = evaluate_split(h, make_grid(lo, hi, n_coarse), train_off, held_off, level)
    best = choose_best(coarse)
    print(f"[CHECK] coarse best (train): {best}", flush=True)
    fine, _ = evaluate_split(h, refine_grid(np.array([best[n] for n in PARAM_NAMES]), lo, hi, n_fine, 0.33),
                             train_off, held_off, level)
    best = choose_best(coarse + fine)
    print(f"[CHECK] final best (train): {best}", flush=True)

    rows = state["step_rows"]
    sr = [r for r in rows if r["physx"] and r["default"] and r["fitted"]]
    picks = sorted(sr, key=lambda r: -np.sqrt(np.mean((r["fitted"]["curve"] - r["physx"]["curve"]) ** 2)))[:3]
    plots = plot_steps(rows, dt, {r["joint"] for r in picks})

    def m(r, k, f):
        return "–" if r.get(k) is None or np.isnan(r[k][f]) else f"{r[k][f]:.3f}" if f != "over" else f"{r[k][f]:.1f}"

    mean = {k: {f: float(np.nanmean([r[k][f] for r in sr])) for f in ("rise", "over", "sse")}
            for k in ("physx", "default", "fitted")}
    L = ["# T20 step 1 · Sanity checks of the T19 fit",
         "",
         f"Generated by `scripts/sysid_check.py` ({h.n} envs, Newton, num_substeps {h.num_substeps}, clamp {h.clamp} "
         f"({h.clamp_mode}), ADR max, cube parked). Reference: `{os.path.basename(args_cli.ref)}` (PhysX, ADR max).",
         f"Fitted = `results/sysid_robot.json` best: armature {fitted[0]:.4f}, damping_scale {fitted[1]:.3f}, "
         f"effort_scale {fitted[2]:.3f}. Default = armature {default[0]:.4f}, scales 1.0 (with the fixed corrections).",
         "",
         "## 1. Step response, signal (a): +0.3 rad on one joint (others held), 120 steps",
         "",
         "Per finger joint, the mean normalised response over the reference envs that stepped it (PhysX: envs whose "
         "PhysX reference didn't reset; Newton: those of them that didn't reset either). Rise time 10–90 % (s), "
         "overshoot (% of the step), steady-state error (mean |q − target| over the last 10 steps, rad). "
         "n = Newton envs used / envs that stepped the joint.",
         "",
         "| joint | rise PhysX | rise default | rise fitted | overshoot PhysX | overshoot default | overshoot fitted "
         "| sse PhysX | sse default | sse fitted | n default | n fitted |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['joint']} | {m(r, 'physx', 'rise')} | {m(r, 'default', 'rise')} | {m(r, 'fitted', 'rise')} | "
                 f"{m(r, 'physx', 'over')} | {m(r, 'default', 'over')} | {m(r, 'fitted', 'over')} | "
                 f"{m(r, 'physx', 'sse')} | {m(r, 'default', 'sse')} | {m(r, 'fitted', 'sse')} | "
                 f"{r['default_n'][0]}/{r['default_n'][1]} | {r['fitted_n'][0]}/{r['fitted_n'][1]} |")
    L.append(f"| **mean ({len(sr)} joints)** | {mean['physx']['rise']:.3f} | {mean['default']['rise']:.3f} | "
             f"{mean['fitted']['rise']:.3f} | {mean['physx']['over']:.1f} | {mean['default']['over']:.1f} | "
             f"{mean['fitted']['over']:.1f} | {mean['physx']['sse']:.3f} | {mean['default']['sse']:.3f} | "
             f"{mean['fitted']['sse']:.3f} | | |")
    L += ["", "Plots (the 3 finger joints whose fitted curve is furthest from PhysX's, RMS of the normalised curves): "
          + ", ".join(f"`results/plots/{os.path.basename(p)}`" for p in plots), ""]

    L += ["## 2. Held-out episodes (signal c)",
          "",
          f"Signal (c) replays {len(eps)} T17 trace episodes over the 64 references (`c_trace_env`). Train = episodes "
          f"{train_eps.tolist()} ({len(train_off)} reference envs), held-out = {held_eps.tolist()} "
          f"({len(held_off)} reference envs). Sara's grid search ({n_coarse}³ coarse + {n_fine}³ fine, her functions "
          f"unchanged) scored on the train envs only; penalty level from the default run on the train envs "
          f"({level:.4f}). Blow-ups = Newton resets over the three signals in those envs, excluding pairs where "
          "PhysX itself reset.",
          "",
          "| parameters | armature | damping_scale | effort_scale | train loss | train blow-ups (a/b/c) | "
          "held-out loss | held-out blow-ups (a/b/c) |",
          "|---|---|---|---|---|---|---|---|"]
    for lab, r in (("default", base_rows[0]), ("full fit (sysid_robot.json)", base_rows[1]),
                   ("best on train episodes", best)):
        L.append(f"| {lab} | {r['armature']:.4f} | {r['damping_scale']:.3f} | {r['effort_scale']:.3f} | "
                 f"{r['loss']:.4f} | {r['blowups']} ({'/'.join(map(str, r['train_blowups_abc']))}) | "
                 f"{r['held_loss']:.4f} | {r['held_blowups']} ({'/'.join(map(str, r['held_blowups_abc']))}) |")
    L += ["", f"Max possible blow-ups: train {3 * len(train_off)}, held-out {3 * len(held_off)} (minus PhysX resets).",
          f"Grid rows (train and held-out scores for every candidate): `results/{os.path.basename(OUT_JSON)}`.", ""]
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    open(OUT_MD, "w").write("\n".join(L))
    json.dump({"train_episodes": train_eps.tolist(), "held_episodes": held_eps.tolist(), "penalty_level": level,
               "default": base_rows[0], "full_fit": base_rows[1], "best_train": best, "coarse": coarse, "fine": fine,
               "step_mean": mean,
               "step": [{k: (v if k in ("joint", "default_n", "fitted_n") else
                             (None if v is None else {f: _f(x) for f, x in v.items()}))
                         for k, v in r.items()} for r in rows]},
              open(OUT_JSON, "w"), indent=1)
    print(f"[CHECK] step means: {mean}", flush=True)
    print(f"[CHECK] wrote {OUT_MD}, {OUT_JSON}, plots {plots}", flush=True)


if __name__ == "__main__":
    run_with_harness(run)
