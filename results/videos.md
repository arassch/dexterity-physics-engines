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
- These clips are in-engine only. The cross-engine clips are in the next section (T12).

## Transfer clips · Lift policy in the other engine (T12)

Same settings as above (4 envs, 360 steps, seed 42), but the final policy plays in the engine it was *not* trained in.

| Trained in → played in | Run folder | Checkpoint | Clip | Size (bytes) |
|---|---|---|---|---|
| PhysX → Newton | `2026-11-11_11-08-26` | 14999 | `lift_physx_policy_in_newton/model_14999.mp4` | 556,607 |
| Newton → PhysX | `2026-11-11_23-21-33` (resume) | 14999 | `lift_newton_policy_in_physx/model_14999.mp4` | 786,306 |

- Both recorded without a Traceback (11:30–11:32 UTC). The PhysX → Newton log shows the Newton manager loading, so the
  engine switch took effect.
- The play logs don't print resets or terminations, so the number of resets within each clip can't be read from them;
  T6 suggests PhysX → Newton resets after ~23 control steps (98% `abnormal_robot`), which would be ~15 resets in
  a 360-step clip. Someone needs to watch the clips to confirm.
- Both transfer clips are larger than the same policy in its own engine (PhysX policy: 556,607 vs 486,627 bytes;
  Newton policy: 786,306 vs 254,974). Larger files suggest more motion/scene changes (e.g. frequent resets or
  flailing), but that's only a hint.

# Training-progress videos · Reorient (T14)

Recorded Sun 15 Nov 2026, 15:38–15:45 UTC, with `scripts/record_videos.sh` (same play settings as Lift: 4 envs,
360 control steps, seed 42, `presets=cube`, headless), from the 4,096-env full runs (T10, T11). Each policy plays in
its own engine. Clips are on the server only (`~/runs/videos/reorient_<engine>/`), not in git.

| Engine | Run folder | Checkpoint | Clip | Size (bytes) |
|---|---|---|---|---|
| PhysX | `2026-11-12_22-18-09` | 1000 | `reorient_physx/model_1000.mp4` | 472,100 |
| PhysX | `2026-11-12_22-18-09` | 5000 | `reorient_physx/model_5000.mp4` | 466,147 |
| PhysX | `2026-11-12_22-18-09` | 10000 | `reorient_physx/model_10000.mp4` | 543,875 |
| PhysX | `2026-11-12_22-18-09` | 14999 | `reorient_physx/model_14999.mp4` | 519,620 |
| Newton | `2026-11-12_22-19-43` | 1000 | `reorient_newton/model_1000.mp4` | 244,449 |
| Newton | `2026-11-12_22-19-43` | 5000 | `reorient_newton/model_5000.mp4` | 275,397 |
| Newton | `2026-11-12_22-19-43` | 10000 | `reorient_newton/model_10000.mp4` | 397,235 |
| Newton | `2026-11-12_22-19-43` | 14999 | `reorient_newton/model_14999.mp4` | 370,644 |

- No Traceback and no `FAILED: no video produced` line in either log (`~/runs/videos_reorient_<engine>.log`).
- As with Lift, the Newton clips are smaller than the PhysX ones (≈240–400 KB vs ≈470–540 KB). Both engines' clips
  grow from 5,000 to 10,000, when training success was rising. Size is only a hint; someone needs to watch them.

## Transfer clips · Reorient policy in the other engine (T15)

| Trained in → played in | Run folder | Checkpoint | Clip | Size (bytes) |
|---|---|---|---|---|
| PhysX → Newton | `2026-11-12_22-18-09` | 14999 | `reorient_physx_policy_in_newton/model_14999.mp4` | 565,901 |
| Newton → PhysX | `2026-11-12_22-19-43` | 14999 | `reorient_newton_policy_in_physx/model_14999.mp4` | 586,896 |

- Both recorded without a Traceback (15:38–15:39 and 15:42–15:46 UTC). The PhysX → Newton log loads
  `isaaclab_newton/physics/newton_manager.py`, so the engine switch took effect.
- Both transfer clips are larger than the same policy in its own engine (PhysX policy: 565,901 vs 519,620 bytes;
  Newton policy: 586,896 vs 370,644). Same pattern as Lift (T12). The play logs don't print resets; T13 measured
  0% success both ways and 94% `abnormal_robot` for PhysX → Newton, so the clips should show frequent resets.
  Someone needs to watch them to confirm.
