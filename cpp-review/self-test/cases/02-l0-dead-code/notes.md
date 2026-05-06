# Case 02: L0 dead code (no production caller)

Tests the **L0 production-caller audit** from `cpp-review/SKILL.md`.

## Setup

Two files are submitted:

- `context.h` — a new, well-written `ContextCache` class (no L2/L3 defects)
- `ContextCacheTests.cpp` — a unit test file; the only file in the submitted diff that includes `context.h`

No production `.cpp` includes the header. The reviewer must notice that this
new class has no production consumer in the submitted diff.

The header is intentionally clean (docblock, `[[nodiscard]]`, `noexcept`,
ownership annotation) so the reviewer is not distracted by L2/L3 defects.

## Expected finding

```text
N. [SHOULD] context.h -- ContextCache has no production caller in this commit;
   the only consumer is ContextCacheTests.cpp (a test file). The class ships as
   dead code on trunk.
   Evidence: L0 (intent): zero production callers visible in the diff.
   Suggested: move ContextCache to the commit that wires its first production
              caller, or add the production caller in this commit.
```

Tier is SHOULD (not MUST) because the commit message does not claim the class
is already wired.

## Pass criterion

The case PASSES when the reviewer raises a finding citing that `ContextCache`
has no production caller (only a test file caller) in the submitted diff.
Two of these keywords must appear together: ContextCache / dead / caller /
production / test / ContextCacheTests / zero.
