# Commenting Hygiene

Shared C++ reference. Loaded by `cpp-write` (step 6, write-time commenting), `cpp-review` (step 9, alongside the modernisation-playbook check), and `cpp-simplify` (step 6, hygiene self-check). Applies to every new or changed class, struct, enum, and function declaration.

The guiding principle is **WHY over WHAT**: comments document intent, contracts, ownership, and non-obvious constraints -- never what the code literally does. A reader who can read C++ already knows what `++i` means.

## Authority and prior art

- **Doxygen** -- canonical tag reference; the `/** */` block style is the Doxygen-recognised multi-line form for public API documentation.
- **LLVM Coding Standards** ("self-documenting code") -- a comment that restates the code adds noise; it ages badly and eventually contradicts.
- **C++ Core Guidelines NL.1 / NL.2** -- "Don't say in comments what can be said in code"; comments explain intent and rationale, not mechanics.
- **AGENTS.md `Authoring & Review Hygiene`** -- "WHY not WHAT"; prohibits roadmap / phase-narrative comments ("Phase D will fix this").

---

## Header is the public interface — document it

The header file is the contract a caller sees. The `.cpp` is implementation
detail the caller does not read. The split has direct consequences for
commenting policy:

- **Every public declaration in a header carries a docblock.** Class, struct,
  free function, public method, enum, public typedef, public constant. The
  brief says what role the declaration plays; the longer prose, when needed,
  states the contract a caller cannot infer from name + type alone (lifetime,
  ordering, ownership, thread-safety, error mode). This applies even when the
  declaration "looks obvious" — the next maintainer is not the author and will
  not be reading the implementation.
- **Implementation comments live in the `.cpp`.** Notes about *how* something
  works, why a particular algorithm was chosen, the gotcha that motivated a
  branch, references to specific bug repros — these go next to the code that
  embodies them. Putting implementation notes in the header leaks coupling: a
  reader of the header now has to mentally distinguish "contract" from
  "current implementation choice", and the comment ages with whichever side
  changes first.
- **A `.cpp`-only function (anonymous namespace, file-static) is exempt from
  the header rule** — it has no public surface — but still benefits from a
  docblock explaining intent when the body is non-trivial.

The narrow suppressions in [What NOT to comment](#what-not-to-comment--suppress-list)
still apply (trivially obvious getters / setters with unambiguous names,
self-evident one-liners). The "every public declaration in a header carries a
docblock" rule does **not** force a docblock on `[[nodiscard]] Mode mode() const noexcept { return m_Mode; }`
when `Mode` itself is documented and the getter is trivially named — the
suppress list governs that case. The rule **does** apply to anything whose
contract has lifetime, ordering, mutation, error, or thread-safety semantics
the name does not carry.

### Section-divider banner comments are a smell

Comments shaped like

```cpp
// ---- Concrete subclasses -- facet enums scoped to their own type ----
// ---- Named predicates ----
// ---- Runtime-safe mode helpers (definitions in ProcessContext.cpp) ----
// =================== PUBLIC API ===================
// ////////////// Internal helpers //////////////////
```

are a substitute for structure that the language already provides. They mark
"regions of the file" in prose because the file has grown to hold multiple
distinct responsibilities. The banner is the symptom; the design issue is one
of:

1. **The file should be split.** Two banners separating two responsibilities is
   the file telling you it wants to be two files. Split into
   `Foo.h` + `FooHelpers.h` (or `Foo.h` + `FooFwd.h`, or `Foo.h` + a separate
   public detail header) and let the include relationship carry the meaning.
2. **The grouping should be a type.** Free functions banner-grouped under
   `// ---- predicates ----` are usually candidates for a class with member
   predicates, or a namespace with a clear name (`namespace foo::predicates { … }`).
   The namespace name carries the meaning the banner was trying to convey.
3. **The "definitions live elsewhere" annotation is noise.** A trailing
   `(definitions in Foo.cpp)` on a banner restates what the header / source
   split already implies. If the reader needs that hint, the declaration
   itself is in the wrong file or the file is doing too much.

Raise as **SHOULD**: propose either a split or a namespace / type grouping.
Do not propose "rename the banner" or "remove only the banner" — the banner
is the symptom, not the bug; removing it without addressing the underlying
multi-responsibility structure just hides the smell.

The narrow exception is a **single** banner separating two genuinely
co-located concerns that cannot be split (e.g. a templated public class and
its required out-of-line specialisations in the same header for ADL reasons).
One such banner is acceptable; two banners in the same header is a split
signal.

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
[[nodiscard]] std::optional<Foo> TryResolve(std::string_view name) noexcept;
```

**Omit `@param` when**: the parameter name + type together leave no ambiguity and the function has a clear brief. Never omit when the parameter has non-obvious directionality, units, or a null/empty contract.

**Always include `@return`** when the return type is not `void` and the meaning of the return value is not fully captured by the function name and type.

---

## Severity-tiered finding table

| Tier | Rule |
|---|---|
| **MUST** | Public declaration in a header (class, struct, free function, public method, enum, public constant) has no docblock — even when "obvious from name". The header is the contract; the next maintainer reads only the header. Narrow suppressions apply (see [What NOT to comment](#what-not-to-comment--suppress-list)). |
| **MUST** | Public API whose semantics cannot be inferred from name + type alone (lifetime, ordering requirement, thread-safety, memory ownership) has no doc comment |
| **MUST** | A comment directly contradicts the current code (stale comment) |
| **SHOULD** | A header carries one or more section-divider banner comments (`// ---- X ----`, `// === X ===`, etc.) — a symptom of multi-responsibility structure that should be a file split or a namespace / type grouping. Single banner separating co-located ADL-required specialisations is exempt. |
| **SHOULD** | An implementation-detail comment ("uses a hash map keyed by ...", "branch is faster on x86") sits in a header rather than in the `.cpp` — leaks coupling between contract and current implementation choice |
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

## Project-specific conventions

If an org overlay is present (`../org/references/`), load it after this file. The overlay defines project-specific comment markers (e.g., `// LEGACY:` conventions), policy allowlist entry requirements, and memory-ownership annotation forms.

---

## Worked examples

### Example A -- missing brief on a new class (SHOULD)

```text
N. [SHOULD] Module/Foo/FooManager.h:12 -- `FooManager` has no doc comment.
   A reader cannot tell from the name alone whether this is the owner of
   all Foo instances, a registry, a factory, or a coordination layer.
   Evidence: cpp-commenting.md SHOULD rule: "class has no brief".
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
N. [MUST] Module/Bar/BarCache.cpp:88 -- the comment says "returns nullptr
   on cache miss" but the function signature changed to return
   std::optional<Bar> in this PR; a caller reading the comment will
   misuse the API.
   Evidence: cpp-commenting.md MUST rule: "comment contradicts current code";
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
   Evidence: cpp-commenting.md SHOULD rule: "noexcept wraps potentially-
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

*Append new entries when the team encounters a recurring comment anti-pattern. Pair with `cpp-anti-patterns.md` for suppressions: if a finding type is consistently rejected, add it to the suppress list there, not here. After extending this file, commit and push -- see [Contributing](../../README.md#contributing).*
