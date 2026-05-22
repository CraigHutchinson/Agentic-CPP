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

### File-level `@file` block placement

When a header (or `.cpp`) carries a top-of-file `@file` / `@brief` doc block,
place it **immediately after `#pragma once`** (or after `#include "UnityPrefix.h"`
in a `.cpp` where the precompiled header is mandatory) and **before any
other `#include` directive**:

```cpp
// CORRECT -- header doc block surfaces purpose before dependencies
#pragma once

/** @file Foo.h
 *  @brief One-sentence statement of what this file is for.
 *
 *  Longer description...
 */

#include "Bar.h"
#include "Baz.h"
```

```cpp
// CORRECT -- .cpp variant; UnityPrefix.h stays the mandatory first include
#include "UnityPrefix.h"

/** @file Foo.cpp
 *  @brief Implementation notes for Foo.
 */

#include "Foo.h"
#include "Bar.h"
```

```cpp
// WRONG -- @file block buried after the include list
#pragma once

#include "Bar.h"
#include "Baz.h"
#include "Qux.h"
// ...several more lines of includes...

/** @file Foo.h    // <- reader has already scrolled past this trying to
 *  @brief ...     //    find the declarations and never reads it
 */
```

**Rationale.** A reader's mental order on opening a file is "what is this?"
→ "what does it depend on?" → "what does it declare?". Pattern A matches that
order; Pattern B (after includes) forces the reader past 5–15 include lines
before they reach a statement of purpose, and many readers stop reading at
the include block and start scrolling for declarations. The `@file` block
never gets read in Pattern B except by readers who already know what they
are looking for — at which point it adds no value.

Both placements produce identical Doxygen output; the rule is purely about
how the file reads in source.

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

Five comment forms. Each has exactly one role -- do not substitute one for another.

| Form | Role | When |
| --- | --- | --- |
| `/** */` | Public doc block (Doxygen) | **Any** multi-line doc comment: two or more sentences, or any `@tag` section. This is the only correct multi-line doc form. |
| `///` | Public doc line (Doxygen) | **Exactly one sentence**, no tags. One `///` line per declaration, never stacked. |
| `///<` | Trailing doc annotation (Doxygen) | Same-line annotation on an enum value or struct member. |
| `/* */` | Developer-aid block (non-doc) | Multi-line implementation note inside a function body. |
| `//` | Developer-aid line (non-doc) | Single-line WHY note inside a function body. |

### The multi-line rule

**A doc comment that spans more than one line must use `/** */`.** Stacking
multiple `///` lines to form a multi-line comment is wrong -- it defeats
tooling paragraph-reflow, obscures the block boundary, and creates ambiguity
about whether adjacent `///` lines are one comment or separate briefs.

```cpp
// CORRECT -- multi-line doc uses /** */
/** Resolves the active context for the current thread.
 *
 * Returns nullopt when no context has been bound.
 *
 * @param scope  Limits resolution to the given scope; pass
 *               Scope::Global for an unrestricted lookup.
 * @return The active context, or nullopt.
 */

// CORRECT -- single-sentence doc uses ///
/// Returns the number of registered providers.

// WRONG -- stacked /// lines forming a multi-line comment
/// Resolves the active context for the current thread.
///
/// Returns nullopt when no context has been bound.
///
/// @param scope  Limits resolution to the given scope.
/// @return The active context, or nullopt.
```

Other forms unchanged:

```cpp
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

Public and reusable API functions in headers **must** document every
parameter and every non-void return value with Doxygen tags. The header is
the only surface a caller reads -- undocumented parameters force the caller
into the implementation.

### Required tags

| Tag | Required when |
| --- | --- |
| `@param` | **Every** parameter of a public/reusable function declared in a header. Use directional annotations: `@param[in]`, `@param[out]`, `@param[in,out]`. |
| `@return` | Every non-void return. State what the value represents **and** what sentinel values (false, nullptr, nullopt, empty) signal. |
| `@pre` | Any precondition not expressible in the type system. |
| `@note` | Thread-safety contract; `noexcept` terminate-on-throw contract. |
| `@see` | Cross-references to related declarations when the relationship is non-obvious. |
| `@tparam` | Every template parameter whose name + constraints do not fully convey the contract. |

### Narrow suppressions for `@param`

Omit `@param` **only** when **all** of the following hold:

1. The function is a trivial getter/setter or single-parameter predicate.
2. The parameter name + type together leave zero ambiguity.
3. No directionality, units, null/empty contract, or lifetime semantics apply.

When in doubt, document. A redundant `@param` is a minor style cost; a
missing one is a contract gap.

### `@param` content rules

- **State the contract, not the type.** "The scope to search within" beats
  "A Scope value". The caller can see the type; the comment adds what the
  type does not carry.
- **Document valid ranges, null/empty semantics, and ownership.** "Must not
  be empty; pass `Scope::Global` for unrestricted lookup" is useful.
  "The scope" is not.
- **Use directional annotations consistently.** `[in]` is the default; mark
  `[out]` and `[in,out]` explicitly so the caller knows which parameters are
  mutated.

### Template

```cpp
/** One-sentence summary (imperative mood: "Returns", "Registers",
 *  "Parses").
 *
 * Longer description only when the behaviour is non-obvious from the
 * signature and the brief.
 *
 * @param[in]  name      Identifier to resolve; must not be empty.
 * @param[out] result    Populated on success; left unmodified on failure.
 * @param[in,out] state  Read on entry; updated on return.
 * @return     The resolved Foo, or nullopt if `name` is not registered.
 * @pre        Must call Create() before this function.
 * @note       Thread-safe. | Not thread-safe -- caller must hold m_Mutex.
 * @note       noexcept: terminates (via Assert / std::terminate) if the
 *             underlying <call> throws; this is intentional because [reason].
 * @see        RelatedFunction
 */
[[nodiscard]] std::optional<Foo> TryResolve(std::string_view name) noexcept;

/// Returns the current provider count.
size_t GetProviderCount() const noexcept;
```

The single-line `///` form is appropriate for parameterless or trivially
self-evident functions where no `@param` or `@return` tag is needed.

---

## Severity-tiered finding table

