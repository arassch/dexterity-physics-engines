"""T26: how noisy are the system-ID blow-up counts? Newton only, harness only, no policy.

4 candidates (default; Sara's full fit = results/sysid_robot.json best; T20's train-episodes best =
results/sysid_check.json best_train; one grid point with 0 blow-ups in both T19 and T20, the lowest T19 loss among
them). With 1,024 envs each candidate gets 4 blocks of 64 envs (same params, same 64 references, different env
indices) in one rollout() call; the same params array is rolled out in 5 separate calls. Every block is scored with
Sara's score_candidate (unchanged, imported from sysid_fit.py), penalty level fixed to the default candidate's first
block in call 1.

Reports within-call noise (the 4 blocks of one call), between-call noise (the same block over 5 calls), and whether
identical inputs give bit-identical outputs (joint_pos, reset_step): block vs block in one call, call vs call for the
same block.

Run:    scripts/run_isaac.sh sysid_repeat sysid_repeat.py --headless --num_envs 1024 physics=newton_mjwarp presets=cube
Smoke:  add --smoke --calls 2 and use --num_envs 512 (2 blocks per candidate); writes to ~/runs/.
"""

import argparse
import json
import os
import sys
import time

_p = argparse.ArgumentParser(add_help=False)
_p.add_argument("--smoke", action="store_true")
_p.add_argument("--calls", type=int, default=5)
_p.add_argument("--tag", type=str, default="", help="T26b: output results/sysid_repeat_<tag>.{md,json}")
_own, _rest = _p.parse_known_args()
sys.argv = [sys.argv[0]] + _rest

import numpy as np  # noqa: E402

from sysid_fit import PARAM_NAMES, REFS, score_candidate  # noqa: E402
from sysid_harness import run_with_harness  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIT_JSON = os.path.join(REPO, "results", "sysid_robot.json")
CHECK_JSON = os.path.join(REPO, "results", "sysid_check.json")
_sfx = f"_{_own.tag}" if _own.tag else ""
OUT_MD = os.path.join(REPO, "results", f"sysid_repeat{_sfx}.md")
OUT_JSON = os.path.join(REPO, "results", f"sysid_repeat{_sfx}.json")
if _own.smoke:
    OUT_MD = os.path.expanduser("~/runs/sysid_repeat_smoke.md")
    OUT_JSON = os.path.expanduser("~/runs/sysid_repeat_smoke.json")
KEYS = ("blowups", "loss", "rms_a", "rms_b", "rms_c")


def _key(r):
    return tuple(round(float(r[p]), 5) for p in PARAM_NAMES)


def pick_candidates(default):
    fit = json.load(open(FIT_JSON))
    chk = json.load(open(CHECK_JSON))
    t19 = {_key(r): r for r in fit["coarse"] + fit["fine"]}
    both = []
    for r in chk["coarse"] + chk["fine"]:
        k = _key(r)
        if k in t19 and t19[k]["blowups"] == 0 and r["blowups"] + r["held_blowups"] == 0:
            both.append((t19[k]["loss"], k, [float(t19[k][p]) for p in PARAM_NAMES]))
    both.sort(key=lambda x: x[0])
    print(f"[REPEAT] {len(both)} grid points with 0 blow-ups in both T19 and T20; lowest T19 loss: {[b[:2] for b in both[:3]]}",
          flush=True)
    assert both, "no grid point with 0 blow-ups in both runs"
    row = lambda r: [float(r[p]) for p in PARAM_NAMES]  # noqa: E731
    return [("default", [float(x) for x in default]),
            ("full fit (T19 best)", row(fit["best"])),
            ("T20 train-episodes best", row(chk["best_train"])),
            ("0 blow-ups in T19 and T20", both[0][2])]


def stats(v):
    v = np.asarray(v, float)
    return dict(mean=float(v.mean()), std=float(v.std()), min=float(v.min()), max=float(v.max()))


