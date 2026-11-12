# Status
Updated: 2026-11-12 10:12 UTC by the server agent (wake-up: manual --once)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T4 Reorient | Newton | 1,140 / 15,000 | 0.00 | 0.99 | 0.00 | ~17:10 UTC (~7 h, 1.13 s/it) |

T3 Reorient PhysX is finished (see below). T5 waits until T4 is done (it needs the GPU to itself).

## Since last update
- **T3 Reorient · PhysX finished normally** (10 h 40 min, no Traceback). Backed up `model_14999.pt`, configs, final
  log excerpt. Set to `done`. Training success is only **~4%** (last-500-iteration mean 4.2%), ADR **0.005**,
  abnormal_robot ~1%. It plateaued from iteration ~3,000. The policy holds the cube (position reward ~1.1) but does not
  reorient it (final orientation error 2.35 rad). Details in `notes/log.md`.
- **T4 Reorient · Newton** is running. ~99% of episodes end through `abnormal_robot` (episode length ~25–30 steps).
  Lift Newton looked the same at iterations 500–1,500 and recovered by ~2,500, so I'm not treating this as a failure yet.

## Needs a human
- **Reorient PhysX barely learned (~4% training success, ADR stuck near 0).** That makes the Reorient comparison
  between engines weak. Is 15,000 iterations at 512 envs too little for Reorient, or does it need different defaults?
  This decision belongs to the planning chat (PLAN.md). I changed nothing.
- If T4 still has abnormal_robot > 0.9 at ~3,000 iterations (~10:45 UTC), it is probably stuck. Should it be stopped?
  The crash policy doesn't cover a run that keeps going but isn't learning, so I will leave it running unless PLAN.md says otherwise.
