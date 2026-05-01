---
name: cpp-write
description: C++ authoring persona. Use proactively before and during authoring new C++ files, classes, or public APIs -- new header/source pairs, new module surfaces, refactors that add public API, and any code destined for cpp-review. Loads the project's idiom, modernisation, commenting, and anti-pattern references before generating any code so the first commit targets zero cpp-review MUST findings.
allowed-tools: Read, Glob, Grep, Bash, Write, Edit
---

# C++ Write

Pre-writing authoring persona. Mirrors the same reference set that `cpp-review` and `cpp-simplify` use, applied proactively so the first commit is already correct rather than correct after a review cycle.

## When to invoke

Invoke proactively when the task includes any of:

- Creating a new `.h` / `.cpp` pair (new class, new module, new utility).
- Adding or changing public API declarations.
- Writing code that owns or interacts with global / process-lifetime state.
- Writing any new utility helper (reinvention-check risk).
- Authoring template types or template methods.
- Implementing code that crosses module, runtime/editor, or platform boundaries.

Skip for: one-line bug fixes, pure comment or wording edits, mechanical renames with zero semantic delta, test-only changes that add no production surface.

## Gaps and assumptions

When a design choice is not covered by the loaded references or the project's AGENTS.md / CLAUDE.md, do not silently pick the more familiar or "safe-looking" option. Surface the gap:

1. **Name the choice** -- state the two or three realistic options concisely (a sentence each).
2. **State the trade-offs** -- type-safety, allocator awareness, testability, ABI stability, migration cost, project constraint applicability.
3. **Ask before writing** -- "I don't see a directive for this; which do you prefer?" A brief answer unblocks authoring and gets captured for future reference.

What this prevents: one pass of "wrong" code followed by a review finding, followed by a rewrite. The ask costs 30 seconds; the rewrite costs a cycle.

When the gap is minor enough that writing both variants in the file would help the user decide, write the shorter one as a placeholder with a clearly labelled `// [GAP: describe choice]` comment, and ask the question inline.

**Do not assume** the modernised option is always preferred. Some modules have explicit freeze policies, project-specific type constraints (see cpp-modernisation.md > Project-specific overlay), or ABI stability requirements that make the standard-library version wrong even when it looks cleaner.

## Reference load (mandatory -- before writing any code)

Load all four references in order before generating any code. They are the shared set also used by `cpp-review` and `cpp-simplify`; code written without them will not survive a review pass.

1. `../cpp/references/cpp-anti-patterns.md`
   -- what NOT to introduce; overriding principle: safety wins are never cosmetic,
      do not suppress a pattern just because migration is expensive.
2. `../cpp/references/cpp-modernisation.md`
   -- C++17 idiom tiers, project-specific type overlay (if org overlay present),
      globals/testability seam pattern.
3. `../cpp/references/cpp-idioms.md`
   -- reinvention catalogue, API design smells, file organisation rules.
4. `../cpp/references/cpp-commenting.md`
   -- doc comment MUST/SHOULD table, doc templates, ownership annotation conventions.

Read these to understand intent, not merely to skim rules. The anti-patterns file's **Overriding principle** is more important than any individual entry in the other three: a change that reduces a class of bug or encodes an invariant in the type system is always raised, never suppressed.

## Authoring checklist

Apply each step in order before and during writing. The steps mirror the four layers of `cpp-review`'s layered design review, applied proactively so there is nothing for a reviewer to find.

### Step 1 -- Reinvention and code-location pre-flight (before creating any file)

**Highest-leverage step.** A utility written from scratch that already exists in the project produces a MUST finding in review and must be deleted or replaced.

1. **Identify the shape** of what you are about to write -- "case-insensitive compare", "argv flag check", "global process-context cache", "small string container".
2. **Grep the reinvention catalogue** (`../cpp/references/cpp-idioms.md > Reinvention catalogue`) for that shape. If `../cpp/unity-references/` exists, also check any `*-reinvention.md` file there -- it carries project-specific utilities that supersede the generic catalogue. If a project utility already covers it, use that utility and stop.
3. **Locate the correct home** for new code by asking: "If a teammate searched for this functionality six months from now, where would they look?"
   - Generic string helper → the project's utility / kernel directory
   - Argv classification → the project's shared utilities layer
   - Process-lifetime global state → derive from the project's `Singleton<T>` or equivalent at the nearest module boundary
   - Feature-local helper → inside the feature module, not a global utility header
