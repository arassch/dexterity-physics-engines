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

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


def _matrix(pos, quat_xyzw) -> Gf.Matrix4d:
    x, y, z, w = quat_xyzw
    m = Gf.Matrix4d(1.0)
    m.SetRotateOnly(Gf.Quatd(w, Gf.Vec3d(x, y, z)).GetNormalized())
    m.SetTranslateOnly(Gf.Vec3d(*pos))
    return m


# Plain UsdPreviewSurface colours, so the scene doesn't render white when its original (Omniverse/MDL) materials
# can't be found. Colours are approximate: the LBR iiwa is light grey, the Allegro Hand dark grey/black.
LOOKS = {
    "arm":   ((0.80, 0.80, 0.78), 0.35, 0.0),
    "hand":  ((0.08, 0.08, 0.09), 0.40, 0.2),
    "cube":  ((0.10, 0.35, 0.85), 0.50, 0.0),
    "table": ((0.55, 0.40, 0.25), 0.70, 0.0),
}


def _make_material(stage, name, color, roughness, metallic):
    mat = UsdShade.Material.Define(stage, f"/World/Looks/{name}")
    sh = UsdShade.Shader.Define(stage, f"/World/Looks/{name}/Surface")
    sh.CreateIdAttr("UsdPreviewSurface")
    sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    sh.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
    mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
    return mat


def _bind(stage, path, mat, stop_at=()):
    """Bind mat directly on every shape under path, skipping subtrees that start at another path in stop_at."""
    color = Gf.Vec3f(*mat.GetPrim().GetChild("Surface").GetAttribute("inputs:diffuseColor").Get())
    it = iter(Usd.PrimRange(stage.GetPrimAtPath(path)))
    for p in it:
        if str(p.GetPath()) != path and str(p.GetPath()) in stop_at:
            it.PruneChildren()
            continue
        if p.IsA(UsdGeom.Gprim):
            over = stage.OverridePrim(p.GetPath())
            UsdShade.MaterialBindingAPI.Apply(over)
            UsdShade.MaterialBindingAPI(over).Bind(mat)
            UsdGeom.Gprim(over).CreateDisplayColorAttr([color])  # for viewers that ignore materials


def _uninstance(stage, root):
    """Robot assets put their visual meshes in instanceable prims, which can't take overrides (that's why the robot
    stayed white). Turn instancing off under root, in our layer only, so each mesh can get a material."""
    root_prim = stage.GetPrimAtPath(root)
    if not root_prim:
        return 0
    count = 0
    while True:
        found = [p for p in Usd.PrimRange(root_prim, Usd.TraverseInstanceProxies()) if p.IsInstance()]
        if not found:
            return count
        for p in found:
            stage.OverridePrim(p.GetPath()).SetInstanceable(False)
        count += len(found)


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
    ap.add_argument("--layer", action="append", default=[], help="Extra .usda layer(s) to put on top, e.g. shared "
                    "lights or camera edits (strongest first). Repeatable.")
    ap.add_argument("--keep_materials", action="store_true", help="Don't replace the scene's materials with plain colours.")
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
    out_dir = os.path.dirname(os.path.abspath(args.out))
    for extra in args.layer:  # stronger than everything this script writes
        layer.subLayerPaths.append(os.path.relpath(os.path.abspath(extra), out_dir))
    layer.subLayerPaths.append(os.path.relpath(os.path.abspath(args.scene), out_dir))
    stage = Usd.Stage.Open(layer)
    stage.SetEditTarget(Usd.EditTarget(layer))
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

    mats = {} if args.keep_materials else {k: _make_material(stage, k, *v) for k, v in LOOKS.items()}

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

        if mats:
            n = _uninstance(stage, _env_path(usd["robot_root"], i))
            if n:
                print(f"env {i}: turned off instancing on {n} prims so the robot meshes can be coloured")
            links = set(prim_of.values())
            for b, p in prim_of.items():
                _bind(stage, p, mats["arm" if b.startswith("iiwa") else "hand"], stop_at=links)
            _bind(stage, obj_path, mats["cube"])
            table = _env_path(usd["env_prim"], i) + "/table"
            if scene.GetPrimAtPath(table):
                _bind(stage, table, mats["table"])

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
