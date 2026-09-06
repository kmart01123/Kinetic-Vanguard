# Pyrokinesis Apex evaluation

Historical Pyrokinesis-only evaluation. The subsequently adopted Cryokinesis/Electrokinesis packets and current combined results are recorded in the [discipline Apex evaluation](discipline-apex-evaluation.md).

The maintainer selected **3d8 fire**, matching Psychokinesis's Apex dice count. At Fighter 18, once per Attack action, a Manifested Strike hit deals this separate packet to the struck creature. Each new Attack action refreshes it, including Action Surge. It costs no Psi or Blood Tax, does not double on critical hits, and respects Resistance and Immunity even beside a Tier-2 rider or with Holdout.

This implements the Pyrokinesis portion of [#122](https://github.com/kmart01123/kinetic-vanguard/issues/122). Other discipline decisions and the Psychokinesis/Refined Holdout question remain open. Rules stay on unreleased v15.0.0, with schema 2.10.0 and projection 1.6.0; the 2d8 candidate was never published.

## Full-roster result

| Level-20 single-target result | No Pyro Apex | Earlier 2d8 | Selected 3d8 |
|---|---:|---:|---:|
| Pyrokinesis DPR | 112.105 | 122.105 | 127.105 |
| Distance below EK | -12.76% | -4.98% | -1.09% |

The 3d8 packet adds **15.000 DPR (13.38%)** over no Apex, and **5.000 DPR** over 2d8. Eldritch Knight remains the lower comparator at 128.502 DPR; Battle Master is 164.824. The remaining shortfall reflects the measured comparator interval and is not a universal real-play balance tolerance.

All other disciplines and level-7/11/15 damage cells remain numerically unchanged. Every comparator value is unchanged. The control publication is byte-identical.

| Level-20 aggregate damage | No Apex | 2d8 | 3d8 | 3d8 band |
|---|---:|---:|---:|---|
| 1 target | 112.105 | 122.105 | 127.105 | COLD (-1.09%) |
| 3 targets | 112.105 | 122.105 | 127.105 | COLD (-1.11%) |
| 6 targets | 112.105 | 122.105 | 127.105 | COLD (-22.88%) |

## Focused checks

| Target | Cluster | DPR gain over no Apex |
|---|---:|---:|
| Ancient Copper Dragon | 1 | +22.500 |
| Ancient Copper Dragon | 6 | +22.500 |
| Ancient Copper Dragon (synthetic fire Resistance) | 1 | +10.833 |
| Pit Fiend | 1 | +0.000 |
| Pit Fiend | 6 | +0.000 |

The packet adds damage only to the struck creature. Its expected damage is 13.5 normally and 6.5 after integer rounding against fire Resistance; critical hits do not double it. The level-20 roster has zero fire-resistant creatures and four fire-immune creatures among twelve, so fire immunity reduces the roster gain while remaining a real limitation. The earlier class-wide Tier-2 resistance rule did not improve Pyrokinesis's level-20 result.

Focused tests cover availability at 18 versus 17, use per actual Attack action, Action Surge refresh, critical hits, Resistance/Immunity/Vulnerability, Holdout retaining fire damage, no Apex from standalone actions, primary-only damage, both consumer projections, and malformed mutations. Projection comparison proves that only the Pyrokinesis dice count changed from the 2d8 candidate; Psychokinesis and all other mechanics are preserved.

## Evidence and reproduction

Frozen authority SHA-256: `f0ffe9ba57cf80c168fe26e34a7903f086f3deb40e021b8ccaabb3953f52d84b`. The fresh analytical run evaluated all 47 maintained profiles at levels 7/11/15/20 and clusters 1/3/6, using 12 workers with unchanged methodology, roster, and comparator configuration. Worker count affects execution time, not evaluation or aggregation. Standard publication validators accepted the results and synchronized README to the 3d8 v15.0.0 development snapshot.

Use `python3 -m harness.readme_matrices --write --workers 12` for the maintained publication workflow with the same worker count. This run's ignored local evidence is in `artifacts/pyro-apex/`: `damage/kv-15-0-0-damage-detail.csv` retains per-target policies; the comparison matrix CSV/Markdown/HTML retain aggregates and provenance; `publication-rows.json` retains all publication arrays; `sentinels.json` retains focused comparisons; `scope-proof.json` records the exact change from 2d8. The unchanged no-Apex sentinel baselines were reused from the prior run after verifying that dice count is the only mechanical change. Earlier 2d8 evidence remains in `artifacts/pyro-apex-2d8/`; no-Apex v14.4 evidence is in the parent workspace's `artifacts/issue-135/`.