4. **Check for a module-level `AGENTS.md`** in the target directory. Module files can override global conventions; read before writing.
5. **Simplification pre-flight.** Before designing any file or type, load `../cpp/references/cpp-idioms.md > Simplification and DRY` and run the signal table. If the proposed design triggers more than one signal (single-implementation abstraction, helper for a single call site, type count exceeding problem responsibility count), stop and ask: is there a simpler correct shape? The cheapest fix is the one that happens before the first line is written.

### Step 2 -- File design (before writing the first line of code)

Apply the **File organisation** rules in `../cpp/references/cpp-idioms.md > File organisation`.

- **`#pragma once`** at the top of every new header. Never use `#ifndef` guards in new code.
- **Filename matches the primary class name** exactly, including casing. `class FooManager` → `FooManager.h` / `FooManager.cpp`. Mismatch causes a build failure on Linux/macOS; Windows masks it.
- **One primary public type per header/source pair.** Tightly-coupled helpers (tag types, trivial RAII guards, return-value structs used only by this API) may share the file; unrelated types must not.
- **Include order in `.cpp`**: corresponding `.h` first, then standard library, then project headers. This catches missing-include bugs in the header immediately rather than hiding them.
- **Headers pull in only what they need.** Forward-declare rather than `#include` whenever a pointer or reference suffices.
- **Public runtime headers** must not `#include` heavy project container types when they can be avoided -- those drag editor-only template instantiations into runtime TUs. Prefer forward declarations and keep heavy types in editor-only headers.

### Step 3 -- Type design (before declaring any class or struct)

Answer these before writing the declaration:

1. **Does this need to be a class?** A type whose every method accesses only its own members and enforces no invariant is a candidate for namespace-scope free functions. No polymorphism requirement and only one foreseeable concrete implementation → no `I` prefix abstraction.
2. **Ownership model.** Who creates, who destroys, who holds non-owning references? Settle this before any member declaration -- it determines whether members are owning (`std::unique_ptr`) or non-owning (raw pointer with an ownership annotation in the doc comment).
3. **Global or process-lifetime state?** Any member variable that lives beyond a single call stack frame -- a cache, a registry, a "computed once" value -- must pass the testability seam test:
   - Does a test need to exercise an alternative value? → **Use the project's `Singleton<T>`** or equivalent CRTP singleton utility. Never introduce a file-static or function-local static for cached state; both are testability-hostile in exactly the same way.
   - Is the value genuinely process-immutable (compile-time-derived, no test could need an alternative)? → A file-static is acceptable; document the suppression reason with a `// [TICKET-NNN]` reference and the cpp-anti-patterns.md justification.
   - **Never** introduce a test-build conditional bypass branch. That branch is evidence that the design is testability-hostile, not a solution to it. If you find yourself wanting one, redesign around the project's singleton utility first.
4. **Class member ordering:** public before private. Within each section: type aliases → static constants → constructors/destructor/assignment → methods (most important first) → private types → private methods → data members.

### Step 4 -- API declaration (before implementing any method)

Apply to every new or changed public declaration.

**Names:**

- **Verb + noun** for mutators: `RegisterCallback`, `BuildIndex`, `ClearCache`.
- **`Is` / `Has` / `Can`** prefix for predicates: `IsEnabled()`, `HasPendingWork()`.
- **`Get`** only for cheap, non-allocating observers. Use `Compute`, `Build`, or `Resolve` when the function does real work.
- **`Try`** prefix for functions that may fail: `[[nodiscard]] std::optional<T> TryResolve(...)`.
- **Named predicates** over enum comparison at call sites: `IsBackgroundWorker()` instead of `GetMode() == Mode::Background`.

**Contract attributes:**

- Apply `[[nodiscard]]` per `cpp-idioms.md > [[nodiscard]] heuristics`. When in doubt: if discarding the return value is almost certainly a caller error, add it.
- Apply `noexcept` per `cpp-idioms.md > noexcept heuristics`. Pure observers and default/move constructors are `noexcept` by default.
- Use `static_assert` to encode type contracts knowable at compile time (POD-ness, size, enum exhaustiveness).

**API design smells to avoid at declaration time** (from `cpp-idioms.md > C++17-specific API design smells`):

| Smell | Fix |
|---|---|
| Boolean behaviour selector (`void Process(bool fast)`) | Two named functions or an `enum class` parameter |
| Homogeneous parameter list (3+ adjacent same-type params) | Named parameter struct |
| Primitive obsession on API boundary | Strong-type with `enum class` or named wrapper |
| `std::pair` return where a named struct carries semantic weight | Named struct or `std::optional<T>` |
| Non-const reference output parameter for output-only | Return by value or `std::optional<Result>` |

