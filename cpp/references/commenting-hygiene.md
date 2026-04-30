# Commenting Hygiene

Shared C++ reference. Loaded by `cpp-write` (step 6, write-time commenting), `cpp-review` (step 9, alongside the modernisation-playbook check), and `cpp-simplify` (step 6, hygiene self-check). Applies to every new or changed class, struct, enum, and function declaration.

The guiding principle is **WHY over WHAT**: comments document intent, contracts, ownership, and non-obvious constraints -- never what the code literally does. A reader who can read C++ already knows what `++i` means.

## Authority and prior art

- **Doxygen** -- canonical tag reference; the `/** */` block style is the Doxygen-recognised multi-line form. Unity's codebase uses this style for public API documentation.
- **LLVM Coding Standards** ("self-documenting code") -- a comment that restates the code adds noise; it ages badly and eventually contradicts.
- **C++ Core Guidelines NL.1 / NL.2** -- "Don't say in comments what can be said in code"; comments explain intent and rationale, not mechanics.
- **AGENTS.md `Authoring & Review Hygiene`** -- "WHY not WHAT"; prohibits roadmap / phase-narrative comments ("Phase D will fix this").

---

## Comment style

Three distinct comment forms; each has a specific role:

| Form | Role | Example context |
| --- | --- | --- |
| `/** */` | Public/user documentation block -- multi-sentence or multi-section Doxygen comment | Class, struct, enum, multi-param function |
| `///` | Public/user documentation line -- single-sentence Doxygen comment | Short function, single-field annotation |
| `///<` | Trailing/right-side Doxygen annotation on the same line | Enum value, struct member |
| `/* */` | Inline developer-aid block -- non-doc, explains implementation behaviour | Multi-line workaround note inside a body |
| `//` | Inline developer-aid line -- non-doc, WHY comment | Single-line body note |

```cpp
/** Multi-line public documentation block.
 *
 * Use when more than one sentence or a tag section is needed.
 */

/// Single-sentence public documentation -- preferred for short declarations.

int m_Count; ///< Current number of live items; excludes pending-destroy.

/* Non-doc block: explains a non-obvious implementation constraint that
   spans more than one line but does not belong in the API surface. */

// Non-doc line: explains a non-obvious choice in the body (WHY, not WHAT).
```

---

## Class / struct doc template

```cpp
/** One-sentence purpose statement -- what problem this type solves,
 *  not a list of its members.
 *
 * Longer description when needed: key design decisions, when to use this
 * type vs. an alternative, important constraints or invariants the caller
 * must respect.
 *
 * Ownership:     [who creates | who destroys | who may hold a non-owning ref]
 * Thread-safety: [safe | unsafe | reads safe; writes require <mutex name>]
 *
 * @note Any important caveat for callers (e.g. must call Init() before use;
 *       elements must be trivially relocatable; not safe to copy across
 *       module boundaries).
 * @see  RelatedType, FactoryFunction
 */
class Foo : public Singleton<Foo>
{
    ...
};

/// Single-sentence variant -- preferred when no tags or extra paragraphs are needed.
class Bar {};
```


**Prefer implicit brief (autobrief).** The first line of a `/** */` block or a `///` line is treated as the brief without an explicit `@brief` tag. Do not write `@brief` unless tooling requires it. The brief should state the role the type plays in the system, not its implementation: "Caches the result of ParseConfig() for the process lifetime" beats "Contains m_Config and m_Cached".

**What goes in Ownership / Thread-safety**: these are the two most common causes of misuse when they are absent from the header.

---

## Function / method doc template

```cpp
/** One-sentence summary (imperative mood: "Returns", "Registers",
 *  "Parses").
 *
 * Longer description only when the behaviour is non-obvious from the
 * signature and the brief.
 *
 * @param[in]  name      Description (omit only when unambiguous from type
 *                       alone, e.g. a single `bool enabled`).
 * @param[out] result    Populated on success; left unmodified on failure.
 * @param[in,out] state  Read on entry; updated on return.
 * @return     What the return value represents; what false / null / empty
 *             signals (failure? not-found? no-op?).
 * @pre        Precondition not expressible in the type system -- e.g.
 *             "Must call Create() before this function."
 * @note       Thread-safe. | Not thread-safe -- caller must hold m_Mutex.
 * @note       noexcept: terminates (via Assert / std::terminate) if the
 *             underlying <call> throws; this is intentional because [reason].
 * @see        RelatedFunction
 */
[[nodiscard]] std::optional<Foo> TryResolve(core::string_ref name) noexcept;
```

**Omit `@param` when**: the parameter name + type together leave no ambiguity and the function has a clear brief. Never omit when the parameter has non-obvious directionality, units, or a null/empty contract.

**Always include `@return`** when the return type is not `void` and the meaning of the return value is not fully captured by the function name and type.

---

## Severity-tiered finding table

| Tier | Rule |
|---|---|
| **MUST** | Public API whose semantics cannot be inferred from name + type alone (lifetime, ordering requirement, thread-safety, memory ownership) has no doc comment |
| **MUST** | A comment directly contradicts the current code (stale comment) |
| **SHOULD** | A class or struct has no brief (first doc-comment line) |
| **SHOULD** | A raw-pointer member has no ownership annotation (owning / non-owning / optional-owning) |
| **SHOULD** | A `#if ENABLE_UNIT_TESTS_WITH_FAKES` block (or equivalent test-bypass) has no `@note` explaining why the production code path is bypassed |
| **SHOULD** | A `noexcept` function wraps a potentially-throwing call with no `@note` documenting the terminate-on-failure contract |
| **SHOULD** | A `// TODO` or `// FIXME` has no `[TICKET-NNN]` tracker reference |
| **SHOULD** | A `@pre` precondition is documented in prose but could instead be encoded in the type system (use the idiom-checklist ordering-contract rule) |
| **NICE** | `/** */` block used where a single `///` line would suffice |
| **NICE** | Brief restates the function name verbatim ("Gets the foo" on `GetFoo()`) |
| **NICE** | `@param` documents a parameter whose name + type already carry full meaning |

