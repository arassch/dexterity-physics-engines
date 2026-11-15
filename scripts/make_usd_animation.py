#!/usr/bin/env python3
"""Turn a recording from scripts/export_episode.py into a USD animation that Unreal's USD Stage actor can play.

Runs anywhere with the USD Python bindings (`pip install usd-core`); no Isaac Lab or GPU needed, so you can run it on
your own computer after downloading the .json and .usd files.

It writes a small .usda layer that sublayers the exported scene and overrides, for every frame (60 fps):
  * each robot link's transform (time samples), computed relative to its parent prim
  * the cube's transform
  * a new translucent "Goal" cube at the target pose
Open the output .usda in Unreal (Place Actors → USD Stage, or File → Import into Level), then scrub or play the
stage's timeline. Unreal converts USD's metres/Z-up to centimetres for you (check Stage metersPerUnit if not).

Usage:
  python3 make_usd_animation.py <recording.json> <scene.usd> <out.usda> [--env N | --all_envs] [--goal_size 0.06]
  For a Newton playback, use the scene and prim paths of a PhysX export of the same task:
  python3 make_usd_animation.py reorient_physx_in_newton.json reorient_physx_in_physx.usd out.usda \\
      --usd_from reorient_physx_in_physx.json

The recording's env N is played on env_N's robot. By default only that env is kept visible; --all_envs animates
every env in the recording.
"""

import argparse
import json
import os

from pxr import Gf, Sdf, Usd, UsdGeom


def _matrix(pos, quat_xyzw) -> Gf.Matrix4d:
    x, y, z, w = quat_xyzw
    m = Gf.Matrix4d(1.0)
    m.SetRotateOnly(Gf.Quatd(w, Gf.Vec3d(x, y, z)).GetNormalized())
    m.SetTranslateOnly(Gf.Vec3d(*pos))
    return m


def _env_path(path: str, i: int) -> str:
    return path.replace("/World/envs/env_0", f"/World/envs/env_{i}", 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("recording")
    ap.add_argument("scene")
    ap.add_argument("out")
    ap.add_argument("--env", type=int, default=0)
    ap.add_argument("--all_envs", action="store_true")
    ap.add_argument("--usd_from", default="", help="Take the scene's prim paths from this recording (a PhysX one), "
                    "for a recording played in Newton, which can't export the scene itself.")
    ap.add_argument("--goal_size", type=float, default=0.06, help="Edge length (m) of the goal marker cube.")
    args = ap.parse_args()

    with open(args.recording) as f:
        rec = json.load(f)
    meta, frames = rec["meta"], rec["frames"]
    usd = meta.get("usd")
    if args.usd_from:
        with open(args.usd_from) as f:
            usd = json.load(f)["meta"].get("usd")
    if not usd:
        raise SystemExit("No USD info: pass --usd_from <a PhysX recording of the same task> (Newton runs have no scene).")
    body_names = meta["body_names"]
    body_prims = usd["body_prims"]
    missing = [b for b in body_names if b not in body_prims]
    if missing:
        print(f"warning: no prim found for {len(missing)} bodies (left static): {missing}")
    envs = range(meta["num_envs"]) if args.all_envs else [args.env]

    scene = Usd.Stage.Open(args.scene)
    layer = Sdf.Layer.CreateNew(args.out)
    layer.subLayerPaths.append(os.path.relpath(os.path.abspath(args.scene), os.path.dirname(os.path.abspath(args.out))))
    stage = Usd.Stage.Open(layer)
    stage.SetEditTarget(layer)
    fps = round(1.0 / meta["control_dt"])
    stage.SetTimeCodesPerSecond(fps)
    stage.SetFramesPerSecond(fps)
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(len(frames) - 1)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, UsdGeom.GetStageMetersPerUnit(scene) or 1.0)

    if not args.all_envs:  # show only the chosen robot
        for i in range(meta["num_envs"]):
            if i != args.env:
                stage.OverridePrim(f"/World/envs/env_{i}").SetActive(False)

    xcache = UsdGeom.XformCache(Usd.TimeCode.Default())
    for i in envs:
        origin = Gf.Vec3d(*meta["env_origins"][i])
        prim_of = {b: _env_path(p, i) for b, p in body_prims.items()}
        # each animated prim: (path, parent path, function frame -> world matrix)
        animated = []
        for b in body_names:
            if b in prim_of:
                k = body_names.index(b)
                animated.append((prim_of[b], lambda e, k=k: _matrix(Gf.Vec3d(*e["body_pos"][k]) + origin, e["body_quat"][k])))
        obj_path = _env_path(usd["object_prim"], i)
        animated.append((obj_path, lambda e: _matrix(Gf.Vec3d(*e["object_pos"]) + origin, e["object_quat"])))

        goal_path = _env_path(usd["env_prim"], i) + "/Goal"
        goal = UsdGeom.Cube.Define(stage, goal_path)
        goal.CreateSizeAttr(args.goal_size)
        goal.CreateDisplayColorAttr([Gf.Vec3f(0.2, 0.8, 0.3)])
        goal.CreateDisplayOpacityAttr([0.35])
        animated.append((goal_path, lambda e: _matrix(Gf.Vec3d(*e["goal_pos"]) + origin, e["goal_quat"])))

        ops = {}
        for path, _ in animated:
            prim = stage.OverridePrim(path) if path != goal_path else stage.GetPrimAtPath(path)
            xf = UsdGeom.Xformable(prim)
            xf.ClearXformOpOrder()
            ops[path] = xf.AddTransformOp(opSuffix="anim")

        for t, frame in enumerate(frames):
            e = frame["envs"][i]
            world = {path: fn(e) for path, fn in animated}
            for path, _ in animated:
                parent = str(Sdf.Path(path).GetParentPath())
                if parent in world:
                    parent_w = world[parent]
                else:  # a static prim (env, robot root): its transform from the exported scene
                    parent_prim = scene.GetPrimAtPath(parent)
                    parent_w = xcache.GetLocalToWorldTransform(parent_prim) if parent_prim else Gf.Matrix4d(1.0)
                ops[path].Set(world[path] * parent_w.GetInverse(), Usd.TimeCode(t))
        ends = [(fr["step"], fr["envs"][i]["episode_end"]) for fr in frames if "episode_end" in fr["envs"][i]]
        print(f"env {i}: {len(animated)} animated prims, episode ends at {ends or 'none'}")

    layer.Save()
    print(f"wrote {args.out} ({len(frames)} frames at {fps} fps)")


if __name__ == "__main__":
    main()