**Minimal / complete test (run before finalising the declaration):**

- **Minimal:** can any public method be removed without breaking a current or obvious caller? Remove it.
- **Complete:** can all legitimate use cases be expressed without reaching around the abstraction? If not, the missing operation belongs on the class.
- **Ordering contract:** if methods must be called in a specific sequence, encode the sequence in the type system (builder, factory, RAII guard) -- never in prose.

### Step 5 -- Implementation (core writing phase)

**Project types first** (MUST on public API, SHOULD in implementation):

**Org overlay check (mandatory -- do before writing any project type):**

Check for `../cpp/unity-references/`. If the directory exists, load in order:
1. Any `*-modernisation.md` -- project type preferences; entries marked `[OVERRIDE]` replace the `std::*` defaults in the tier tables.
2. Any `*-reinvention.md` -- project reinvention catalogue; check before writing any new utility.
3. Any `*-idioms.md` -- project idiom extensions.

If the directory is absent, use `std::*` types as specified in `cpp-modernisation.md > Tier tables`.

**Idioms (write modern, not legacy):**

Apply the tier tables in `cpp-modernisation.md`. Key items at MUST/SHOULD tier:

- Range-for over index loops for container iteration.
- Structured bindings for map iteration (`for (const auto& [key, val] : map)`) and multi-value returns.
- `std::optional<T>` for "may fail" returns instead of bool + out-parameter.
- `enum class` over unscoped `enum`.
- `using MyType = T;` over `typedef`.
- Lambdas over `std::bind`.
- `std::scoped_lock` over manual `lock()` / `unlock()`.
- `std::unique_ptr` over raw `new` / `delete` (or project equivalent when the project has a custom allocator macro).
- `nullptr` over `0` or `NULL`.
- `static_assert` over runtime `Assert` when the property is compile-time knowable.
- `override` on every virtual override.
- `= delete` for non-copyable types (not private-undefined).

### Step 6 -- Comments (write as you go, not as a post-pass)

Apply `../cpp/references/cpp-commenting.md` throughout authoring.

**Write doc comments at declaration time:**

- Every new class or struct gets at least a one-sentence brief. Use `///` when no tags or extra paragraphs are needed; `/** */` when ownership, thread-safety, or `@param`/`@return`/`@note` tags are needed.
- Every raw pointer member gets an ownership annotation: `// owning`, `// non-owning`, or `// optional-owning (nullptr when inactive)`.
- Every public method whose semantics are not fully captured by name + type gets a doc comment. At minimum: `@return` if the return type is not `void` and the meaning is not obvious.
- Every `noexcept` function that wraps a potentially-throwing callee gets a `@note` documenting the terminate-on-failure contract and why it is intentional.
- Every `// TODO` or workaround carries a `// [TICKET-NNN]` tracker reference.

**Never write:**

- Comments that restate what the code literally does.
- Phase / roadmap narrative ("Phase D will fix this" → use `// [TICKET-NNN]`).
- `@brief` prefix -- the first line of a doc block is the brief by autobrief convention.
- Stale doc comments copied from a related function without updating.

### Step 7 -- Pre-commit self-review

Before marking the task done, run the `cpp-review` L0-L3 checklist against your own work. Every MUST item caught here costs nothing; every MUST item found in review costs a review cycle.

