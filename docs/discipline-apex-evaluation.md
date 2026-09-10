# Discipline Apex evaluation

**Historical benchmark:** this evaluation used automatic first-hit maturation. The current rule for all four disciplines requires a pre-roll declaration and spends the use even on a miss. The results below predate that correction and are not validation of the current gamble; see the [corrected benchmark evaluation](maturation-declaration-evaluation.md) and [current damage methodology](../harness/README.md#damage-methodology).

The maintainer adopted **3d8 Apex damage for all four disciplines** at Fighter 18, retaining the tested Cryokinesis and Electrokinesis additions alongside Pyrokinesis and the existing Psychokinesis packet. A shared Discipline Maturation procedure deals cold for Cryokinesis, fire for Pyrokinesis, force for Psychokinesis, and lightning for Electrokinesis, once during each Attack action when a Manifested Strike hits. Only the struck creature takes the packet; each new Attack action refreshes its use, including Action Surge.

The packet costs no Psi or Blood Tax, does not double on a critical hit, and retains normal Resistance and Immunity even beside a Tier-2 rider or with Holdout. It has no Overload tier. Refined Holdout remains available to all four disciplines. Rules remain unreleased v15.0.0; schema is 2.11.0 and harness projection is 1.7.0.

This implements the adopted discipline maturation work for [#122](https://github.com/kmart01123/kinetic-vanguard/issues/122). It does not establish that every discipline sits inside the comparator interval or close the broader diagnosis issue. The [earlier Pyrokinesis evaluation](pyrokinesis-apex-evaluation.md) records its separate no-Apex, 2d8, and 3d8 comparisons.

## Level-20 results

The baseline already includes the selected 3d8 fire and existing 3d8 force packets. Cryokinesis and Electrokinesis gain their corresponding native packets in the adopted result.

| Discipline | Previous single-target DPR | Adopted DPR | Gain | Below lower comparator |
|---|---:|---:|---:|---:|
| Cryokinesis | 78.269 | 87.259 | +8.990 | 32.10% |
| Pyrokinesis | 127.105 | 127.105 | +0.000 | 1.09% |
| Psychokinesis | 109.290 | 109.290 | +0.000 | 14.95% |
| Electrokinesis | 90.145 | 106.908 | +16.763 | 16.80% |

The single-target comparator means remain Eldritch Knight 128.502 and Battle Master 164.824 DPR. Cryokinesis gains 11.49% and Electrokinesis gains 18.60% over their previous single-target results. These are maintained-roster means, not a universal real-play balance tolerance.

| Discipline | Targets | Previous aggregate DPR | Adopted aggregate DPR | Adopted band |
|---|---:|---:|---:|---|
| Cryokinesis | 3 | 151.161 | 151.308 | IDEAL (0.00%) |
| Cryokinesis | 6 | 151.161 | 151.308 | COLD (-8.20%) |
| Electrokinesis | 3 | 131.055 | 146.695 | IDEAL (0.00%) |
| Electrokinesis | 6 | 203.206 | 208.733 | HOT (+11.52%) |

The six-target Electrokinesis result rises to 11.52% above the upper comparator, up from 8.56%; this known tradeoff was part of the accepted experiment. Cryokinesis's area gain is small because its optimized area policy often uses standalone Arctic Tempest actions, which cannot trigger Attack-action Apex. Policy selection is reoptimized for each target and cluster rather than adding a fixed bonus to the previous totals.

Every level-7/11/15 damage result is unchanged. Pyrokinesis and Psychokinesis damage and selected policies are unchanged. All comparator results are unchanged, all five control evidence arrays match after updating authority provenance, and the control publication is byte-identical.

## Validation and reproduction

Frozen authority SHA-256: `f5cd2bddec5b78ea04280b63806d23a74371bcc0c50b418e184f30eade55258c`. The fresh native analytical run used all 47 maintained target profiles at levels 7/11/15/20, four disciplines, clusters 1/3/6, and 12 workers with unchanged roster, comparator, resource, and aggregation settings. Its 564 per-target detail rows include all 72 Cryokinesis/Electrokinesis level-20 experiment cases; their primary damage, aggregate damage, selected policies, and Action Surge schedules match the experiment (damage tolerance 1e-8).

Projection comparison proves that the only mechanical additions since the Pyrokinesis baseline are the two accepted packets. Focused tests cover all four damage types, level 17 versus 18 availability, one use per Attack action, Action Surge refresh, ordinary defenses and integer resistance rounding, Holdout preserving the Apex damage type, critical hits, and standalone actions. Consumer parity and malformed-mechanics mutation tests guard the shared contract.

Validation passed typechecking, canonical and harness input validation, all 77 Node tests, all 278 harness tests, deterministic publication builds, and all 11 layout checks across Chromium and Firefox.

Run `python3 -m harness.readme_matrices --write --workers 12` to regenerate the maintained publication. This run's ignored local evidence is in `artifacts/discipline-apex/`: the projection and scope proof, full per-target CSV and matrix CSV/Markdown/HTML under `damage/`, all six publication arrays, and `verification.json`. `publish-evidence.py` compares the native results to the retained Pyrokinesis baseline and the 72-case experiment and invokes the standard publication checker using these freshly generated arrays. Worker count changes execution time, not the analytical method.
