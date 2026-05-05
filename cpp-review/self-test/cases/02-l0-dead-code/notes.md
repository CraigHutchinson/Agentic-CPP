# Case 02: L0 dead code (no production caller)

Tests the **L0 production-caller audit** from `cpp-review/SKILL.md` Pre-finding
context load step 1a and Layered design review L0 question 2.

## Setup

`ContextCache` is a new class introduced in this "commit". The header comment
explicitly states that the only file importing it is `ContextCacheTests.cpp` --
no production accessor calls `ContextCache::Get()`.

## Expected finding

```text
N. [SHOULD / L0] context.h -- ContextCache ships in this commit with zero
   production callers; the class is dead code on trunk until a follow-up
   commit wires it into a production accessor.
   Evidence: L0 (intent): only consumer is ContextCacheTests.cpp (a test file).
   Suggested: move ContextCache to the follow-up commit alongside its first
              production caller, or wire the accessor in this commit.
```

Tier is SHOULD (not MUST) because the commit message does not claim the class
is already wired.

## Pass criterion

The case PASSES if the reviewer raises an L0 finding (SHOULD or MUST) on
`ContextCache` citing zero production callers.
