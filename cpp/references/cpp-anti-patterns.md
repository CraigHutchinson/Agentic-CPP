# Anti-Pattern Guard

Shared C++ reference. Loaded by `cpp-write` (step 0, before authoring), `cpp-review` (before producing findings), and `cpp-simplify` (step 1, reference load). Living list of finding categories the reviewer has learned **not** to raise, derived from review feedback on past PRs. Load before producing any findings.

Append a new entry when a finding type is rejected with the same reason on two or more PRs. Include the rejection rationale -- future reviewers (human and persona) need it.

## Overriding principle (read first)

**Safety-improving and forward-thinking modernisation is NEVER an anti-pattern.** The guard suppresses *cosmetic / preference-only* findings, not findings that would make the code less error-prone, more idiomatic, or harder to misuse.

Before suppressing any finding under this guard, ask:

1. Does the suggested change *reduce* a class of bug at the call site? (Bounds, lifetime, type-safety, range-for vs index loop, total functions over partial.) -> **Raise it.** SHOULD at minimum.
2. Does it *encode an invariant* in the type system that the reader currently has to track in their head? (`[[nodiscard]]`, `noexcept`, `static_assert`, project span type over hand-rolled `data + size`.) -> **Raise it.** SHOULD at minimum.
3. Does it *eliminate reinvention* of a documented project utility? (A project string-compare helper, a project span type, a project argv parser.) -> **Raise it.** MUST per the reinvention check.
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

This rule covers both file/namespace-scope statics and function-local statics symmetrically. The motivating modernisation (`cpp-modernisation.md > Globals, singletons, and testability seam`) targets the testability defect, not statics in the abstract. When the cache is genuinely process-immutable, the static form is the simplest correct shape.

**Always raise** when the accessor carries a test-only bypass branch. The bypass *is* the evidence -- the original author already conceded that the static is testability-hostile but chose to fork the code paths rather than redesign. **A function-local static is not a "smaller" version of a file-static** -- it has identical testability properties (latched once per process, no reset hook, scoped-override impossible). The narrower lexical scope does not buy any test isolation.

Narrow exceptions where function-local statics are acceptable:

- Write-only diagnostic counters that nothing depends on for behaviour.
- Meyer's-singleton holders for genuinely immutable values (e.g. a process-lifetime const lookup table built at first call) that have no plausible test alternative.

Both exceptions require that the static is observed only through reads that test code does not need to influence. Anything else -- including "it's just a cache, the contents are derived from inputs that don't change" -- still benefits from instance ownership and should be raised.

## Suggesting tests as MUST findings

**Do not** raise "add a test for this" as MUST. Test coverage findings are SHOULD at most -- the missing test is a quality gap, not a defect. Raise as MUST only when the diff explicitly removes a test that pinned a documented invariant.

---

## Semantic contract weakening for testability

**Do not approve** new API added to an existing type when that API weakens the type's implicit semantic contract, even when:

- Existing call sites compile and behave identically.
- The new API enables clean test scoping.
- The net allowlist diff is zero.

**The canonical rejected case: `Singleton<T>::ScopedOverride`.** `Singleton<T>` carries a name and documented contract implying "exactly one instance, process-wide". Adding `ScopedOverride` changes that to "one *active* at a time; callers can stack-swap the active instance". The type's name and any pre-existing caller assumptions about uniqueness no longer fully hold. This change was rejected in review precisely because the semantic drift was not surfaced for user discussion before landing.

Raise as **SHOULD NOT** and issue a discussion request. Before the author proceeds, require answers to:

1. Is there a structural path -- extract interface, provider, type-state -- that achieves the same testability goal without altering the contract of the existing type?
2. If this type is the right host, is the contract weakening explicitly documented and understood by all callers?
3. Would a new, honestly-named type carry the expanded contract more clearly?

**Distinguish from legitimate additive changes.** Adding a method or type that does not weaken existing guarantees is *not* semantic-contract weakening. `BindInstance()` alongside `Create()` is additive: same ownership story, new producer path. An injectable constructor overload alongside the default is additive. These do not trigger this guard.

**The test for semantic drift:** after the addition, can a reader of the *existing* documentation (or any existing caller) be surprised by a behavioural change? If yes, flag it.

---

## Blocking or discouraging retroactive test coverage

**Do not** raise findings that discourage or block adding tests to existing APIs that have no direct coverage. Retroactive test additions are always valid. A reviewer must not:

- Suggest that "the code is already tested indirectly" is sufficient justification to avoid direct coverage.
- Raise structural findings against the test file itself unless the test introduces a production-code defect.
- Require API changes before accepting tests (the reverse is the correct order: tests first, then consider whether an API improvement is warranted).

**What is valid:** raising a SHOULD when the test requires a new structural path (e.g. a `BindInstance` + `ScopedOverride` style seam) that does not yet exist in the codebase -- but the finding is on the *absence of the seam*, not on the test.

---

## "Must stay aligned" comments as a substitute for shared code

**Do not propose** "add a comment at both sites stating they must stay aligned" as
a remediation for two pieces of code that share a non-trivial primitive (a parser
loop, a dash-strip + case-insensitive compare, a token-table walk, a field-by-field
copy, a header-byte layout). Comments enforce nothing. Two implementations sitting
behind a "keep me in sync" comment are two implementations that **will** drift -- the
comment is a marker for the future bug, not a guard against it.

Treat this as a last-resort suggestion only. The reviewer should propose:

1. **Extract the primitive into a shared helper.** This is the default. The cost of a
   small free function in the canonical utility module (the project's utility / kernel layer)
   is always lower than the future drift cost.
2. **Encode the alignment invariant in the type system.** `static_assert` on parallel
   array sizes, a single source-of-truth table both consumers iterate, a tagged union
   that makes the dependency unignorable.
3. **Only when (1) and (2) are both genuinely impossible** -- e.g. the duplication
   spans a binary boundary, or the two implementations live in repositories that
   cannot share code -- consider the alignment comment as a marker, and pair it with
   a tracked tech-debt ticket that names the future unification work.

**Raise the underlying duplication finding** at the appropriate tier (SHOULD when
the drift risk is real; MUST when the divergence already manifests as a bug).
**Do not raise** the comment-only remediation as a finding in its own right; if
extracting the helper is genuinely out of scope for the diff, suggest extraction
in a follow-up ticket and SHOULD-defer rather than asking for a comment.

The deeper principle: the cpp-review persona's purpose is to surface design and
contract issues, not to paper over them with prose. A comment is a documentation
tool for *intent that has no enforcement seam*; it is not a substitute for a
seam that the reviewer chose not to build. When the seam is buildable, build it.

---

*Add new entries below this line as the team learns the persona's blind spots and over-eager patterns. After adding an entry, commit and push -- see [Contributing](../../README.md#contributing).*
