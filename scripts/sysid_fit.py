"""T19 system-ID fit: find Newton finger parameters that make Newton's hand move like PhysX's ("the real hand").

Design (Sara, notes/log.md 16 Nov 18:20). Open loop, no policy: both engines get the same recorded joint-target
sequences; we compare Newton's finger motion with PhysX's (not with the targets).

Search: a log-spaced grid over [armature, damping_scale, effort_scale], then a finer grid around the best point.
Each candidate is scored on ALL 64 PhysX references: the harness runs 64 * K envs and env i replays reference
i mod 64, so the envs [64k, 64k + 64) all get candidate k's parameters.

Run (Newton only, ~1 min per batch of K candidates, to be measured):
    scripts/run_isaac.sh sysid_fit sysid_fit.py --headless --num_envs 1024 physics=newton_mjwarp presets=cube

make_grid, refine_grid, score_candidate and choose_best are Sara's (marked SARA). Everything else is plumbing.
"""

import json
import os
import time

import numpy as np

from sysid_harness import SIGNALS, run_with_harness

REFS = 64                      # PhysX references per candidate (the harness's ref_env = i mod 64)
OUT_JSON = os.path.join(os.path.dirname(__file__), "..", "results", "sysid_robot.json")
PARAM_NAMES = ("armature", "damping_scale", "effort_scale")


# ---------------------------------------------------------------------------------------------- SARA: the grid
def make_grid(lo, hi, n_per_axis=6):
    """Return an array (M, 3) of candidate parameter rows covering [lo, hi] on each axis.

    lo, hi: arrays of shape (3,), from the harness's param_bounds().
    Log spacing (each point a fixed multiple of the previous one), n_per_axis points per axis
    (endpoints included), all combinations, so M = n_per_axis ** 3 (216 for the default of 6).
    Bounds must be > 0.
    """
    lo = np.asarray(lo, dtype=float)
    hi = np.asarray(hi, dtype=float)
    axes = [np.geomspace(lo[i], hi[i], n_per_axis) for i in range(3)]
    mesh = np.meshgrid(*axes, indexing="ij")
    return np.stack(mesh, axis=-1).reshape(-1, 3)


def refine_grid(best, lo, hi, n_per_axis, shrink):
    """Return a finer grid (M, 3) centred on `best` (shape (3,)).

    For each axis, span [best / f, best * f] with f = (hi / lo) ** (shrink / 2), clipped to [lo, hi],
    log-spaced with n_per_axis points. shrink = 0.33 means a third of the original (log) range.
    """
    best = np.asarray(best, dtype=float)
    lo = np.asarray(lo, dtype=float)
    hi = np.asarray(hi, dtype=float)
    f = (hi / lo) ** (shrink / 2)                    # per-axis multiplicative half-width
    new_lo = np.clip(best / f, lo, hi)
    new_hi = np.clip(best * f, lo, hi)
    axes = [np.geomspace(new_lo[i], new_hi[i], n_per_axis) for i in range(3)]
    mesh = np.meshgrid(*axes, indexing="ij")
    return np.stack(mesh, axis=-1).reshape(-1, 3)


