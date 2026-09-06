# Roadmap

## v15.0 development (continuing the v14.4 roadmap)

### Rider-first mechanical model

Inventory and then standardize ability representation around one rider per Manifested Strike while preserving every current rule outcome and the existing action economy. The accepted Phase 1 [rider-first model inventory](rider-model-inventory.md) covers every concrete ability, and the [neutral mechanical primitives design](mechanical-primitives-design.md) classifies the existing Calculator/harness fields and defines the gated migration sequence.

The schema 2.7.0 migration models every machine-consumed ability through neutral per-entity mechanics and colocates every machine-consumed shared progression/core field with one canonical rules entity. Delivery and targeting are orthogonal axes, and concrete D&D damage/save facts live with each feature. The obsolete 30-entry Calculator registry, 27-entry harness registry, and ten shared-field reference slots have been removed. The browser publication and Python harness adapter now derive deterministic consumer views directly from canonical entity order, with focused semantic equivalence checks failing closed on output drift. Player-facing procedures and utility-only abilities remain canonical prose until a real consumer demonstrates a structured-data need.

An area effect combines `targeting.topology: area` with its independently authored delivery. A rider-delivered area and a standalone area share the same targeting concept without creating combined schema types or a composite-rider category.

Completed in PR #134; issue [#132](https://github.com/kmart01123/kinetic-vanguard/issues/132) is closed. The separate Phase Step family force/Strength correction landed in PR #137 and issue #136 is also closed.

### Remaining resolution simplification

Implement the approved #135 rules together: normal Action Surge access for standalone psionic Actions, Electron Burst target parity, Static Discharge's 1/3/5 additional-target ladder, class-wide Tier-2 feature/rider resistance penetration, and explicit partial-on-success control. Validate the candidate with fresh damage/control evidence before late-game tuning.

Tracking: [#135](https://github.com/kmart01123/kinetic-vanguard/issues/135).

### Gravitic Press retirement

The maintainer chose retirement. Remove Gravitic Press from the Advanced Training pool, rules publication, and consumer projections. Removing a published option is a breaking change, so the next development rules version is v15.0.0 under the versioning policy.

Tracking: [#133](https://github.com/kmart01123/kinetic-vanguard/issues/133).

### Fighter 20 damage scaling

Diagnose the level-20 comparator crossover and subclass scaling by discipline before proposing mechanics. Keep single-target damage findings separate from discipline control tradeoffs, and prefer surgical late-game maturation if a rules change is justified.

The Pyrokinesis candidate adds a Fighter-18 once-per-Attack-action 2d8 fire hit packet through Psionic Apex, with normal defenses and no critical doubling or resource cost. Focused sentinels and the frozen full benchmark support retaining the candidate; see the [evaluation](pyrokinesis-apex-evaluation.md). Other discipline maturation and the Psychokinesis/Refined Holdout intent remain separate decisions.

Tracking: [#122](https://github.com/kmart01123/kinetic-vanguard/issues/122).

### External-review diagnostics

Make doctor and provider failures actionable while preserving exact-head validation, atomic posting, isolation, redaction, and fail-closed behavior. This tooling work is independent of subclass mechanics.

Tracking: [#119](https://github.com/kmart01123/kinetic-vanguard/issues/119).

## Completed parking-lot item

Forked Lightning's independent primary and secondary saving throws were resolved in v13.1.0. The old v13.1 parking-lot entry was removed because it no longer described an open rules issue.