**L0 (intent):** Does the commit message match the actual diff? Is every new file, class, and non-trivial public function called from at least one production caller within this commit (excluding the type's own test file)? If a provider or class ships with zero production callers, either wire it into production code or split it to the follow-up commit that does so.

**L1 (structural):** Is the abstraction justified by more than one concrete production consumer, or is this YAGNI? Is it in the right module and directory? Are new module dependencies acyclic? Would a plain namespace + free functions be equivalent?

**L2 (API contract):** Apply the minimal/complete test with the implementation now visible. Does the implementation reveal that a parameter or method is unnecessary? Does it reveal a missing operation that a caller must reach around the abstraction to perform?

**L3 (implementation):** Scan the new code against the modernisation-playbook tier tables. Every MUST item visible here is cheaper to fix now than to fix after a review finding.

After the self-review: fix all MUST items before reporting done. Defer SHOULD items with a `// [TICKET-NNN]` reference.

---

## Worked examples

### Example A -- Reinvention check prevents a duplicate utility

Task: "Add a helper that checks whether a string consists entirely of ASCII digits."

Step 1 reinvention check: grep `cpp-idioms.md > Reinvention catalogue` for "numeric", "digit", "integer". Find an existing `IsStringInteger` / `IsStringNumber` style utility in the project's utility layer. Verify the signature covers the need.

**Decision:** Do not write a new helper. Use the existing utility. If neither covers the edge case exactly, extend the canonical utility rather than adding a local copy -- extending the canonical utility means every consumer benefits.

---

### Example B -- Global state: choosing Singleton<T> over a file-static

Task: "Cache the resolved `ApplicationMode` so it is computed once per process."

Step 3 global state check: does a test need an alternative value? Yes -- fixtures exercise different modes. → Use `Singleton<T>`.

**What to write:**

```cpp
// ApplicationModeProvider.h
class ApplicationModeProvider : public Singleton<ApplicationModeProvider>
{
public:
    [[nodiscard]] ApplicationMode Get() noexcept;

private:
    std::atomic<bool> m_Cached{false};
    std::mutex        m_Mutex;
    ApplicationMode   m_Mode{};
};

// ApplicationModeProvider.cpp (define static storage for CRTP singleton)
template<> ApplicationModeProvider* Singleton<ApplicationModeProvider>::s_Instance = nullptr;

[[nodiscard]] ApplicationMode GetApplicationMode() noexcept
{
    return ApplicationModeProvider::GetInstance().Get();
}
```

**What NOT to write:**

```cpp
// Do not write this -- requires a #if TEST_BUILD bypass
// the moment the first test needs an alternative value.
static ApplicationMode s_Mode;
static std::once_flag  s_Flag;

ApplicationMode GetApplicationMode() {
    std::call_once(s_Flag, [] { s_Mode = Compute(); });
    return s_Mode;
}
```

The file-static form is testability-hostile by construction. The `Singleton<T>` form costs the same at runtime and requires no test-bypass code path.

---

### Example C -- API declaration smell avoided before writing

Task: "Add a function that processes an input token with an optional fast path."

Step 4 API smell check: draft `void ProcessToken(std::string_view token, bool fast)` triggers the boolean behaviour selector smell -- `true` and `false` paths do fundamentally different things; callers invert silently.

**Corrected declaration:**

```cpp
[[nodiscard]] Result ProcessToken(std::string_view token) noexcept;
[[nodiscard]] Result ProcessTokenFast(std::string_view token) noexcept;
```

or, if the two paths share most logic:

```cpp
enum class ProcessingSpeed { Normal, Fast };
[[nodiscard]] Result ProcessToken(std::string_view token, ProcessingSpeed speed) noexcept;
```

Either form makes the call site self-documenting and catches wrong-argument bugs at compile time.

---

### Example D -- Ownership annotation prevents a review SHOULD

Task: "Add a `Renderer` class that observes (but does not own) a `Device` from the `RenderSystem`."

Step 6 commenting: every raw pointer member requires an ownership annotation.

```cpp
class Renderer
{
public:
    explicit Renderer(Device* device) noexcept : m_Device(device) {}

private:
    Device* m_Device; // non-owning; lifetime managed by RenderSystem
};
```

Without the annotation `cpp-review` raises a SHOULD. The annotation costs one line and prevents the next reader from wondering whether the destructor should call `delete m_Device`.

---

### Example E -- L0 pre-commit self-review catches dead code before it ships

Task: "Add `FooProvider` class and register it with `FooSystem`."

After writing the class, Step 7 L0 self-review: grep for `FooProvider` in production code (excluding `FooProviderTests.cpp`). Result: zero production callers -- the `FooSystem::Register()` call is missing.

**Decision:** either add the registration call in this commit (making `FooProvider` live), or defer `FooProvider` entirely to the follow-up commit that adds the call. Do not ship `FooProvider` with zero production callers -- it is dead code on trunk and the commit message will disagree with reality.

---

## Honest limitations

The persona cannot reliably catch:

- **Architectural fit.** Whether the new API should exist, whether the abstraction scales to next quarter's requirements -- these need a human who knows the roadmap.
- **Subtle concurrency correctness.** Memory-ordering proofs, scheduler interaction, timing-window races. Apply `scoped_lock` and `atomic` correctly by following the playbook; the reviewer and CI own the subtle cases.
- **Distributed / multi-process semantics.** IPC ordering, partial-failure recovery.
- **Product / UX.** Whether the API name matches the user's mental model, whether the feature makes sense.

When the code being written touches any of the above, note it explicitly in the commit message or PR description so a targeted human reviewer can pick it up.
