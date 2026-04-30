# Anti-Pattern Guard

Shared C++ reference. Loaded by `cpp-write` (step 0, before authoring), `cpp-review` (before producing findings), and `cpp-simplify` (step 1, reference load). Living list of finding categories the reviewer has learned **not** to raise, derived from review feedback on past PRs. Load before producing any findings.

Append a new entry when a finding type is rejected with the same reason on two or more PRs. Include the rejection rationale -- future reviewers (human and persona) need it.

## Overriding principle (read first)

**Safety-improving and forward-thinking modernisation is NEVER an anti-pattern.** The guard suppresses *cosmetic / preference-only* findings, not findings that would make the code less error-prone, more idiomatic, or harder to misuse.

Before suppressing any finding under this guard, ask:

1. Does the suggested change *reduce* a class of bug at the call site? (Bounds, lifetime, type-safety, range-for vs index loop, total functions over partial.) -> **Raise it.** SHOULD at minimum.
2. Does it *encode an invariant* in the type system that the reader currently has to track in their head? (`[[nodiscard]]`, `noexcept`, `static_assert`, `core::array_ref` over hand-rolled `data + size`.) -> **Raise it.** SHOULD at minimum.
3. Does it *eliminate reinvention* of a documented project utility? (`StrICmp`, `core::Format`, `core::array_ref`, `Argv.cpp` helpers.) -> **Raise it.** MUST per the reinvention check.
4. Is the suggested change *only* a stylistic preference with no measurable safety / clarity / reuse improvement? -> Suppress.

"Migration cost is non-zero" is **not** a sufficient reason to suppress. Migration cost belongs in the SHOULD vs MUST tier choice, not in the suppress decision. Most safety wins amortise across the lifetime of the code.

## Defensive asserts on impossible inputs

**Do not raise** "add `Assert(!(a && b))` to guard the impossible case" when:

- The function is intentionally written as a total function over the input space.
- The choice is documented in a comment block at the function.
- The "impossible" case has a defined behaviour that's tested.

Raise it only when the input space genuinely allows the bad combination and the current code silently does the wrong thing.

## Rewording comments to drop project context

**Do not raise** "remove the [JIRA-NNNN] reference from this comment" as a finding. Project / ticket references in comments help future readers understand why the code looks the way it does, and the AGENTS.md hygiene rules call for "WHY not WHAT" -- the WHY often references the initiative.

Drop only when the comment is a roadmap / phase narrative ("we will do X in Phase D"), which is explicitly forbidden by AGENTS.md.

## File-static and function-local-static caches in process-immutable contexts

**Do not raise** "wrap this static in a class" when *all* of the following hold:

- The cached value is derived from compile-time constants or from configuration loaded once at process start, before any test fixture could run.
- No `#if ENABLE_UNIT_TESTS_WITH_FAKES` (or equivalent) bypass exists in the accessor.
- Tests do not, and cannot reasonably need to, exercise alternative values of the cached state.
- The accessor is `noexcept` and the cache is set exactly once per process lifetime.

This rule covers both file/namespace-scope statics and function-local statics symmetrically. The motivating modernisation (`modernisation-playbook.md > Globals, singletons, and testability seam`) targets the testability defect, not statics in the abstract. When the cache is genuinely process-immutable, the static form is the simplest correct shape.

**Always raise** when the accessor carries a test-only bypass branch. The bypass *is* the evidence -- the original author already conceded that the static is testability-hostile but chose to fork the code paths rather than redesign. **A function-local static is not a "smaller" version of a file-static** -- it has identical testability properties (latched once per process, no reset hook, scoped-override impossible). The narrower lexical scope does not buy any test isolation.

Narrow exceptions where function-local statics are acceptable:

- Write-only diagnostic counters that nothing depends on for behaviour.
- Meyer's-singleton holders for genuinely immutable values (e.g. a process-lifetime const lookup table built at first call) that have no plausible test alternative.

Both exceptions require that the static is observed only through reads that test code does not need to influence. Anything else -- including "it's just a cache, the contents are derived from inputs that don't change" -- still benefits from instance ownership and should be raised.

## Suggesting tests as MUST findings

**Do not** raise "add a test for this" as MUST. Test coverage findings are SHOULD at most -- the missing test is a quality gap, not a defect. Raise as MUST only when the diff explicitly removes a test that pinned a documented invariant.

---

*Add new entries below this line as the team learns the persona's blind spots and over-eager patterns.*