# ---------------------------------------------------------------------------------------------- SARA: the loss
def score_candidate(out, envs, finger, pos_scale=0.3, vel_scale=6.283, w_vel=1.0,
                    signal_weights=(1.0, 1.0, 3.0), penalty_factor=2.0, penalty_level=None):
    """Score ONE candidate from the rollout dict `out`, using only the env indices in `envs` (its 64 envs).

    Arrays in `out` (N = all envs, S = 3 signals, T = steps, J = 23 joints in PhysX order):
      joint_pos, joint_vel                (N, S, T, J)  Newton
      physx_joint_pos, physx_joint_vel    (N, S, T, J)  PhysX reference for the same env
      reset_step (N, S)  first step at which that Newton env reset, -1 if it never did
      physx_reset (N, S) True where the PhysX reference itself reset: leave those env/signal pairs out
    finger: (J,) bool, the 16 finger joints.

    Return a dict with at least:
      "loss"      float, the number the grid search minimises
      "blowups"   int, Newton resets over the 3 signals in these envs (excluding physx_reset pairs)
      "rms_a", "rms_b", "rms_c"   tracking error per signal (normalised units), for the table

    The design:
      error per env and signal = RMS over finger joints and over steps BEFORE reset_step of
          (pos error / pos_scale)  and  w_vel * (vel error / vel_scale)  (e.g. sqrt of the mean of both squared)
      blow-up penalty per env and signal = penalty_factor * (worst error of a surviving env)
          * (steps left after the reset / T)          -> early blow-ups cost more
      loss = weighted mean over signals (signal_weights for a, b, c) of the per-signal mean over envs
             of (error + penalty)
    Choose for yourself how to define "worst error of a surviving env" (e.g. the 95th percentile of the errors
    of the envs that didn't reset, in this batch or from the default-parameter run).
    """
    finger = np.asarray(finger, dtype=bool)
    dp = (out["joint_pos"][envs][..., finger] - out["physx_joint_pos"][envs][..., finger]) / pos_scale
    dv = w_vel * (out["joint_vel"][envs][..., finger] - out["physx_joint_vel"][envs][..., finger]) / vel_scale
    sq = (dp ** 2 + dv ** 2).mean(axis=-1)                        # (E, S, T): mean over finger joints
    T = sq.shape[-1]

    reset_step = np.asarray(out["reset_step"])[envs]              # (E, S)
    reset = reset_step >= 0
    valid = ~np.asarray(out["physx_reset"])[envs].astype(bool)    # drop pairs where PhysX itself reset

    # RMS over the steps before the reset (all T steps if it never reset)
    alive = np.arange(T)[None, None, :] < np.where(reset, reset_step, T)[..., None]
    n_alive = alive.sum(axis=-1)
    err = np.sqrt(np.where(alive, sq, 0.0).sum(axis=-1) / np.maximum(n_alive, 1))   # (E, S)

    # "worst error of a surviving env" (the penalty yardstick): use penalty_level if given (fit() passes the
    # default run's "level" to every other candidate); otherwise the 95th percentile over this batch's survivors
    # (falls back to all valid pairs, then 0, if nobody survived)
    if penalty_level is not None:
        worst = penalty_level
    else:
        survivors = valid & ~reset
        ref = err[survivors] if survivors.any() else err[valid] if valid.any() else np.zeros(1)
        worst = np.percentile(ref, 95)

    # early blow-ups cost more: scaled by the fraction of steps left after the reset
    penalty = np.where(reset, penalty_factor * worst * (T - reset_step) / T, 0.0)
    total = err + penalty

    per_signal_loss = np.array([total[valid[:, s], s].mean() if valid[:, s].any() else 0.0
                                for s in range(total.shape[1])])
    per_signal_err = np.array([err[valid[:, s], s].mean() if valid[:, s].any() else 0.0
                               for s in range(err.shape[1])])
    w = np.asarray(signal_weights, dtype=float)
    return {
        "loss": float((w * per_signal_loss).sum() / w.sum()),
        "level": float(worst),
        "blowups": int((reset & valid).sum()),
        "rms_a": float(per_signal_err[0]),
        "rms_b": float(per_signal_err[1]),
        "rms_c": float(per_signal_err[2]),
    }


def choose_best(rows):
    """Pick the winner from the list of result rows (each: params + score_candidate's dict).

    The design: fewest blow-ups first, then the lowest loss among those. Return the chosen row.
    """
    raise NotImplementedError("SARA: choose_best")


# ---------------------------------------------------------------------------------------------- plumbing
def evaluate(h, candidates, penalty_level=None):
    """Run every candidate on all REFS references, K = h.n // REFS candidates per rollout call.

    penalty_level: the blow-up penalty yardstick, the same for every candidate (the default run's "level").
    """
    k_per_call = h.n // REFS
    assert k_per_call >= 1 and h.n % REFS == 0, f"num_envs must be a multiple of {REFS}, got {h.n}"
    rows = []
    for start in range(0, len(candidates), k_per_call):
        batch = candidates[start:start + k_per_call]
        params = np.repeat(np.asarray(batch, np.float32), REFS, axis=0)
        if len(params) < h.n:  # pad the last call with copies of the defaults; their scores are ignored
            pad = h.default_params()[: h.n - len(params)]
            params = np.concatenate([params, pad], 0)
        t0 = time.time()
        out = h.rollout(params)
        for j, p in enumerate(batch):
            envs = np.arange(j * REFS, (j + 1) * REFS)
            s = score_candidate(out, envs, out["finger"], penalty_level=penalty_level)
            rows.append({**dict(zip(PARAM_NAMES, map(float, p))), **{k: _f(v) for k, v in s.items()}})
        print(f"[FIT] candidates {start}-{start + len(batch) - 1}/{len(candidates)} in {time.time() - t0:.0f} s; "
              f"best so far: {min(rows, key=lambda r: r['loss'])}")
    return rows


def _f(v):
    return float(v) if np.ndim(v) == 0 else np.asarray(v).tolist()


def fit(h):
    lo, hi = h.param_bounds()
    default = h.default_params()[0]
    print(f"[FIT] {h.n} envs = {h.n // REFS} candidates per call; bounds {lo} .. {hi}; default {default}")

    base = evaluate(h, [default])[0]
    level = base["level"]  # penalty yardstick from the default run, used for every candidate after it
    print(f"[FIT] default parameters: {base}; penalty level for all candidates: {level:.4f}")

    coarse = evaluate(h, make_grid(lo, hi, 6), level)
    best = choose_best(coarse)
    print(f"[FIT] coarse best: {best}")

    fine = evaluate(h, refine_grid(np.array([best[n] for n in PARAM_NAMES]), lo, hi, 5, 0.33), level)
    best = choose_best(coarse + fine)
    print(f"[FIT] final best: {best}")

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump({"param_names": PARAM_NAMES, "best": best, "default": base,
                   "penalty_level": level, "coarse": coarse, "fine": fine, "num_substeps": h.num_substeps,
                   "clamp": f"{h.clamp} ({h.clamp_mode})", "signals": SIGNALS}, f, indent=1)
    print(f"[FIT] wrote {OUT_JSON}")


if __name__ == "__main__":
    run_with_harness(fit)
