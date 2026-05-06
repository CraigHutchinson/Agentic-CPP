# cpp-review self-test run log

Formula: context ≈ SKILL.md (~11k) + 4 refs (~15k) + case files (~1.5k) + prior turns

| Date | Model | Case | Recall | Noise | In-tok | Out-tok | Cost | Pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-05 | claude-sonnet-4-6 | 00-comprehensive | 0/11 (0%) | 0% | 36,958 | 4,096 | $0.1723 | FAIL |
| 2026-05-05 | claude-sonnet-4-6 | 01-anti-pattern-guard | 0/0 (100%) | 0% | 36,794 | 2,472 | $0.1475 | PASS |
| 2026-05-05 | claude-sonnet-4-6 | 02-l0-dead-code | 0/1 (0%) | 0% | 36,561 | 3,014 | $0.1549 | FAIL |
| 2026-05-06 | claude-sonnet-4-6 | 00-comprehensive | 10/11 (91%) | 15% | 36,958 | 4,096 | $0.1723 | FAIL |
| 2026-05-06 | claude-sonnet-4-6 | 01-anti-pattern-guard | 0/0 (100%) | 0% | 36,794 | 3,711 | $0.1661 | PASS |
| 2026-05-06 | claude-sonnet-4-6 | 02-l0-dead-code | 1/1 (100%) | 56% | 36,773 | 3,147 | $0.1575 | PASS |
| 2026-05-06 | claude-sonnet-4-6 | 00-comprehensive | 0/11 (0%) | 0% | 36,958 | 4,407 | $0.1770 | FAIL |
| 2026-05-06 | claude-sonnet-4-6 | 01-anti-pattern-guard | 0/0 (100%) | 0% | 36,794 | 2,439 | $0.1470 | PASS |
| 2026-05-06 | claude-sonnet-4-6 | 02-l0-dead-code | 0/1 (0%) | 0% | 36,773 | 2,950 | $0.1546 | FAIL |
| 2026-05-06 | claude-sonnet-4-6 | 00-comprehensive | 10/11 (91%) | 36% | 36,958 | 5,851 | $0.1986 | FAIL |
| 2026-05-06 | claude-sonnet-4-6 | 01-anti-pattern-guard | 0/0 (100%) | 100% | 36,794 | 3,174 | $0.1580 | FAIL |
| 2026-05-06 | claude-sonnet-4-6 | 02-l0-dead-code | 1/1 (100%) | 0% | 36,773 | 2,491 | $0.1477 | PASS |
| 2026-05-06 | claude-sonnet-4-6 | 00-comprehensive | 10/11 (91%) | 21% | 36,958 | 5,006 | $0.1860 | PASS |
| 2026-05-06 | claude-sonnet-4-6 | 01-anti-pattern-guard | 0/0 (100%) | 100% | 36,794 | 2,985 | $0.1552 | PASS |
| 2026-05-06 | claude-sonnet-4-6 | 02-l0-dead-code | 1/1 (100%) | 50% | 36,773 | 2,966 | $0.1548 | PASS |