def run(h):
    cands = pick_candidates(h.default_params()[0])
    C = len(cands)
    B = h.n // (REFS * C)
    assert B >= 2 and h.n == B * C * REFS, f"num_envs must be {C} x 64 x (>=2), got {h.n}"
    params = np.repeat(np.asarray([p for _, p in cands], np.float32), B * REFS, axis=0)
    print(f"[REPEAT] {h.n} envs: {C} candidates x {B} blocks x {REFS} envs, {_own.calls} calls", flush=True)
    for name, p in cands:
        print(f"[REPEAT]   {name}: {dict(zip(PARAM_NAMES, p))}", flush=True)

    def block_envs(c, b):
        return np.arange((c * B + b) * REFS, (c * B + b + 1) * REFS)

    scores = np.zeros((_own.calls, C, B, len(KEYS)))
    abc = np.zeros((_own.calls, C, B, 3), int)
    abn = np.zeros((_own.calls, C, B), int)
    level = None
    same_in_call = {}   # (call, c, b) -> (joint_pos equal to block 0, reset_step equal to block 0)
    same_across = {}    # (call, c, b) -> equal to call 0, same block
    first = None
    adr_calls = []
    for call in range(_own.calls):
        t0 = time.time()
        out = h.rollout(params)
        adr_calls.append(out["adr"])
        if level is None:
            level = score_candidate(out, block_envs(0, 0), out["finger"])["level"]
        for c in range(C):
            e0 = block_envs(c, 0)
            for b in range(B):
                e = block_envs(c, b)
                s = score_candidate(out, e, out["finger"], penalty_level=level)
                scores[call, c, b] = [float(s[k]) for k in KEYS]
                valid = ~out["physx_reset"][e]
                abc[call, c, b] = [int((out["reset"][e, si] & valid[:, si]).sum()) for si in range(3)]
                abn[call, c, b] = int((out["abnormal"][e] & valid).sum())  # T26b: resets by abnormal_robot only
                same_in_call[(call, c, b)] = (bool(np.array_equal(out["joint_pos"][e], out["joint_pos"][e0])),
                                              bool(np.array_equal(out["reset_step"][e], out["reset_step"][e0])))
                if first is not None:
                    same_across[(call, c, b)] = (bool(np.array_equal(out["joint_pos"][e], first["joint_pos"][e])),
                                                 bool(np.array_equal(out["reset_step"][e], first["reset_step"][e])))
        if first is None:
            first = {"joint_pos": out["joint_pos"].copy(), "reset_step": out["reset_step"].copy()}
        print(f"[REPEAT] call {call + 1}/{_own.calls} in {time.time() - t0:.0f} s; blow-ups per block: "
              + "; ".join(f"{cands[c][0]}: {scores[call, c, :, 0].astype(int).tolist()}" for c in range(C))
              + " | of which abnormal_robot: " + "; ".join(f"{abn[call, c].tolist()}" for c in range(C)), flush=True)
        del out

    res = []
    for c, (name, p) in enumerate(cands):
        r = dict(name=name, params=dict(zip(PARAM_NAMES, p)))
        for ki, k in enumerate(KEYS):
            v = scores[:, c, :, ki]                                  # (calls, blocks)
            r[k] = dict(within_call1=stats(v[0]),                    # 4 blocks of call 1
                        within_std_mean=float(v.std(axis=1).mean()),  # mean over calls of the std over blocks
                        between_block0=stats(v[:, 0]),               # block 0 over the calls
                        between_std_mean=float(v.std(axis=0).mean()),  # mean over blocks of the std over calls
                        all=stats(v.ravel()), values=v.tolist())
        r["blowups_abc"] = abc[:, c].tolist()
        r["abnormal_robot"] = abn[:, c].tolist()
        r["identical_in_call"] = [[list(same_in_call[(k, c, b)]) for b in range(B)] for k in range(_own.calls)]
        r["identical_across_calls"] = [[list(same_across[(k, c, b)]) for b in range(B)] for k in range(1, _own.calls)]
        res.append(r)

    n_in = sum(1 for (k, c, b), v in same_in_call.items() if b > 0 and all(v))
    n_in_tot = sum(1 for (k, c, b) in same_in_call if b > 0)
    n_ac = sum(1 for v in same_across.values() if all(v))
    n_ac_tot = len(same_across)
    print(f"[REPEAT] bit-identical (joint_pos and reset_step): blocks vs block 0 in a call {n_in}/{n_in_tot}; "
          f"call vs call 1, same block {n_ac}/{n_ac_tot}", flush=True)

    L = ["# T26 · How noisy are the system-ID blow-up counts?", "",
         f"Generated by `scripts/sysid_repeat.py` ({h.n} envs, Newton, num_substeps {h.num_substeps}, clamp {h.clamp} "
         f"({h.clamp_mode}), ADR max, cube parked, all {REFS} PhysX references). Each candidate gets {B} blocks of "
         f"{REFS} envs per `rollout()` call (same params, same references, different env indices); the same params "
         f"array is rolled out in {_own.calls} separate calls. Scores: Sara's `score_candidate`, unchanged; penalty "
         f"level fixed at {level:.4f} (default candidate, block 1, call 1). Blow-ups = Newton resets over the 3 "
         f"signals, excluding pairs where PhysX reset (max {3 * REFS}).", "",
         "## Candidates", "", "| candidate | armature | damping_scale | effort_scale |", "|---|---|---|---|"]
    for r in res:
        p = r["params"]
        L.append(f"| {r['name']} | {p['armature']:.4f} | {p['damping_scale']:.3f} | {p['effort_scale']:.3f} |")
    L += ["", "## Blow-ups", "",
          f"Within call = the {B} blocks of call 1 (mean ± std, min–max); mean within std = std over blocks, averaged "
          f"over the {_own.calls} calls. Between calls = block 1 over the {_own.calls} calls; mean between std = std "
          f"over calls, averaged over blocks. All = all {B * _own.calls} block scores.", "",
          "| candidate | within call 1 | mean within std | between calls (block 1) | mean between std | all |",
          "|---|---|---|---|---|---|"]

    def fmt(s, d):
        return f"{s['mean']:.{d}f} ± {s['std']:.{d}f} ({s['min']:.{d}f}–{s['max']:.{d}f})"

    for k, d in (("blowups", 1), ("loss", 4)):
        if k == "loss":
            L += ["", "## Loss", "", L[-(C + 2)], L[-(C + 1)]]
        for r in res:
            x = r[k]
            L.append(f"| {r['name']} | {fmt(x['within_call1'], d)} | {x['within_std_mean']:.{d + 1}f} | "
                     f"{fmt(x['between_block0'], d)} | {x['between_std_mean']:.{d + 1}f} | {fmt(x['all'], d)} |")
    L += ["", "## Every block's blow-ups (rows = calls, columns = blocks)", ""]
    for r in res:
        L.append(f"- {r['name']}: " + " · ".join("/".join(str(int(x)) for x in row) for row in r["blowups"]["values"])
                 + "  (of which abnormal_robot: " + " · ".join("/".join(str(x) for x in row) for row in r["abnormal_robot"])
                 + ")")
    L += ["", "## Bit-identical outputs (joint_pos and reset_step arrays)", "",
          f"- Within a call, block b vs block 1 of the same candidate: **{n_in}/{n_in_tot}** identical.",
          f"- Across calls, the same candidate and block vs call 1: **{n_ac}/{n_ac_tot}** identical.", "",
          f"## ADR state at the start of each signal (freeze_adr={h.freeze_adr})", "",
          "| call | signal | ADR mean | ADR min–max | difficulty_frac | gravity z applied (mean, min–max) |",
          "|---|---|---|---|---|---|"]
    for k, sts in enumerate(adr_calls):
        for s, st in zip(("a", "b", "c"), sts):
            g = lambda x: st.get(x, float("nan"))  # noqa: E731
            L.append(f"| {k + 1} | {s} | {g('adr_mean'):.2f} | {g('adr_min'):.0f}–{g('adr_max'):.0f} | "
                     f"{g('adr_frac'):.3f} | {g('g_z_mean'):.2f} ({g('g_z_min'):.2f}–{g('g_z_max'):.2f}) |")
    L.append("")
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    open(OUT_MD, "w").write("\n".join(L))
    json.dump({"num_envs": h.n, "blocks": B, "calls": _own.calls, "penalty_level": level, "keys": KEYS,
               "identical_in_call": [n_in, n_in_tot], "identical_across_calls": [n_ac, n_ac_tot],
               "freeze_adr": h.freeze_adr, "adr": adr_calls,
               "candidates": res}, open(OUT_JSON, "w"), indent=1)
    print(f"[REPEAT] wrote {OUT_MD}, {OUT_JSON}", flush=True)


if __name__ == "__main__":
    run_with_harness(run)
