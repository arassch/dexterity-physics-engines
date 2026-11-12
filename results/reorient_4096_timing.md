# Reorient timing runs · 4,096 envs (T8, T9)

300 iterations each, seed 42, `presets=cube`, `--envs 4096`, alone on the GPU (NVIDIA L40S, 46 GB).
Medians over iterations 100–299 (200 iterations) of the rsl_rl log lines.

| | PhysX (T8) | Newton (T9) |
|---|---|---|
| Run folder | `2026-11-12_11-11-43` | — |
| Log | `~/runs/reorient_physx_300_4096envs.log` | — |
| Iteration time (median) | 3.19 s | — |
| Steps per second (median) | 41,143 | — |
| Collection time (median) | 2.911 s | — |
| Learning time (median) | 0.274 s | — |
| Peak GPU memory (nvidia-smi) | 9.3 GB (60% util, at it. 217) | — |
| Success at 299 | 0.000 | — |
| ADR at 299 | 0.000 | — |
| abnormal_robot at 299 | 0.0097 | — |
| Total training time (300 its) | 931.65 s (15.5 min) | — |
| **Estimate, 15,000 iterations** | **13.3 h, ≈ $48.5** | — |

Estimate = 15,000 × median iteration time (3.19 s = 47,850 s), at $3.65/hr; startup (~1 min) not included.

Notes (PhysX):
- Iteration time drifted upward during the run: 2.6–2.7 s in the first ~20 iterations, 2.95 s at 100, ~3.2 s by 250–299,
  almost all in collection time (learning stays 0.27–0.28 s). Mean episode length grew from 28.5 (it. 0) to ~321
  (it. 100) and ~315 (it. 299). If the drift continues past 300 iterations, the 15,000-iteration estimate is low.
- Memory was sampled only at the agent wake-ups (one reading during the run: 9.3 GB at iteration 217), so the
  true peak may be slightly higher. Far below the 46 GB available.
- Success 0 and ADR 0 at 300 iterations (training-time numbers, with exploration noise). Too early to say anything
  about learning; this run only measures speed.
