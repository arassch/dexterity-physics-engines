# Speed benchmark · Lift · 512 envs (T5)

Each run alone on the GPU (exclusive), `scripts/train.sh lift <engine> 300`, defaults (512 envs, seed 42,
`presets=cube`). Medians over iterations 100–299 (200 iterations each), read from the rsl_rl iteration blocks.

GPU: NVIDIA L40S (48 GB), AWS g6e.4xlarge.

| Metric (median, its 100–299) | PhysX | Newton (MuJoCo Warp) | Newton / PhysX |
|---|---|---|---|
| Iteration time | 1.98 s | 1.09 s | 0.55× |
| Steps per second | 8,293 | 15,073 | 1.82× |
| Collection time | 1.865 s | 0.978 s | 0.52× |
| Learning time | 0.105 s | 0.109 s | ≈1× |
| Total `Training time` (300 its, incl. startup) | 594.88 s | 325.43 s | 0.55× |

- Run folders: PhysX `2026-11-12_11-46-23` (log `~/runs/lift_physx_300.log`), Newton `2026-11-12_11-57-32`
  (log `~/runs/lift_newton_300.log`).
- The whole difference is in collection (simulation + env stepping); the PPO update costs the same in both.
- Newton is ~1.8× faster at 512 envs on Lift; the Reorient 4,096-env timing runs (T8/T9,
  `results/reorient_4096_timing.md`) showed a similar ratio (3.19 s vs 1.80 s per iteration).
