# Status
Updated: 2026-11-12 11:31 UTC by the server agent (wake-up: state changed, T8 training process exited)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T12 clip 1: Lift PhysX policy in Newton (video, model_14999) | Newton | n/a (policy loaded, recording) | — | — | — | ~1–2 min |

No training runs. GPU was idle (0 MiB) before T12 started.

## Since last update
- **T8 done** (finished normally, `Training time: 931.65 seconds`). Medians over iterations 100–299: iteration
  3.19 s, collection 2.91 s, learning 0.27 s, 41.1k steps/s; ~9.3 GB GPU. At 299: success 0, ADR 0,
  abnormal_robot 0.010. **15,000 iterations ≈ 13.3 h ≈ $48.5.** Written to `results/reorient_4096_timing.md`.
- Iteration time rose during the run (~2.65 s → ~3.2 s, all in collection), so that estimate may be low (see
  `notes/log.md`).
- Backed up the T8 configs to `configs/reorient_physx_4096_timing/` and saved the last 60 log lines. I did **not** copy
  `model_299.pt` into the repo: it's a 300-iteration timing run, like T5 ("no checkpoints"). It is still on the server.
- Started **T12** command 1 (`record_videos.sh lift newton 2026-11-11_11-08-26 --out lift_physx_policy_in_newton 14999`).
  Command 2 (Newton policy in PhysX) starts on the next wake-up once this one finishes. After that comes T9.

## Needs a human
- Nothing blocking. If you want the T8 `model_299.pt` in the repo, say so (it's in
  `logs/.../2026-11-12_11-11-43/` on the server).
