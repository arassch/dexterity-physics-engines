"""Print the robot joint order stored in each T17 trace, to compare PhysX and Newton (articulation order decides
the order of the policy's joint observations and actions). Run: scripts/run_isaac.sh joint_order joint_order.py"""

import glob
import os

import numpy as np

orders = {}
for path in sorted(glob.glob(os.path.expanduser("~/runs/traces/reorient_*_in_*.npz"))):
    names = [str(n) for n in np.load(path)["joint_names"]]
    orders[os.path.basename(path)] = names
    print(os.path.basename(path), names)
ref = orders.get("reorient_physx_in_physx.npz")
new = orders.get("reorient_physx_in_newton.npz")
if ref and new:
    print("same order:", ref == new)
    print("physx index -> newton index:", [new.index(n) for n in ref])
