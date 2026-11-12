# Training-progress videos · Lift (T7)

Recorded Thu 12 Nov 2026 with `scripts/record_videos.sh` (Isaac Lab play, `Isaac-Dexsuite-Kuka-Allegro-Lift-Play-v0`,
4 envs, 360 control steps = one 6 s episode, seed 42, `presets=cube`, headless). Each policy is played in the engine it
was trained in. Clips are on the server only (`~/runs/videos/lift_<engine>/`), not in git.

| Engine | Run folder | Checkpoint | Clip | Size (bytes) |
|---|---|---|---|---|
| PhysX | `2026-11-11_11-08-26` | 250 | `lift_physx/model_250.mp4` | 437,334 |
| PhysX | `2026-11-11_11-08-26` | 1000 | `lift_physx/model_1000.mp4` | 446,078 |
| PhysX | `2026-11-11_11-08-26` | 3000 | `lift_physx/model_3000.mp4` | 410,451 |
| PhysX | `2026-11-11_11-08-26` | 8000 | `lift_physx/model_8000.mp4` | 488,249 |
| PhysX | `2026-11-11_11-08-26` | 14999 | `lift_physx/model_14999.mp4` | 486,627 |
| Newton | `2026-11-11_13-06-41` | 250 | `lift_newton/model_250.mp4` | 498,442 |
| Newton | `2026-11-11_13-06-41` | 1000 | `lift_newton/model_1000.mp4` | 553,250 |
| Newton | `2026-11-11_13-06-41` | 3000 | `lift_newton/model_3000.mp4` | 299,088 |
| Newton | `2026-11-11_13-06-41` | 8000 | `lift_newton/model_8000.mp4` | 267,860 |
| Newton | `2026-11-11_13-06-41` | 10000 | `lift_newton/model_10000.mp4` | 280,065 |
| Newton | `2026-11-11_23-21-33` (resume) | 14999 | `lift_newton/model_14999.mp4` | 254,974 |

## Notes from the logs
- No Traceback and no `FAILED: no video produced` line in either log. Each clip took ~50–70 s to record.
- The only warnings are harmless: repeated `OmniHub ... Hub failed to launch` (no Nucleus hub on this machine),
  gymnasium's "Overwriting existing videos" in `<run_folder>/videos/play/` (the script moves each clip out right
  after recording), and two RTX renderer performance warnings.
- The Newton clips from 3,000 on are ~40% smaller than the PhysX ones (≈270–300 KB vs ≈410–490 KB). File size only
  says the frames compress differently (less motion or a different scene look); someone needs to watch the clips
  before reading anything into it.
- These clips are in-engine only. No clip of a policy run in the *other* engine was recorded (not in PLAN.md).
