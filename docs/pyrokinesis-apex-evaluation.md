# Pyrokinesis Apex evaluation

The candidate adds a separate 2d8 fire packet at Fighter 18, once per Attack action when a Manifested Strike hits. A new Attack action refreshes it, including Action Surge. It costs no Psi or Blood Tax, does not double on a critical hit, and respects Resistance and Immunity even when delivered beside a Tier-2 rider or with Holdout. Only the struck creature takes this packet.

This addresses the Pyrokinesis portion of [#122](https://github.com/kmart01123/kinetic-vanguard/issues/122). The other discipline decisions and the Psychokinesis/Refined Holdout question remain open. Rules stay on the unreleased v15.0.0 line; schema is 2.10.0 and harness projection is 1.6.0.

## Full-roster result

| Level-20 primary DPR, one target | Before | Candidate |
|---|---:|---:|
| Pyrokinesis | 112.105 | 122.105 |
| Lower comparator: Eldritch Knight | 128.502 | 128.502 |
| Upper comparator: Battle Master | 164.824 | 164.824 |
| Distance below lower comparator | -12.76% | -4.98% |

The gain is 10.000 DPR (8.92%). The candidate improves the late-game curve without requiring the headline cell to enter the comparator interval. Every other discipline and all level-7/11/15 damage cells remain numerically unchanged. Comparator values are unchanged at every level and cluster size. The control publication is byte-identical.

| Level-20 aggregate damage | Before | Candidate | Candidate band |
|---|---:|---:|---|
| 1 target | 112.105 | 122.105 | COLD (-4.98%) |
| 3 targets | 112.105 | 122.105 | COLD (-5.00%) |
| 6 targets | 112.105 | 122.105 | COLD (-25.92%) |

## Focused checks and interpretation

Ancient Copper Dragon gains 15.000 DPR at both one and six targets, confirming that the packet does not multiply with area coverage. A synthetic fire-resistant version gains 7.083 DPR: the expected separate 2d8 packet after integer rounding is 4.25 damage rather than 9. Fire-immune Pit Fiend gains zero DPR at either cluster size and retains its existing policy.

The level-20 roster contains no fire-resistant creatures and four fire-immune creatures among twelve. The earlier class-wide Tier-2 resistance change therefore did not improve Pyrokinesis's level-20 result. This candidate also leaves immunity matchups unchanged. Resistance penetration and new damage maturation solve different problems.

Tests cover availability at 18 versus 17, one use per actual Attack action, Action Surge refresh, critical-hit behavior, normal/immune/resistant/vulnerable damage, Holdout preserving the fire packet, no activation from standalone actions, primary-only damage, both projections, and malformed mechanical mutations. Retained individual-feature snapshots are unchanged; only the shared-core snapshot gains the authored Apex packet.

## Evidence and reproduction

The frozen candidate authority SHA-256 is `c73d0809f82e00ec4ed9254539dfc08ba17f2713fd367b462b190a8df5ff8a0c`. The full analytical run evaluated the maintained 47 profiles at levels 7/11/15/20 and cluster sizes 1/3/6. Current methodology, roster, and comparator configuration were retained. The standard publication validators accepted the outputs and synchronized README to a v15.0.0 development snapshot.

Use `npm run readme:benchmarks` for the maintained full publication workflow. This run's ignored local artifacts are under `artifacts/pyro-apex/`: `damage/kv-15-0-0-damage-comparison-matrix.csv` and companion Markdown/HTML include raw aggregates and provenance; `publication-rows.json` retains the full damage/control arrays; `sentinels.json` retains focused policies and before/after results; `scope-proof.json` verifies that only the added Pyrokinesis packet changes retained mechanics. The prior v14.4.0 evidence is retained in the parent workspace's `artifacts/issue-135/` directory.
