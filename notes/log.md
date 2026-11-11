# Working notes

## 2026-11-11: Setup and first PhysX runs

**Cloud setup**
- Brev Isaac Launchable (Isaac Sim 6.0.1, Isaac Lab 3.0.0-beta2-post1) on AWS `g6e.4xlarge` (1× L40S).
- Provisioning failed with "internal server error" in Stockholm and Frankfurt; succeeded in us-east-1.
- The VS Code terminal is a non-root container: no `sudo` or `tmux`. Using `nohup` + `PYTHONUNBUFFERED=1`.
  Without unbuffered output, the redirected log updates in bursts and stdout/stderr lines appear out of order.

**Task discovery**
- `list_envs.py --keyword Dexsuite --show_presets`: Lift and Reorient both support
  `physics: newton_mjwarp, physx`, plus domain presets `cube`, `shapes`, `state` and a range of camera modes.
- Using `presets=cube` on both engines (Newton can't do multi-shape spawning).

**Timing run: Lift, PhysX, 512 envs, 300 iterations**
- ~2.0 s per iteration, ~8,000 steps/s, 16,384 steps per iteration (512 × 32).
- Collection 1.9 s vs learning 0.1 s: the simulation is the bottleneck, not PPO.
- At 300 iterations: mean reward ≈ −0.4 (action penalties dominate), `fingers_to_object` ≈ +0.03 (reaching),
  success ≈ 0–2%, ~36% of episodes end with the cube knocked out of bounds.
- Full run of 15,000 iterations ≈ 8.3 h ≈ $30 at $3.65/hr.

**To investigate (Part 3/4)**
- PhysX start-up warning: *"TGS solver with enable_external_forces_every_iteration=False may cause noisy velocities."*
  Check whether the trained policy depends on this, e.g. by evaluating with the flag flipped.

**Next**
- Full Lift run on PhysX (15,000 iterations, seed 42) started ~11:10.