---

## What NOT to comment — suppress list

Raise **no** finding for absent comments on any of the following:

- **Self-evident one-liners** in function bodies: `++i`, `return m_Name`, `m_Mutex.lock()`.
- **Names that already encode intent**: `IsBackgroundWorker()`, `kMaxRetryCount`, `m_Cached` -- these need no comment.
- **Trivially obvious getters/setters** with a single line of implementation and an unambiguous name.
- **Phase / roadmap narrative**: "Phase D will fix this", "Temporary until migration completes" -- these are banned by AGENTS.md and should be replaced with a `// [TICKET-NNN]` reference, not a longer comment.
- **`#include` directives, `using` declarations, `namespace` blocks** -- commenting these is noise.

---

## Unity-specific comment conventions

These are additional to generic Doxygen hygiene.

### `// LEGACY:` marker

```cpp
// LEGACY: pre-dates core::string; kept for ABI compatibility with Platform X.
//         Migrate callsites to StrICmp() when touching this module. [TICKET-NNN]
const char* LegacyStringCompare(const char* a, const char* b);
```

Use `// LEGACY: [reason] [ticket]` on any intentionally preserved legacy pattern. The comment makes clear this is deliberate, not overlooked, and signals to the next reader that there is a migration path.

### `// [TICKET-NNN]` on workarounds

Every workaround, suppression, and deviation from the playbook must carry a tracker reference. The comment should explain the constraint that forced the deviation:

```cpp
// [TICKET-12345] core::hash_map not available in this pre-kernel layer;
// using std::unordered_map here until NativeKernel bootstrap is resolved.
std::unordered_map<core::string_ref, int> m_EarlyMap;
```

### `PolicyViolationAllowList` entry comments

Every entry added to `Tools/PolicyViolationDetector/src/PolicyViolationAllowList.gen.h` must have a companion comment naming:
1. Why the violation exists.
2. The rollout plan to retire it (or "permanent" with justification).
3. The tracking ticket.

The allow list is explicitly designed to shrink over time; an uncommented entry has no retirement pressure.

### Memory ownership on raw pointer members

```cpp
class Renderer
{
    Device* m_Device;          // non-owning; lifetime managed by RenderSystem
    Texture* m_ScratchTexture; // owning; allocated in ctor, freed in dtor
};
```

Every raw pointer member in a new or changed class must carry an ownership annotation. The acceptable forms are: `// owning`, `// non-owning`, `// non-owning; lifetime exceeds this object`, `// optional-owning (nullptr when inactive)`.

### `#if ENABLE_UNIT_TESTS_WITH_FAKES` bypass note

```cpp
/** Returns the current platform context.
 *
 * @note In test builds (ENABLE_UNIT_TESTS_WITH_FAKES), the cached value
 *       is bypassed and recomputed each call so fixtures can install fakes.
 *       The production path caches on first call. If you see this note,
 *       prefer migrating the accessor to Singleton<T> (see modernisation-
 *       playbook.md > Globals, singletons, and testability seam).
 */
```

Any accessor that has a test-only bypass branch **must** document it in the public `@note`. Undocumented bifurcation causes mysterious test failures.

---

## Worked examples

### Example A -- missing brief on a new class (SHOULD)

```text
N. [SHOULD] Runtime/Foo/FooManager.h:12 -- `FooManager` has no doc comment.
   A reader cannot tell from the name alone whether this is the owner of
   all Foo instances, a registry, a factory, or a coordination layer.
   Evidence: commenting-hygiene.md SHOULD rule: "class has no brief".
   Suggested:
     /** Owns and coordinates the lifecycle of all active Foo objects
      *  for the current process. One instance per process; access via
      *  FooManager::GetInstance().
      *
      * Thread-safety: GetInstance() is thread-safe; mutating methods are not.
      */
```

### Example B -- stale comment (MUST)

```text
N. [MUST] Runtime/Bar/BarCache.cpp:88 -- the comment says "returns nullptr
   on cache miss" but the function signature changed to return
   std::optional<Bar> in this PR; a caller reading the comment will
   misuse the API.
   Evidence: commenting-hygiene.md MUST rule: "comment contradicts current code";
             line 88 comment vs. line 31 declaration.
   Suggested: update the comment to describe the optional return and what
              std::nullopt signifies.
```

### Example C -- `noexcept` with no termination note (SHOULD)

```text
N. [SHOULD] Modules/Baz/BazProvider.h:44 -- `GetCurrentBaz()` is marked
   noexcept but internally calls `LegacyResolver()`, which is not noexcept.
   A caller who catches exceptions will not see the failure; the process
   terminates instead.
   Evidence: commenting-hygiene.md SHOULD rule: "noexcept wraps potentially-
             throwing call with no @note documenting terminate-on-failure".
   Suggested:
     /**
      * @note noexcept: LegacyResolver() may Assert-fail or throw internally;
      *       in either case this function terminates the process. This is
      *       intentional -- "what resolver am I?" cannot be meaningfully
      *       handled by a caller.
      */
```

---

*Append new entries when the team encounters a recurring comment anti-pattern. Pair with `anti-patterns.md` for suppressions: if a finding type is consistently rejected, add it to the suppress list there, not here. After extending this file, commit and push -- see [Contributing](../../README.md#contributing).*
