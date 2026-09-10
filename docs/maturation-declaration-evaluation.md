# Discipline Maturation declaration evaluation

The corrected v15.0.0 development rules require declaring Discipline Maturation before a Manifested Strike attack roll. Declaration spends the once-per-Attack-action use even on a miss. Only the declared attack can deliver the separate 3d8 native-damage packet; each new Attack action, including Action Surge, grants a fresh use. The planner can defer declaration using observed state, but cannot choose after seeing the declared roll. Combat Prowess can convert that declared miss into a hit. Normal defenses, no critical doubling, and no Psi or Blood Tax cost are preserved.

These results established the pre-surgical baseline and replaced the automatic first-hit snapshot. README now uses the subsequent [surgical integration benchmark](surgical-damage-integration.md). The [earlier discipline evaluation](discipline-apex-evaluation.md) remains a historical record of the adopted 3d8 packets. Rules remain unreleased v15.0.0, with schema 2.12.0 and harness projection 1.8.0.

## Fighter-20 single-target results

| Discipline | Previous first-hit DPR | Corrected DPR | Change | Corrected benchmark |
|---|---:|---:|---:|---|
| Cryokinesis | 87.259 | 87.100 | -0.159 | COLD (-32.22%) |
| Pyrokinesis | 127.105 | 126.818 | -0.287 | COLD (-1.31%) |
| Psychokinesis | 109.290 | 108.782 | -0.508 | COLD (-15.35%) |
| Electrokinesis | 106.908 | 106.497 | -0.411 | COLD (-17.12%) |

The comparator means remain Eldritch Knight **128.502 DPR** and Battle Master **164.824 DPR**. These classifications measure the maintained comparator interval, not a universal real-play balance tolerance. The broader damage/control tradeoff assessment in [#122](https://github.com/kmart01123/kinetic-vanguard/issues/122) remains open.

## Fighter-20 area results

Aggregate damage includes all targets in the configured cluster; the maturation packet still damages only the struck creature. Each target/discipline/cluster policy and Action Surge schedule is reoptimized.

| Discipline | Targets | Previous aggregate DPR | Corrected aggregate DPR | Change | Corrected benchmark |
|---|---:|---:|---:|---:|---|
| Cryokinesis | 3 | 151.308 | 151.308 | +0.000 | IDEAL |
| Cryokinesis | 6 | 151.308 | 151.308 | +0.000 | COLD (-8.20%) |
| Pyrokinesis | 3 | 127.105 | 126.818 | -0.287 | COLD (-1.34%) |
| Pyrokinesis | 6 | 127.105 | 126.818 | -0.287 | COLD (-23.06%) |
| Psychokinesis | 3 | 114.448 | 113.939 | -0.508 | COLD (-11.36%) |
| Psychokinesis | 6 | 122.557 | 122.050 | -0.508 | COLD (-25.95%) |
| Electrokinesis | 3 | 146.695 | 146.306 | -0.388 | IDEAL |
| Electrokinesis | 6 | 208.733 | 208.723 | -0.010 | HOT (+11.51%) |

## Scope and verification

The native analytical run used all 47 maintained headline creature profiles at Fighter levels 7/11/15/20, all four disciplines, clusters 1/3/6, and **12 workers**. It produced 564 per-target detail rows and 96 damage matrix rows, followed by the full control publication evaluation. No roster, comparator, resource, or aggregation settings changed.

Comparison with the retained first-hit baseline confirms:

- All 420 level-7/11/15 detail rows retain identical damage, selected policies, and Action Surge schedules.
- All comparator damage and Action Surge schedules are unchanged.
- All five control publication arrays are unchanged except for authority provenance; the rendered control publication remains byte-identical.
- No level-20 damage matrix value increases under the corrected declaration rule.
- The consumer projection differs mechanically only in the four maturation packets' declaration and consumption fields.

Current authority SHA-256: `63e34d17bce2dc410c8eb21ad508d9de2bacfec8ff0d11d0851ced4dce06b703`. Baseline authority SHA-256: `f5cd2bddec5b78ea04280b63806d23a74371bcc0c50b418e184f30eade55258c`.

Ignored local evidence is retained in `artifacts/maturation-declaration/`: `damage/` contains full per-target CSV and comparison CSV/Markdown/HTML, `control/` contains control evidence, `publication-rows.json` retains all six publication arrays, `inputs.json` freezes input/code hashes, and `verification.json` records the baseline comparison. The publication write and check use the standard validators with these freshly generated rows, without repeating the expensive analytical run.

To regenerate through the maintained workflow, run `python3 -m harness.readme_matrices --write --workers 12`. The retained runner also supports `python3 artifacts/maturation-declaration/benchmark.py --check` while its frozen inputs still match the workspace.
