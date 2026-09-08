# Triple-AAA release scorecard

Gate-level statuses use `PASS`, `PARTIAL`, `BLOCKED`, `NOT_RUN` and `PENDING`. The phrase `PASS (scoped)` means that the gate passes its explicitly declared software/architecture scope; it is not a synonym for audiovisual production acceptance and it cannot promote the overall release.

The three gates are independent and scored on their own evidence:

| Gate | PASS requires | Current closure reading |
|---|---|---|
| Architecture | canonical ownership, one-way dependencies, progressive disclosure, safety boundary, traceability and ADR challenge | `PASS (scoped)` |
| Verification | all deterministic tests, known-good/bad fixtures, runtime contract fakes, adapter differential, portability and distribution checks | `PASS (scoped)` |
| Production | exact local/generated media, byte/decode QA, category-separated semantic/continuity/audio observations, transitions and editorial review for claimed ladder | `PARTIAL/BLOCKED` until unavailable capabilities and long-form artifacts are resolved |

## Maturity levels

0. `INTENT_ONLY`: only a creative objective exists.
1. `STRUCTURAL_PLAN`: canonical plan and graph validate.
2. `DETERMINISTIC_VERIFICATION`: contracts and fixtures pass.
3. `RUNTIME_PROVENANCE`: exact runtime/profile/workflow/attempt/artifact hashes are retained.
4. `AUDIOVISUAL_EVALUATION`: inspected media has category-separated observations and human/qualified semantic oracles.
5. `REPEATABLE_BOUNDED_PRODUCTION`: ladder case passes, repair budgets are respected, packaging is portable, and a fresh critic accepts the frozen bar.

The final label is `TRIPLE_AAA_CANDIDATE` only when all three gates are PASS. A strong architecture or software score never upgrades a blocked production score.