| Tier | Rule |
|---|---|
| **MUST** | Multi-line doc comment uses stacked `///` lines instead of `/** */`. The block form is the only correct multi-line doc form; stacked `///` defeats reflow, obscures block boundaries, and creates brief-vs-continuation ambiguity. |
| **MUST** | Public declaration in a header (class, struct, free function, public method, enum, public constant) has no docblock — even when "obvious from name". The header is the contract; the next maintainer reads only the header. Narrow suppressions apply (see [What NOT to comment](#what-not-to-comment--suppress-list)). |
| **MUST** | Public API whose semantics cannot be inferred from name + type alone (lifetime, ordering requirement, thread-safety, memory ownership) has no doc comment |
| **MUST** | Public/reusable header function has undocumented parameters -- every parameter requires `@param[in\|out\|in,out]`. Narrow suppression: trivial getter/setter or single-parameter predicate where name + type leave zero ambiguity. |
| **MUST** | Public/reusable header function has a non-void return with no `@return` tag. The tag must state what the value represents and what sentinel values (false, nullptr, nullopt, empty) signal. |
| **MUST** | A comment directly contradicts the current code (stale comment) |
| **MUST** | A comment, commit message body, or PR description destined for trunk contains a bare line-number reference to another file (`Foo.cpp:1037`, "around line 1037", "line ~1037"). Line numbers drift on any edit. Use the function name, class name, `@see` Doxygen tag, or a commit-pinned permalink instead. See [No bare line-number references in committed prose](#no-bare-line-number-references-in-committed-prose). |
| **SHOULD** | A header carries one or more section-divider banner comments (`// ---- X ----`, `// === X ===`, etc.) — a symptom of multi-responsibility structure that should be a file split or a namespace / type grouping. Single banner separating co-located ADL-required specialisations is exempt. |
| **SHOULD** | A file-level `@file` / `@brief` doc block sits after the `#include` list rather than immediately after `#pragma once` (or `#include "UnityPrefix.h"` in a `.cpp`). The block should surface the file's purpose before its dependencies; placement after includes forces the reader past 5-15 lines of includes to learn what the file is for, and many readers never reach it. Pre-existing Pattern-B files do not need to be flipped speculatively; new and substantially-edited files use Pattern A. |
| **SHOULD** | An implementation-detail comment ("uses a hash map keyed by ...", "branch is faster on x86") sits in a header rather than in the `.cpp` — leaks coupling between contract and current implementation choice |
| **SHOULD** | A class or struct has no brief (first doc-comment line) |
| **SHOULD** | A raw-pointer member has no ownership annotation (owning / non-owning / optional-owning) |
| **SHOULD** | A `#if ENABLE_UNIT_TESTS_WITH_FAKES` block (or equivalent test-bypass) has no `@note` explaining why the production code path is bypassed |
| **SHOULD** | A `noexcept` function wraps a potentially-throwing call with no `@note` documenting the terminate-on-failure contract |
| **SHOULD** | A `// TODO` or `// FIXME` has no `[TICKET-NNN]` tracker reference |
| **SHOULD** | A `@pre` precondition is documented in prose but could instead be encoded in the type system (use the idiom-checklist ordering-contract rule) |
| **SHOULD** | A cross-reference comment leads with a bare pointer (`// see Foo.h @file`, `/* per AGENTS.md ... */`, `@ref X` as the opening line) or carries only the pointer with no local gist. The reader of the consumer site is forced into a lateral jump to learn the local property the pointer is justifying. Reorder gist-first / pointer-last, or add a one-line gist if none exists. See [Cross-reference hygiene -- local gist before lateral pointer](#cross-reference-hygiene----local-gist-before-lateral-pointer). |
| **SHOULD** | A comment at a consumer site re-documents a project-wide convention or invariant (static-init no-heap rule; engine container choice; `noexcept` terminate-on-throw policy; allocator-tag idioms; etc.). The convention belongs in **one** canonical place (project `AGENTS.md`, a contributing doc, the primitive's `@file` block, or an org overlay such as `unity-commenting.md`); restating it at every consumer teaches no new property and trains readers to expect the same paragraph elsewhere. Trim to a one-line pointer, or remove entirely when the choice is the only project-conforming option. See [Project-wide invariants belong in one canonical place](#project-wide-invariants-belong-in-one-canonical-place). |
| **SHOULD** | A breadcrumb comment (cross-file sequencing, callback priority, boot-time ordering, static-init dependency) re-derives the priority value, the registration/sort mechanism, the standard semantics of `numeric_limits::min`, or the platform-mains call sequence — facts an expert reader gets by following the named anchor functions and reading the upstream primitive. Name the off-screen anchors (functions, files, types) and stop. See [Breadcrumb comments — name the anchor, do not re-derive](#breadcrumb-comments--name-the-anchor-do-not-re-derive). |
| **SHOULD** | A `//` body comment block of two or more lines carries only one load-bearing fact -- subsequent lines are paraphrase, pointer-tail (*"see also ..."*), or sibling-consequence the reader does not need to follow the local code. Multi-line shape implies multi-fact density; collapsing to a single line preserves the signal and reduces visual weight. Exception: hard-wrap when the single line genuinely exceeds the project column limit. See [One-liner viability -- collapse when the load-bearing fact fits](#one-liner-viability----collapse-when-the-load-bearing-fact-fits). |
| **SHOULD** | A preamble comment justifies *why* statement X exists when X's consumer is within ~5 non-blank lines (same scroll viewport, no scrolling required to see both). The reader will reach the consumer before they need the justification; the comment teaches what the code is about to show. Remove the preamble; surface any non-local property at the destination it actually documents (the producer's header, or the consumer's call site). See [Local-use-proves-purpose -- don't preamble code the reader will see immediately](#local-use-proves-purpose----dont-preamble-code-the-reader-will-see-immediately). |
| **SHOULD** | A class, struct, or namespace docblock contains prose that paraphrases content already asserted by one or more of its own members' docblocks (member brief, member detail, `///<` trailing annotation, nested-type docblock). The type docblock should retain only the @brief, type-level purpose / canonical-example prose, type-level invariants that span ≥2 members, and `@section` content referenced by ≥2 members. Move overlapping sentences to the member that owns them, or delete the type-level copy when the member's wording is already adequate. See [Type docblock — explain the type, not its members](#type-docblock--explain-the-type-not-its-members). |
| **SHOULD** | A Doxygen `@section` or `@anchor` has exactly **one** `@ref` consumer in the file (or module, for primitive `@file` anchors). The anchor's content moves to the single consumer; the anchor declaration and the `@ref` are both deleted. Single-consumer anchors do not earn the upward lateral jump they impose on every reader of the consumer. See [`@section` and `@anchor` — earn the indirection with ≥2 consumers](#section-and-anchor--earn-the-indirection-with-2-consumers). |
| **MUST** | A Doxygen `@section` or `@anchor` has **zero** `@ref` consumers — the anchor is dead. Either a `@ref` was removed without cleaning up, or the anchor was speculative. Delete the anchor and any content framing it justified. See [`@section` and `@anchor` — earn the indirection with ≥2 consumers](#section-and-anchor--earn-the-indirection-with-2-consumers). |
| **SHOULD** | A comment block within a function body exceeds ~8 non-blank lines, or a `/* */` block exceeds ~5 lines. Length is a signal, not a defect in itself: apply the **density test** to each sentence — could an expert C++ reader, familiar with the project's libraries and idioms, derive it from reading the code and its immediate vicinity? Candidates for removal: sentences restating what the code immediately below does (WHAT over WHY); descriptions of well-known standard library or API behaviour that the expert reader already knows (e.g. what `std::from_chars` guarantees on overflow, what `sscanf` does with a negative unsigned value); summary sentences that restate a point already made earlier in the same block. Worth keeping: the rationale for a non-obvious design choice (why `-` is intentionally rejected on unsigned `T` rather than wrapped); cross-file invariants (why two surfaces share the same whitespace predicate); concrete edge-case input examples that show the boundary being defended. Raise as **SHOULD** with a trimmed version. See [Example E](#example-e----verbose-inline-comment-block-should). |
| **NICE** | `/** */` block used where a single `///` line would suffice |
| **NICE** | Brief restates the function name verbatim ("Gets the foo" on `GetFoo()`) |
| **NICE** | `@param` on a trivially self-evident parameter (suppression-eligible) adds noise -- prefer removing it |

---

## No bare line-number references in committed prose

Comments, commit messages, PR descriptions, and `@see` tags destined for trunk **must not** contain bare line-number references to other files. Lines drift the moment any file is edited; a comment that says *"see `Foo.cpp` around line 1037"* is wrong on the next refactor and silently misleads every reader from then on.

| Reference form | Stable? | Use it? |
| --- | --- | --- |
| `Foo.cpp` (filename only) | yes | yes |
| `Foo::Bar()` (function name) | yes — survives moves within the file | yes |
| `class Foo` / `struct Foo` (type name) | yes | yes |
| `@see Foo::Bar` Doxygen tag | yes — tooling resolves the symbol | preferred |
| Permalink to a commit-pinned line on a hosted repo | yes — frozen by SHA | yes, when a specific historical state matters |
| `Foo.cpp:1037` / "around line 1037" / "line ~1037" in prose | **no** | **never in committed prose** |

`Foo.cpp:1037` is fine in *findings reports* and *review comments* — they are tied to a specific state of the diff and are read once. It is **not** fine in code comments, commit message bodies, PR descriptions, or any artefact that lands on trunk.

### Severity

| Form | Severity |
| --- | --- |
| Bare line number in a header `@see` or doc comment that ships to trunk | **MUST** -- replace with function/class name or stable anchor |
| Bare line number in a commit message body for a commit that ships to trunk | **MUST** -- amend if pre-publish, follow-up if post-comment |
| Bare line number in a PR description | **SHOULD** -- the description is editable, swap to a stable anchor |
| Bare line number in a review comment | -- (allowed; the comment is tied to the review state) |

### Worked example

```cpp
// WRONG -- line number will drift
/** ... The Editor re-inits BootConfig a second time from
 *  ProjectSettings/boot.config (see Application.cpp around line 1037). */

// CORRECT -- stable function-name anchor
/** ... The Editor re-inits BootConfig a second time from
 *  ProjectSettings/boot.config (see Application::ReloadBootConfig). */

// CORRECT -- @see tag, tooling-resolvable
/** ... The Editor re-inits BootConfig a second time from
 *  ProjectSettings/boot.config.
 *  @see Application::ReloadBootConfig */
```

If the cited site has no nameable function (e.g. an inline block in `main()`), promote it to a named helper as part of the change that needs to reference it. *"There's nowhere stable to point at"* is itself a finding -- raise the named-function refactor as a SHOULD rather than landing a line-number reference.

---

## Cross-reference hygiene -- local gist before lateral pointer

When a rationale applies to two or more sites (a contract, an invariant, a lifetime guarantee, a threading discipline, a design trade-off), state it in **one canonical place** and reference it from each consumer. The canonical place is the upstream primitive's `@file` block, the shared header's class-level `@brief`, the project `AGENTS.md` clause, or a Doxygen `@section` anchor -- whichever is the "home" for the rationale. Do not duplicate the full prose at every consumer.

Each consumer site then carries a **local one-line gist plus the pointer**:

> **Gist first, pointer last.**

The gist conveys the load-bearing local property so a reader can understand the local logic without taking the lateral jump. The pointer is for the reader who wants the full detail -- they would have followed it anyway. Both costs are paid; the gist is free.

### Anti-pattern: bare pointer with no preceding gist

```cpp
// Lifetime, threading, and trivial-destructor contract: see
// `LinkedRegistry.h` @file. Magic-statics make the `s_Global`
// construction itself thread-safe; chain mutation is not, and
// relies on BootConfig's single-threaded boot-time registration.
```

The opening sentence is the pure pointer. The reader hits *"Lifetime, threading, and trivial-destructor contract: see ..."* and is told *what kind* of comment this is and *where to look* -- but not *what the local property is*. The substantive gist is buried in sentences 2-4; a reader scanning the file may stop at the lateral-reference cue and never read the actual property.

### Pattern: gist + pointer

```cpp
// Magic-statics make `s_Global` construction thread-safe; chain
// mutation is single-threaded boot-time only, and the trivial
// destructor keeps cross-TU node-destructor ordering safe.
// Full lifetime / threading contract at the top of `LinkedRegistry.h`.
```

The reader takes away the three local properties (construction safety, mutation discipline, destructor reasoning) on the first read. The pointer is a one-line lead-out for the reader who wants the upstream contract in full. Same total length; better-ordered.

### Pointer phrasing -- prefer plain English over pseudo-Doxygen suffixes

The natural English form is *"at the top of `<file>`"* or *"in `<file>`'s file-scope doc"*. Avoid the trailing pseudo-markup form `<file> @file` (as in *"see `LinkedRegistry.h` @file"*) -- `@file` is a Doxygen command that *declares* a block as the file-level doc when placed inside that block; it does not work as a suffix-noun referring to such a block from elsewhere. The trailing-`@file` form does not resolve to anything in Doxygen, breaks the sentence's English cadence, and reads as cargo-cult markup.

| Form | Verdict |
| --- | --- |
| *Full contract at the top of `LinkedRegistry.h`.* | OK -- plain English, points to where the `@file` block actually lives |
| *Full contract in `LinkedRegistry.h`'s file-scope doc.* | OK -- equivalent phrasing |
| `@see LinkedRegistry.h` (on its own line in a `/** */` block) | OK -- standard Doxygen `@see` resolves to the file's documentation page when the file carries an `@file` block |
| *Full contract in `LinkedRegistry.h` @file.* | **wrong** -- pseudo-markup; `@file` is not a referring construct |
| *see @file* (self-reference) | **wrong** -- same reason; use *"see the file-scope contract block above"* or drop the pointer entirely |

### When pure pointers are fine

Doxygen `@see` / `@sa` between **peer** declarations is a navigation aid, not a stand-in for rationale:

```cpp
/// @see RelatedType, SiblingFunction
```

That is navigation, not rationale. The rule fires when the pointer would have been a rationale comment in its full form.

A single-line pointer is also fine when it follows immediately after a substantive doc block that already carries the gist -- e.g. a class-level `@brief` that fully establishes the contract, with a member function's `@note` saying *"see class-level brief for the lifetime contract"*. The gist already lives in the reader's immediate context, so the pointer alone closes the loop.

### Detection signal

A comment that opens with one of the following, with no preceding local content of its own:

- *see `<other file or symbol>`*
- *as documented in ...*
- *per ...*
- *for rationale ...*
- *for detail ...*
- *same as `<other site>`*
- `@ref <anchor>` or `@see <anchor>` as the first content of the block (peer `@see` lists are exempt -- see above)

Each is a pointer. If subsequent sentences in the same block carry the load-bearing local content, **reorder**: gist first, pointer last. If no subsequent sentences carry local content, **add a one-line gist** -- the link alone is insufficient.

### Severity

| Form | Severity |
| --- | --- |
| Comment whose entire content is a bare pointer to another file (`// see Foo.h @file`) with no local gist | **SHOULD** -- add a one-line gist of the local property the pointer is justifying |
| Comment that opens with a pointer and buries the gist later in the same block | **SHOULD** -- reorder gist-first, pointer-last |
| Comment with gist before pointer (the pattern) | -- no finding |
| Doxygen `@see` / `@sa` listing peer declarations | -- no finding (navigation aid) |

### Worked example

```cpp
// WRONG -- bare pointer leads; reader must lateral-jump to learn the local property
/** Process-wide registry.
 *  See lifetime contract at the top of `LinkedRegistry.h`.
 *  Function-local static; magic-statics handle construction.
 */

// CORRECT -- gist leads; pointer is the lead-out for detail-hungry readers
/** Process-wide registry. Function-local static; magic-statics
 *  guarantee thread-safe lazy construction. Destruction-order
 *  concerns are sidestepped by keeping the destructor trivial --
 *  full lifetime contract at the top of `LinkedRegistry.h`.
 */
```

The wrong form pays the lateral-jump cost on every read; the correct form pays it only when the reader wants the full upstream rationale, which is precisely the reader the pointer is there to serve.

Both examples above use plain English (*"at the top of `LinkedRegistry.h`"*); avoid the pseudo-Doxygen suffix form *"in `LinkedRegistry.h` @file"* described in the previous subsection.

---

## Breadcrumb comments — name the anchor, do not re-derive

A *breadcrumb* comment surfaces a dependency the reader cannot see locally — a cross-file sequencing constraint, a platform-mains call order, a callback-priority ordering that determines when a function fires, an interaction with a later boot phase. The dependency is real and worth recording; the local code shows only the consequence (the `RegisterRuntimeInitializeAndCleanup` line, the priority literal, the registration object).

The rule: a breadcrumb comment **names the off-screen anchors** — functions, files, types — and stops. An expert C++ reader, given the names of the upstream functions, the local signature, and the surrounding registration mechanism, can derive the *mechanism* in under a minute by following the anchor. The comment should not do that derivation for them.

This is a sibling of [Cross-reference hygiene — local gist before lateral pointer](#cross-reference-hygiene----local-gist-before-lateral-pointer) — that rule is about **format** (gist first, pointer last). This rule is about **content** (name the anchor; do not re-explain what following it would reveal).

### Signature shape

- A registration or call site whose timing/ordering matters in ways the local declaration alone cannot convey, **and**
- A comment whose body **explains the priority value, the registration/sort discipline, the standard meaning of a library construct, or the platform-mains call sequence** — facts derivable by following one or two named anchors.

When both hold, the comment is over-deriving. Trim to the anchor names.

### Detection signal

A multi-line comment on a boot-time registration, a callback-priority site, a static-init constructor, or a cross-platform sequencing dependency, where:

1. The comment names the relevant off-screen anchor(s) (good).
2. The comment also restates what the priority value means, what the sort discipline does, what `std::numeric_limits<int>::min()` is, what the registration class invokes, or how the platform mains are structured (bad — derivable from the anchor).
3. A reader who knew the anchor functions and read each for one minute would gain nothing from the restated content.

The **anchor-derivation test**: if every sentence in the comment could be reconstructed by reading the named functions/types it points at, the comment is doing the reader's follow-up for them. Keep only sentences that hold *additional* properties (a consumer-specific quirk, a behavioural sentinel, an interaction with a sibling component the anchors do not document).

### Exception — consumer-specific interactions

A breadcrumb site may carry a specific property the anchors do not cover — e.g. *"the editor's later `BootConfig::InitFromString` (project boot.config) is not picked up"* is not visible from following `AutoInitializeAndCleanupRuntime`; it is a property of *this* callback's timing relative to a *later* boot phase. That property is worth recording. The boundary is the anchor-derivation test: if the property is *specific to this site and its relationship to a later/earlier phase*, it stays; if it is *the mechanism the anchor itself implements*, it goes.

### Severity

**SHOULD** — trim to one or two lines that name the anchors and stop. Keep only properties that are *not* derivable from the named anchors plus the local code.

### Worked example

```cpp
// WRONG — re-derives what the named anchors already encode
// Sequencing: priority `numeric_limits<int>::min()` runs this first among
// `RegisterRuntimeInitializeAndCleanup` callbacks. Platform mains call
// `SetupArgv` then `BootConfig::Init(argv)` before constructing
// `AutoInitializeAndCleanupRuntime`, so the global config is populated by
// the time this fires. The editor's later `BootConfig::InitFromString`
// (project boot.config) is not picked up — this matches the pre-migration
// `HasARGV` behaviour, which only saw the command line.
static RegisterRuntimeInitializeAndCleanup s_SetupStacktraceTypes(
    SetupStacktraceTypes, nullptr, std::numeric_limits<int>::min());

// CORRECT — names the off-screen anchors and stops; reader follows them for detail
// Sequencing: invoked via `AutoInitializeAndCleanupRuntime`, which platform
// mains construct after `SetupArgv` + `BootConfig::Init(argv)`. The editor's
// later `BootConfig::InitFromString` (project boot.config) is not picked up.
static RegisterRuntimeInitializeAndCleanup s_SetupStacktraceTypes(
    SetupStacktraceTypes, nullptr, std::numeric_limits<int>::min());
```

The dropped sentences re-derived facts the reader gets by following the named anchors: that `numeric_limits<int>::min()` orders this first follows from `RegisterRuntimeInitializeAndCleanup::Sort`'s lower-order-first discipline; that the global config is populated by the time this fires follows from reading either platform `main` for the call order. The kept paragraph names the three anchor functions that together pin the sequencing, plus the one property — the later editor `InitFromString` not feeding this callback — that the reader cannot derive by following any single anchor.

---

## Project-wide invariants belong in one canonical place

When the codebase has a project-wide convention or invariant -- a rule that holds at every site of the same shape, not just this one -- documenting that convention *at the consumer site* is duplication. The convention belongs in **one** canonical place: the project `AGENTS.md`, a contributing doc, an `@file` block on the primitive that enforces the rule, an org overlay such as `unity-commenting.md`, or a Doxygen `@section` anchor. Each consumer should not carry its own restatement of the rule -- a reader trained by one such restatement starts expecting the same paragraph at every consumer of the same convention, and the cumulative tax across the codebase is real.

This is a distinct finding from the cross-reference hygiene rule: that rule says when you *do* cross-reference, lead with the gist. **This** rule says you often do not need a comment at the consumer at all -- the choice flows from a project-wide convention and is the only conforming option, so the absence of a comment is itself project-conforming.

### Signature shape

- An *implementation choice* at the consumer that is **the only project-conforming option** for that slot (the rule leaves no genuine choice to make), and
- A comment whose body **explains the rule itself** as if the reader had not internalised it.

When both hold, the comment is restating project-wide convention. Trim it.

### Detection signal

A multi-line comment block at a static-lifetime object, a `noexcept` function, a `core::vector` / `core::array_ref` declaration, an `Assert*` site, an allocator-tag selection, or any other slot governed by a project-wide rule, where:

1. The body of the comment *explains the rule*, not a local property.
2. Removing the comment would not change a project-experienced reader's understanding of why the choice was made.
3. The same paragraph could be copy-pasted, verbatim, to every other consumer of the same rule without losing accuracy. **This is the test.** If the answer is yes, the paragraph belongs upstream, not here.

### Exception -- consumer-specific interactions

A consumer site may carry a *specific* property the convention does not cover -- a non-obvious interaction between the convention and this particular consumer's needs (a non-default allocator tag justified by this consumer's lifetime pattern; a `noexcept` whose terminate-mode is load-bearing for *this* call site's invariants; a fixed-capacity choice driven by this consumer's bounded input). That property is worth a comment. The boundary is still the copy-paste test: if the property is *specific to this site*, it stays; if it is *the rule itself*, it goes.

### Severity

**SHOULD** -- trim to a one-line pointer or remove entirely, depending on the convention's visibility. If the rule is not documented in a canonical place yet, add it there as part of the same change rather than landing it inline at the consumer.

### Worked example

```cpp
// WRONG -- re-documents the project-wide static-init invariant at one consumer
// `-forceFullStacktrace` accepts a list of LogType-name tokens; the token
// table is enumerated from `LogTypeToString` so the spelling stays in
// lockstep with the enum's own stringifier. Backed by `std::array` so the
// storage is part of the static object rather than a heap allocation --
// `s_ForceFullStacktrace` below is a TU-static whose constructor runs
// during dynamic initialisation, before `MemoryManager` is fully up, so
// a `core::vector` here would crash on the first allocation.

// CORRECT -- keeps only the consumer-specific WHY (lockstep with stringifier)
// `-forceFullStacktrace` accepts a list of LogType-name tokens; the token
// table is enumerated from `LogTypeToString` so the spelling stays in
// lockstep with the enum's own stringifier.
```

The dropped paragraph is the project-wide rule: every TU-static in the engine is subject to the MemoryManager-not-ready-during-dynamic-init constraint. Documenting that constraint at one site teaches no new property -- the choice of `std::array` over `core::vector` is the only conforming option for any TU-static of this shape, and the rule lives once in the engine's static-init documentation. The kept paragraph is what the *next* maintainer cannot infer from the language or the project conventions alone: the token list is intentionally enumerated from the enum's stringifier so the two stay in lockstep.

The copy-paste test confirms the split: the dropped paragraph would apply verbatim to `s_ApiProfile`, `s_OverrideTextureCompression`, `s_StackTraceLogType`, and every other TU-static `MappedParameter` in the same translation unit. The kept paragraph would not -- it is specific to this consumer's token-table construction.

---

## One-liner viability -- collapse when the load-bearing fact fits

When the load-bearing content of a `//` body comment is a **single fact** -- a one-sentence sequencing constraint, a brief WHY, a single contract claim -- it must be written as a single comment line. Multi-line `// // //` blocks that wrap to a second or third line "for readability" but carry only one fact dilute the signal: a reader scanning a function sees a three-line block and expects three facts; finding two of those lines to be paraphrase, pointer-tail, or sibling-consequence is friction. The same fact in one line carries less visual weight, fits more code into the same viewport, and reads in a single glance.

Length is a signal, not a defect in itself. A single-fact `//` line that genuinely exceeds the project column limit (typically 100-120 chars) should hard-wrap to two lines -- that is not the smell. The smell is the *multi-fact appearance* on what is really one fact stretched across lines.

This is a sibling of the verbose-comment heuristic (the ~8-line SHOULD): that rule fires on *long* blocks where the density test removes derivable sentences; **this** rule fires on *short* blocks (2-3 lines) whose entire content was a single fact to begin with.

### Signature shape

- A `//` comment block of 2-3 lines, **and**
- Each sentence after the first either paraphrases the first, adds a non-load-bearing cross-reference pointer-tail (*"see also ..."*), or names a sibling consequence that the reader does not need to know to follow the local code.

### Detection signal

A `// X` / `// Y` / `// Z` block where:

1. Sentence X states the load-bearing fact.
2. Sentences Y, Z are paraphrase (*"so that ..."*), pointer-tail (*"see also ..."*, *"documented in ..."*), or sibling-consequence (*"which means ..."*).
3. A reader who saw only X would understand the local code with no loss.

### Severity

**SHOULD** -- trim to a single line.

### Worked example

```cpp
// WRONG -- three lines for one fact
// Sequencing: AutoInit must follow SetupArgv + BootConfig::Init so the
// runtime-initialize callback list (e.g. SetupStacktraceTypes) sees
// populated state. See the @file block in NativeKernel/Bootstrap/BootConfig.h.
AutoInitializeAndCleanupRuntime autoInit;

// CORRECT -- one line, same load-bearing content
// Sequencing: AutoInit shall be after SetupArgv + BootConfig::Init.
AutoInitializeAndCleanupRuntime autoInit;
```

Sentence 1 (*"AutoInit must follow SetupArgv + BootConfig::Init"*) is the load-bearing fact. Sentence 2 (*"so the callback list sees populated state"*) re-derives mechanism the named anchors already encode -- also a breadcrumb-rule SHOULD on its own. Sentence 3 (*"See the @file block in ..."*) is a bare pointer-tail; the reader who wants the mechanism follows `BootConfig::Init` to its header by name. The single-line form keeps the only fact a reader needs to understand the local code: this construction is ordered relative to the two preceding calls.

---

## Local-use-proves-purpose -- don't preamble code the reader will see immediately

A preamble comment that justifies *why* statement X exists is redundant when X's consumer is within a short scroll distance of X -- typically ~5 non-blank statements, or one screen of code without scrolling. A reader walking the function top-to-bottom does not need the comment to tell them *why* `LocateDataFolder()` runs first: the very next non-blank line uses `GetDataFolder()`. The comment is teaching what the code is about to show.

Length is not the criterion -- even a single-line preamble that re-narrates an immediate use is noise. The criterion is **spatial proximity**: when producer and consumer share a viewport, the consumer documents the producer. The preamble's only legitimate role is when the consumer is *far away* (a different function, a different file, a cross-platform boundary) and the local reader would not see it.

This is distinct from the breadcrumb-comment rule -- breadcrumb fires when the comment names *off-screen* anchors and re-derives what following them would reveal. **This** rule fires when the comment narrates *on-screen* code that follows in the same scroll viewport. Both can be present together on the same block.

### Signature shape

- A comment immediately preceding a producer statement (an init call, a cache primer, a flag set), **and**
- The consumer of that producer's output appears within ~5 non-blank lines, **and**
- The comment's content is exhausted by the producer name + the consumer's existence.

### Detection signal

A comment whose body has the shape:

- *"X is done first so Y can ..."*
- *"set up X here for the Y below"*
- *"X is required before Y ..."*
- *"resolve X before the Z call so ..."*

where Y / Z is visibly present in the same function within ~5 statements of X.

### Severity

**SHOULD** -- remove. If the comment carries a *non-local* property (cross-file constraint, platform-specific gotcha, lifetime contract) move that property to the destination it actually documents -- usually the producer's header or the consumer's call site.

### Worked example

```cpp
// WRONG -- preamble re-narrates immediate uses
// Resolve bundle + data paths before AutoInit so the chdir below and
// the BootConfig::InitFromFileFormatted call can see them. Contract
// and constraints documented at the top of OSXPlayer/Bootstrap.h.
osxplayer_bootstrap::LocateApplicationFolder();
osxplayer_bootstrap::LocateDataFolder(argc, (const char* const*)argv);

[[NSFileManager defaultManager]changeCurrentDirectoryPath:
    [NSString stringWithUTF8String: osxplayer_bootstrap::GetApplicationFolder()]];
if (!BootConfig::InitFromFileFormatted(..., osxplayer_bootstrap::GetDataFolder(), ...))

// CORRECT -- no preamble; GetApplicationFolder / GetDataFolder use sites are the documentation
osxplayer_bootstrap::LocateApplicationFolder();
osxplayer_bootstrap::LocateDataFolder(argc, (const char* const*)argv);

[[NSFileManager defaultManager]changeCurrentDirectoryPath:
    [NSString stringWithUTF8String: osxplayer_bootstrap::GetApplicationFolder()]];
if (!BootConfig::InitFromFileFormatted(..., osxplayer_bootstrap::GetDataFolder(), ...))
```

The contract that the resolve calls run pre-AutoInit lives in `Bootstrap.h`'s `@file` block -- the canonical home for the constraint. The reader walking `main()` learns the *what* by reading three statements; they learn the *why* (pre-AutoInit safety) only if they need to, by following `LocateDataFolder` into `Bootstrap.h`.

---

## Type docblock — explain the type, not its members

A class, struct, or namespace docblock that synthesises what its own members' docblocks already say is duplication. The reader walking the file top-to-bottom encounters the type's docblock first, then the members; if the type docblock tells me "reads expose a `ValueRange` whose iterator yields one `Entry` per occurrence in source order with per-element parse outcome", and `Values()`'s own docblock then says exactly the same thing, one of the two pays its weight and the other is noise. The right home is the member docblock — it sits next to the code that implements the claim, sticks to that one entity, and renders in the API docs at the right place.

The type docblock should hold **only** content that has no natural home on any single member:

- The **@brief** — one sentence stating what role the type plays in the system.
- **Purpose / canonical-example prose** that frames *what kinds of problems* the type solves (a `-forceFullStacktrace LogA -forceFullStacktrace LogB` example is type-level; the implementation of iteration is `Values()`-level).
- **Type-level invariants** that genuinely span ≥2 members — thread-safety policy, allocation discipline, lifecycle contract, the "no-cache" design choice that affects every read.
- **Doxygen `@section` / `@anchor` content** referenced by ≥2 member docblocks (the anchor's content cannot move without breaking the cross-references). See [`@section` and `@anchor` — earn the indirection](#section-and-anchor--earn-the-indirection-with-2-consumers).

Everything else moves down to the member that owns it.

This is distinct from the [Project-wide invariants belong in one canonical place](#project-wide-invariants-belong-in-one-canonical-place) rule: that rule is about a convention that holds across **many sites in the codebase** (the engine's static-init no-heap rule, the `noexcept` terminate-on-throw policy). **This** rule is about claims that hold across **multiple members of one type** — same type-internal scope on both sides of the duplication. The two rules compose: a type docblock should not duplicate either its own members *or* project-wide invariants documented elsewhere.

### Signature shape

A type docblock (`/** ... */` block immediately before a `class`, `struct`, `enum class`, or `namespace { ... }` declaration) containing one or more sentences, sections, or paragraphs whose content is also asserted by:

- A member function's brief or detail block.
- A member field's `///<` trailing annotation.
- A nested-type docblock (`struct Entry { ... }`, `class iterator { ... }`).
- A constructor's `@param` tags.

### Detection signal — the member-overlap audit

For each substantive claim in the type docblock, locate any member docblock that asserts the same thing. The fastest way is the **paraphrase test**: pick a sentence from the type docblock; search the member docblocks for any sentence with the same subject and the same verb (allowing for paraphrasing — *"yields one Entry per occurrence"* vs *"Range over occurrences of the key, in source order"* are the same claim). A match means the type docblock is duplicating.

Three patterns to look for, in order of how often they appear:

1. **Member-enumeration sentences in the type's purpose paragraph.** *"Reads expose a `ValueRange` whose iterator yields one `Entry` per occurrence, in source order, with the parse outcome surfaced per-element."* The verbs (`expose`, `yields`, `surfaced`) name member behaviour; the type's `Values()`, iterator, and `Entry` docblocks all say the same things in their own scope.
2. **Standalone paragraphs documenting a single member's contract.** *"Allocation-free: storage for resolved tokens lives in the bound `Data` and the mapping table; this class owns no buffers."* The class-level "allocation-free" claim is the same fact as `ValueRange`'s own *"Lightweight, allocation-free range over per-occurrence `Entry` values"*.
3. **`@section` sub-sections whose content is the union of member docblocks.** A `@section per_element_failure_surface` whose four claims are each fully stated in `Entry`'s docblock or `Parsed()`'s docblock — the section is a redundant index.

### Exception — type-level invariants that span ≥2 members

Some claims genuinely belong to the type, not to any member. Examples:

- A no-cache / no-allocation policy whose **rationale** (Editor two-step init lifecycle, staleness hazard, cost-benefit) doesn't fit on `Parsed()` alone — it's the design choice for the type as a whole. Keep at type level, optionally as a `@section` if ≥2 members `@ref` it.
- A thread-safety contract that the caller must respect across every public read or write.
- A lifecycle constraint (*"must outlive the bound `Data`"*) that applies whichever member the caller calls.
- A non-obvious canonical-example WHY (the `-forceFullStacktrace` per-log-level case for `MappedParameter<T, Multi>`) that frames the type's purpose. No member's docblock is the natural home for this.

The discriminator is the **member-overlap audit**: if the claim is *also* asserted by a member's docblock, the type docblock is duplicating. If the claim is asserted *only* at the type level, it belongs there.

### Severity

**SHOULD** — trim the type docblock to its @brief, its type-level purpose/example prose, and any type-level invariants that don't overlap with the members. Move every overlapping sentence down into the member that owns it (or simply delete the type-level copy, if the member's wording is already adequate).

### Worked example

See [Example H](#example-h----type-docblock-synthesises-its-members-should) below.

---

## `@section` and `@anchor` — earn the indirection with ≥2 consumers

A Doxygen `@section` or `@anchor` is a named destination — its purpose is to be **referenced** from elsewhere. When the file has exactly one `@ref` consumer for a given anchor, the anchor isn't earning its keep: the reader of the consumer pays an upward lateral jump to read content that would have read more directly if it sat inline at the consumer. When there are zero consumers, the anchor is dead — a reference target nobody references.

The rule: **an anchor needs ≥2 consumers to justify the indirection.** Below that, the anchor's content moves to its single consumer (or is deleted if the content was itself a synthesis of other docblocks — see [Type docblock — explain the type, not its members](#type-docblock--explain-the-type-not-its-members)).

This is a sibling of [Cross-reference hygiene — local gist before lateral pointer](#cross-reference-hygiene----local-gist-before-lateral-pointer) — that rule says *when you keep an anchor, format the pointer correctly* (gist first, pointer last). **This** rule says *whether to keep the anchor at all*. Apply this rule first; the cross-reference rule applies only to anchors that survive the consumer-count audit.

### Signature shape

A `@section <name>` or `@anchor <name>` declaration in a docblock, paired with a count of `@ref <name>` consumers across the same file (and, for module-level anchors, the same module). The discriminator is the consumer count.

### Detection signal

Run a paired grep against the file (or module) for every anchor in the diff:

```bash
# Define-side: every @section / @anchor in the file
rg '^\s*\*\s*@(section|anchor)\s+(\w+)'  <file>

# Reference-side: every @ref against that anchor name
rg '@ref\s+(\w+)'  <file>
```

For each anchor, count consumers. Three outcomes:

1. **0 consumers** — dead anchor. Delete the anchor; either the `@ref` was removed and the anchor wasn't cleaned up, or the anchor was speculative ("someone might want to reference this someday"). **MUST**: remove the anchor and any orphan content the anchor was framing.
2. **1 consumer** — single-consumer anchor. **SHOULD**: inline the anchor's content at the consumer (move the prose down, delete the anchor declaration, delete the `@ref`). If the anchor's content is itself a synthesis of other docblocks (e.g. a `@section per_element_failure_surface` whose claims are also in `Entry::brief` and `Parsed()::brief`), delete both the anchor *and* its content — the consumer's existing docblocks already carry the load.
3. **≥2 consumers** — anchor earns its keep. Leave in place; apply the cross-reference hygiene rule (gist before pointer) to each consumer.

### Exception — module-spanning anchors

An anchor in a primitive's `@file` block whose `@ref` consumers live across many sites in the codebase (e.g. `bootconfig_threading` referenced from every `BootConfig`-consumer site) is in the ≥2-consumer category by definition; the count is across files, not within the defining file. Apply the same rule with module-wide consumer counting.

### Severity

| Consumer count | Severity | Action |
| --- | --- | --- |
| 0 | **MUST** | Delete the anchor and any content the anchor was framing |
| 1 | **SHOULD** | Inline content at the consumer; delete the anchor + the `@ref` |
| ≥2 | -- | Keep; apply cross-reference hygiene |

### Worked example

See [Example I](#example-i----single-consumer-section-anchor-should) below.

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

**Org overlay check:** If `../unity-references/` exists, load any `*-commenting.md` file there after this file. It defines project-specific comment markers (e.g., `// LEGACY:` conventions), policy allowlist entry requirements, and memory-ownership annotation forms that supplement or override the generic rules above.

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

### Example D -- undocumented parameters on public API (MUST)

```text
N. [MUST] Module/Net/ConnectionPool.h:63 -- `Acquire(StringView tag,
   Duration timeout)` is a public header function with two parameters and
   no `@param` tags. A caller cannot tell from the signature what `tag`
   identifies, whether `timeout` is wall-clock or monotonic, or what
   happens on timeout (nullptr? exception? assert?).
   Evidence: cpp-commenting.md MUST rule: "Public/reusable header function
             has undocumented parameters".
   Suggested:
     /** Acquires a pooled connection matching `tag`.
      *
      * Blocks the calling thread until a connection is available or
      * `timeout` elapses.
      *
      * @param[in] tag      Logical pool partition to acquire from; must
      *                     not be empty.
      * @param[in] timeout  Maximum wall-clock wait. Pass Duration::Zero()
      *                     for a non-blocking attempt.
      * @return A live connection, or nullptr if `timeout` elapsed.
      */
```

---

### Example E — verbose inline comment block (SHOULD)

A template function body has a `// ...` block of ~22 lines explaining the integer parse path,
covering: the two input paths (boot.config vs command-line), the `+` sign handling, the `-`
rejection on unsigned types, `std::from_chars` error semantics, and whitespace policy alignment
with another TU's tokeniser.

```text
N. [SHOULD] NativeKernel/Bootstrap/BootConfigParameterData.h:<line> --
   the `// Boot config integer values reach this parser through two paths` block
   runs to ~22 lines for ~15 lines of `std::from_chars` setup; several sentences
   describe standard library behaviour an expert reader already knows.
   Evidence: cpp-commenting.md SHOULD rule (verbose-comment heuristic): density test
             fails on three sentence groups:
               (a) "std::from_chars itself remains strict on the trimmed window:
                   locale-independent, explicit overflow via std::errc::result_out_of_range,
                   and partial parses rejected via result.ptr != last" -- describes
                   documented std::from_chars behaviour; adds nothing the reader would
                   not check in cppreference.
               (b) "The parser accepts that wider input shape (skip leading whitespace,
                   skip one optional '+', trim trailing whitespace)" -- restates what
                   the six lines of code immediately below this comment do.
               (c) "falling back to the configured default is the safer behaviour for
                   boot config integers" -- summary of the preceding `-` rejection
                   rationale; redundant.
             The non-obvious parts worth keeping:
               - the two-path context (boot.config lines are pre-trimmed; command-line
                 tokens arrive verbatim with inner whitespace and '+' prefixes);
               - why `-` on an unsigned type is intentionally rejected (from_chars
                 is strict; the old sscanf path silently wrapped to a large positive);
               - why both surfaces use `IsBlank` (one predicate ensures a value that
                 survives the tokeniser cannot be re-rejected here for a different
                 whitespace definition).
   Suggested trimmed block (~8 lines):
     // Integer values reach this parser through two paths:
     //   boot.config lines are trimmed by InitFromString before arrival;
     //   command-line tokens (e.g. `-gc-helper-count " 4 "`) arrive verbatim with
     //   inner whitespace and optional `+` prefixes.
     // We therefore strip leading/trailing whitespace and one leading `+` before
     // calling from_chars, so both surfaces share one acceptance policy.
     // A leading `-` on unsigned T is intentionally rejected: from_chars is strict
     // where sscanf would wrap to a large positive; defaulting is the safer choice.
     // Whitespace: both surfaces call IsBlank (POSIX-style: ' ' and '\t' only),
     // so a value that clears the tokeniser cannot be re-rejected here.
```

### Example F -- consumer-site restating of a project-wide invariant (SHOULD)

A TU-static `MappedParameter` carries a 7-line comment whose lower half explains the engine's static-init no-heap-allocation rule. The comment is at one consumer; the rule applies to every TU-static of the same shape.

```text
N. [SHOULD] Runtime/Logging/LogAssertExtended.cpp:<line> -- the comment block
   on `GetForceFullStacktraceMappings()` restates the engine's project-wide
   static-init invariant ("`s_ForceFullStacktrace` is a TU-static whose
   constructor runs during dynamic initialisation, before `MemoryManager`
   is fully up, so a `core::vector` here would crash on the first
   allocation") at this one consumer.
   Evidence: cpp-commenting.md SHOULD rule (project-wide invariants belong
             in one canonical place); the lower half of the comment passes
             the copy-paste test -- it would apply verbatim to every other
             TU-static `MappedParameter` in this translation unit
             (`s_ApiProfile`, `s_OverrideTextureCompression`,
             `s_StackTraceLogType`).
             The upper half is consumer-specific (token table enumerated
             from `LogTypeToString` for lockstep with the enum's own
             stringifier) and stays.
   Suggested trimmed block (3 lines):
     // `-forceFullStacktrace` accepts a list of LogType-name tokens; the token
     // table is enumerated from `LogTypeToString` so the spelling stays in
     // lockstep with the enum's own stringifier.
```

### Example G -- breadcrumb comment that re-derives the mechanism (SHOULD)

A boot-time `RegisterRuntimeInitializeAndCleanup` registration carries a 7-line comment whose middle paragraph re-explains the priority/sort discipline that lives in the registration class itself.

```text
N. [SHOULD] Runtime/Logging/LogAssertExtended.cpp:<line> -- the comment on
   `s_SetupStacktraceTypes` re-derives mechanism that an expert reader gets
   by following the named anchor functions:
     * "priority `numeric_limits<int>::min()` runs this first" -- derivable
       from `RegisterRuntimeInitializeAndCleanup::Sort` (lower-order first);
       no new information at the call site.
     * "Platform mains call `SetupArgv` then `BootConfig::Init(argv)` before
       constructing `AutoInitializeAndCleanupRuntime`" -- visible by reading
       one platform `main` (e.g. `WinEditorMain.cpp`).
     * "this matches the pre-migration `HasARGV` behaviour" -- git-blame
       narrative, not a current-code property.
   What stays: the editor's later `BootConfig::InitFromString` (project
   boot.config) not feeding this callback -- that property is not visible
   from any single anchor and is consumer-specific.
   Evidence: cpp-commenting.md SHOULD rule (breadcrumb comments -- name the
             anchor, do not re-derive); anchor-derivation test fails on
             three of four sentences.
   Suggested trimmed block (3 lines):
     // Sequencing: invoked via `AutoInitializeAndCleanupRuntime`, which
     // platform mains construct after `SetupArgv` + `BootConfig::Init(argv)`.
     // The editor's later `BootConfig::InitFromString` (project boot.config)
     // is not picked up.
```

### Example H -- type docblock synthesises its members (SHOULD)

A class docblock for `MappedParameterData<T, Cardinality::Multi>` (a multi-value `BootConfig` parameter view) carries a 38-line docblock with: a purpose paragraph naming the type, a `@section bootconfig_multivalue_no_cache` block, a standalone `Allocation-free` paragraph, and a `@section bootconfig_multivalue_failure_contract` block. Within the same class, dedicated docblocks already exist on the `Entry` nested struct, the `ValueRange` nested class, `Values()`, `Parsed()`, and `iterator::operator*()` -- each carrying the contract of the member it sits on.

```text
N. [SHOULD] Modules/NativeKernel/Include/NativeKernel/Bootstrap/BootConfigParameterData.h:<line> --
   the class docblock on `MappedParameterData<T, Cardinality::Multi>` is 38 lines;
   the member-overlap audit shows multiple paragraphs duplicating the immediately-
   following member docblocks:
     * "Reads expose a `ValueRange` whose iterator yields one `Entry` per occurrence,
       in source order, with the parse outcome surfaced per-element" -- `Values()`'s
       own docblock at <line> says "Range over occurrences of the key, in source
       order. Each element is an `Entry` carrying its own `parsed` flag".
     * "Allocation-free: storage for resolved tokens lives in the bound `Data` and
       the mapping table; this class owns no buffers." -- `ValueRange::brief` at
       <line> already opens with "Lightweight, allocation-free range over per-
       occurrence `Entry` values".
     * Inside `@section bootconfig_multivalue_no_cache`: "Each `Values()` / `Parsed()`
       call walks the bound `Data` afresh, and the iterator re-runs `MatchToken`
       per step" -- `ValueRange::brief` says "Each iterator step re-evaluates the
       underlying `Data` against the bound mapping table".
     * Whole `@section bootconfig_multivalue_failure_contract` (12 lines) -- every
       claim is in `Entry`'s docblock or `Parsed()`'s docblock. Single-consumer
       anchor on top of the duplication (see anchor-consumer rule).
   What stays at type level:
     * The canonical `-forceFullStacktrace LogA -forceFullStacktrace LogB` example
       (no member is the natural home for this).
     * The bare-key rule as a one-line property of the type.
     * `@section bootconfig_multivalue_no_cache` body (Editor two-step init /
       RemoveAll() lifecycle / staleness hazard / cost-benefit) -- >=2 consumers
       (`ValueRange::brief`, `Parsed()::brief`, and the single-value `Parsed()`'s
       brief), so the anchor earns its keep.
   Evidence: cpp-commenting.md SHOULD rule (Type docblock -- explain the type,
             not its members); paraphrase test fires on three sentences and the
             whole failure-contract @section.
   Suggested trim (38 -> 18 lines):
     /** Multi-value mapping-driven parameter -- one `T` per key occurrence.
      *
      *  Models keys whose every command-line occurrence contributes a value;
      *  the canonical example is `-forceFullStacktrace LogA -forceFullStacktrace LogB`
      *  where both `LogA` and `LogB` are wanted, not just the last. A bare
      *  key (`-foo` with no value) contributes nothing: `BootConfig::Data`
      *  stores zero values for it, so it does not surface as an entry.
      *
      *  @section bootconfig_multivalue_no_cache No caching by design
      *
      *  Public reads do not cache. The Editor performs a second
      *  `BootConfig::InitFromString` once the project has been resolved
      *  (`Application.cpp`), which calls `RemoveAll()` and re-populates
      *  `Data` from the project's `boot.config`; a cache populated by the
      *  first init would silently ignore the project's view. These are
      *  load-time arguments with tiny token tables, so the no-cache cost
      *  is well below the staleness hazard of the alternative.
      */
```

The deleted prose was the union of what `Values()`, `ValueRange`, `Entry`, `Parsed()`, and `iterator::operator*()` already say. The kept prose is the type's purpose (problem framing + canonical example), one type-level property (bare-key rule, which no individual member is the natural home for), and the no-cache `@section` whose anchor has three `@ref` consumers and therefore earns the indirection.

### Example I -- single-consumer `@section` anchor (SHOULD)

The same class block carries a second `@section`, `bootconfig_multivalue_failure_contract`. Anchor-consumer grep shows exactly one `@ref` in the file -- the `Entry` struct's docblock at <line>. The anchor's body is 12 lines summarising per-element validity, `Parsed()` as a convenience answer, `Entry::token` for diagnostics, and the "absent key -> vacuously parsed" property.

```text
N. [SHOULD] Modules/NativeKernel/Include/NativeKernel/Bootstrap/BootConfigParameterData.h:<line> --
   `@section bootconfig_multivalue_failure_contract` has exactly one consumer
   in the file:
     $ rg '@(section|anchor)\s+bootconfig_multivalue_failure_contract'  <file>
     <class-block-line>:     *  @section bootconfig_multivalue_failure_contract ...
     $ rg '@ref\s+bootconfig_multivalue_failure_contract'  <file>
     <entry-block-line>:     *  See @ref bootconfig_multivalue_failure_contract ...
   Audit of the anchor's body against the existing member docblocks:
     * "Each `Entry` carries its own parse outcome and source token, so a caller
       can choose how to react: silently skip, log, abort, or collect." --
       `Entry`'s own docblock says "Consumers dispatch via `if (entry.value)`
       and dereference with `*entry.value`; `entry.token` is always non-null
       and carries the source spelling, suitable for failure-path diagnostics".
     * "`Parsed()` is the convenience answer for callers that only need a single
       bool over all occurrences" -- `Parsed()`'s docblock says "True iff every
       occurrence of the key matched the bound table. Vacuously true when the
       key is absent. Sugar over 'every entry's `value` is engaged'".
     * "bad tokens stay available on `Entry::token` for any diagnostic walk" --
       covered by `Entry`'s docblock + `Parsed()`'s "callers that need a per-
       element diagnostic walk `Values()` directly and read `Entry::token`".
     * "An absent key has zero occurrences, so the range is empty and `Parsed()`
       is vacuously `true`." -- `Values()`'s `@return` says "empty when the key
       is absent"; `Parsed()`'s docblock says "Vacuously true when the key is
       absent".
   Outcome: the anchor's content is fully duplicated in the member docblocks
   the single consumer already lives next to. Inlining means moving nothing --
   the consumer's existing prose already carries the load. Delete the anchor,
   delete the `@ref`.
   Evidence: cpp-commenting.md SHOULD rule (`@section` and `@anchor` -- earn
             the indirection with >=2 consumers); consumer count = 1, anchor
             body fully duplicated by member docblocks.
   Suggested change:
     1. Delete the entire `@section bootconfig_multivalue_failure_contract`
        block (12 lines) from the type docblock.
     2. Delete the "See @ref bootconfig_multivalue_failure_contract for the
        bare-key and per-element-validity rules." line (2 lines) from `Entry`'s
        docblock.
     3. Promote the one type-level property that wasn't already in any member
        ("A bare key contributes nothing -- `BootConfig::Data` stores zero
        values for it, so it does not surface as an entry") to the type
        docblock's purpose paragraph.
```

The before/after net: -14 lines of comment text, zero compiled code change. The reader of `Entry`'s docblock learns the same contract without the upward lateral jump; the reader of the type docblock learns the bare-key rule directly in the purpose paragraph. Cross-reference graph after the change has one fewer node, no dangling `@ref`.

The discriminator on this finding is the **consumer count**, not the anchor's content quality: even a well-written single-consumer anchor would still earn the SHOULD, because the indirection cost (every reader of the consumer pays the lateral jump) outweighs the format benefit (none -- single-consumer means no shared destination to standardise). The companion check is "did the anchor's content move?": when the consumer's existing docblock already carries the load (as here), the move is a delete; when the consumer needs the content, the move is a transcription from anchor body to consumer body.

---

*Append new entries when the team encounters a recurring comment anti-pattern. Pair with `cpp-anti-patterns.md` for suppressions: if a finding type is consistently rejected, add it to the suppress list there, not here. After extending this file, commit and push -- see [Contributing](../../README.md#contributing).*
