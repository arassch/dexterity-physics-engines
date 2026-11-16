# T22 · Reward experiment · Lift · PhysX, 3,000 iterations

Same setup as T1 (512 envs, seed 42, `presets=cube`), stopped at 3,000 iterations. Only the reward weights below change
(via `scripts/train.sh --override`). Evaluation: `scripts/eval.sh`, deterministic policy, ~1,024 episodes each
(`results/cross_eval.csv`, label `lift`). Success CIs are 95% Wilson intervals.

| Variant | Weights changed | Eval engine | Success (95% CI) | abnormal_robot | object_out_of_bound | time_out |
|---|---|---|---|---|---|---|
| Baseline (T1 `model_3000.pt`) | none | PhysX | 7.9% (6.4–9.7) | 0.7% | 2.1% | 97.3% |
| Baseline (T1 `model_3000.pt`) | none | Newton | 0.0% (0.0–0.4) | 97.1% | 2.9% | 0.0% |
| A `noactpen` (`model_2999.pt`) | `action_l2` = `action_rate_l2` = 0 | PhysX | 0.0% (0.0–0.4) | 1.7% | 4.1% | 94.3% |
| A `noactpen` (`model_2999.pt`) | `action_l2` = `action_rate_l2` = 0 | Newton | 0.0% (0.0–0.4) | 98.5% | 1.7% | 0.0% |
| B `nograsp` (`model_2999.pt`) | `good_finger_contact` = `contact_count` = 0 | PhysX | **90.2%** (88.3–91.9) | 0.8% | 1.4% | 97.9% |

(B in Newton was not part of the task.)

Training logs, final iteration (training-time, with exploration noise):

| Variant | Success | ADR | Mean reward | Mean action std (it 0 → 500 → 1,500 → 2,999) | action_l2 / action_rate_l2 reward terms | s/iter |
|---|---|---|---|---|---|---|
| A `noactpen` | 0.00 | 0.0002 | 8.63 | 1.00 → 1.20 → 1.42 → **1.69** | 0 / 0 (weight 0) | 2.33 |
| B `nograsp` | 0.93 | 0.986 | 19.05 | 1.00 → 0.38 → … → 0.73 | −0.307 / −0.128 | 4.25 |

Mean |action| and mean |action rate| are not logged directly. The logs only give the weighted penalty terms, which
are 0 for A by construction. A and B trained at the same time on one GPU, so their s/iter are not comparable with T5.

Clips (on the server, not in git): `~/runs/videos/lift_physx_noactpen/model_2999.mp4`,
`~/runs/videos/lift_physx_nograsp/model_2999.mp4`, `~/runs/videos/lift_physx_baseline3000/model_3000.mp4`.
Sara's description: _(to add)_.

See Finding 6 in `notes/log.md`.
