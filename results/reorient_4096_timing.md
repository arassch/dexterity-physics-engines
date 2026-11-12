# Reorient timing runs · 4,096 envs (T8, T9)

300 iterations each, seed 42, `presets=cube`, `--envs 4096`, alone on the GPU (NVIDIA L40S, 46 GB).
Medians over iterations 100–299 (200 iterations) of the rsl_rl log lines.

| | PhysX (T8) | Newton (T9) |
|---|---|---|
| Run folder | `2026-11-12_11-11-43` | `2026-11-12_11-32-53` |
| Log | `~/runs/reorient_physx_300_4096envs.log` | `~/runs/reorient_newton_300_4096envs.log` |
| Iteration time (median) | 3.19 s | 1.80 s |
| Steps per second (median) | 41,143 | 72,802 |
| Collection time (median) | 2.911 s | 1.527 s |
| Learning time (median) | 0.274 s | 0.273 s |
| Peak GPU memory (nvidia-smi) | 9.3 GB (60% util, at it. 217) | 7.7 GB (44% util, at it. 6) |
| Success at 299 | 0.000 | 0.000 |
| ADR at 299 | 0.000 | 0.000 |
| abnormal_robot at 299 | 0.0097 | 0.0787 |
| Mean reward at 299 | 3.63 | 5.90 |
| Total training time (300 its) | 931.65 s (15.5 min) | 520.61 s (8.7 min) |
| **Estimate, 15,000 iterations** | **13.3 h, ≈ $48.5** | **7.5 h, ≈ $27.4** |

Estimate = 15,000 × median iteration time (PhysX 3.19 s = 47,850 s; Newton 1.80 s = 27,000 s), at $3.65/hr;
startup (~1 min) not included. Both runs together (sequentially) ≈ 20.8 h ≈ $75.9; if run at the same time (2 training
runs are allowed) they will slow each other down, so that isn't simply the max of the two.

Notes (PhysX):
- Iteration time drifted upward during the run: 2.6–2.7 s in the first ~20 iterations, 2.95 s at 100, ~3.2 s by 250–299,
  almost all in collection time (learning stays 0.27–0.28 s). Mean episode length grew from 28.5 (it. 0) to ~321
  (it. 100) and ~315 (it. 299). If the drift continues past 300 iterations, the 15,000-iteration estimate is low.
- Memory was sampled only at the agent wake-ups (one reading during the run: 9.3 GB at iteration 217), so the
  true peak may be slightly higher. Far below the 46 GB available.
- Success 0 and ADR 0 at 300 iterations (training-time numbers, with exploration noise). Too early to say anything
  about learning; this run only measures speed.

Notes (Newton):
- Newton is ~1.8× faster per iteration at 4,096 envs (collection 1.53 s vs 2.91 s; learning identical).
- Iteration time also drifted upward: 2.62 s at it. 0 (warm-up), 1.56 s at 19, 1.59 s at 99, 1.81 s at 199, 1.90 s
  at 249, 1.96 s at 299, as mean episode length grew (28.3 → 245 at 100 → 301.5 at 299). It was still rising at the
  end, so the 7.5 h estimate is probably low; at the final 1.96 s it would be 8.2 h ≈ $29.8.
- Memory was sampled only once (7.7 GB at iteration 6, early in the run); the peak was not measured.
- abnormal_robot at 299 is 0.079 (PhysX 0.010); object_out_of_bound 0.152. Training-time numbers, 300 iterations only.
