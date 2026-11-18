# Status
Updated: 2026-11-18 10:45 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 8.0 h ≈ $29** (estimate: 7.3 h at the last STATUS, then about 0.4 h
yesterday until `idle_stop.log` ends at 17:10, plus this wake-up. The instance was up 2 min at 10:29). About 33 h ≈ $121
left of the $150. Please correct this from the Brev console if it's off.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T26b step 3.3 fit (`sysid_fit_adrmax2`, eval job) | Newton | grid 125 × 4 repeats | – | – | frozen 10 | ~10 min |

## Since last update
- Already done and committed (51e3ea1): T26b steps 1, 2, 3.1, 3.2 and 4 (ADR drift measured, `--freeze_adr`, new
  PhysX reference `t19_ref_physx_adrmax.npz`, repeat test with ADR frozen, the two frozen eval cells).
- This wake-up: started step 3.3, Sara's fit with ADR frozen, `--repeats 4` (step 3.2's block noise is about 4–5
  blow-ups per 64, similar in size to the gaps between the fitted candidates). The first launch failed straight away
  because the relative `--ref` path didn't resolve (`FileNotFoundError`, log `~/runs/sysid_fit_adrmax.log`). I
  relaunched it with an absolute path as `sysid_fit_adrmax2`.

## Needs a human
- T26b results so far (with ADR frozen, gravity −9.81 in every signal and every call):
  - **The call effect is gone.** Blow-ups per 64-env block over all 5 calls × 4 blocks: default 62.6 ± 4.4,
    T19 full fit 54.5 ± 5.2, T20 train best 54.0 ± 4.7, "0 in T19/T20" 52.3 ± 6.6. Std within a call ≈ std between
    calls ≈ 4–5. With full gravity, all candidates blow up far more than in T26 (where calls ≥ 3 had no gravity).
    The fits beat the default by about 8–10 blow-ups out of ≈ 62; among themselves they are within noise.
  - Eval cells, ADR frozen vs not: Reorient PhysX → fitted Newton (old fit) 0.29% vs 0.10%; PhysX → PhysX 51.0% vs
    51.5%. The drift barely moved either cell.
- Fit with ADR frozen vs the old fit, blow-ups default vs fit, and sysid_check: pending (fit running).
- Still open from before: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close.
- Sara: set T19 `done` when you're happy; "What I learned" notes for T17, T23, T18, T25, T25b, T22, T20, T26.
