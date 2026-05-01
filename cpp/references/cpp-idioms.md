# Idiom Checklist

Shared C++ reference. Loaded by `cpp-write` (steps 1-4, pre-flight and declaration checklist), `cpp-review` (steps 7-8, reinvention and code-location checks), and `cpp-simplify` (step 1, reference load). Idioms below are baseline for this codebase; the build standard is implicit and not restated per entry.

## `[[nodiscard]]` heuristics

Adapted from libc++'s [NodiscardPolicy](https://releases.llvm.org/19.1.0/projects/libcxx/docs/DesignDocs/NodiscardPolicy.html). Apply `[[nodiscard]]` when **any** of the following holds:

1. **Discarding the return value is a correctness issue.** E.g. `std::lock_guard` factory; `Try*` predicates whose result the caller must branch on.
2. **Discarding likely indicates the user meant something else.** Classic case: `vector::empty()` (boolean test) versus `vector::clear()` (mutator). If your function name could be confused with a sibling that has side effects, `[[nodiscard]]` disambiguates.
3. **The function returns a constant or only observes state.** E.g. `string::size()`, getters, named predicates that read process-lifetime classification.
4. **Discarding the value is most likely a misuse.** E.g. `find`, `count`, `Resolve*`, `Compute*`.

**Do not** apply `[[nodiscard]]` when:

- The function is primarily called for its side effect and the return is a convenience (e.g. `vector::insert` returning an iterator).
- Adding it would force every existing caller to add `(void)` casts for no diagnostic value.

## `noexcept` heuristics

From C++ Core Guidelines and prior reviews:

- **Default and move constructors** -- `noexcept` by default unless the type owns a resource that can throw on move.
- **Pure observer functions** with no allocation, no I/O, no possibility of exception -- `noexcept`. Examples: enum-to-string mappers, predicate accessors that read process-lifetime state.
- **Functions that wrap potentially-throwing legacy code** -- `noexcept` only if the failure mode is `std::terminate`-acceptable. Document the choice in a comment block at the function. Common pattern: a thin bridge predicate that wraps a legacy non-`noexcept` accessor can itself be `noexcept` if the underlying failure mode is unrecoverable (e.g. "what process am I?" cannot meaningfully throw past the caller).

## `static_assert` for type contracts

Use `static_assert` to encode invariants the compiler can check at build time:

- POD-ness: `static_assert(std::is_trivially_copyable_v<T>);` for types passed by value across module boundaries.
- Size contracts: `static_assert(sizeof(T) == N);` when ABI matters.
- Enum exhaustiveness: not directly supported pre-C++23, but pair with a `default:` `Assert(false)` in switches.

Prefer `static_assert` over runtime `Assert` whenever the property is knowable at compile time.

## Simplification and DRY

The simplest correct design is the right design -- not the most general, not the most flexible. Apply before designing any new type, API, or module.

### Simplification pre-flight

Run before writing. If any signal fires, ask whether the stated goal can be achieved with fewer moving parts before proceeding.

| Signal | What it suggests |
|---|---|
| New abstraction has exactly one concrete implementation | Pre-emptive indirection; collapse to a concrete type until a second implementation appears |
| New helper exists solely to satisfy a single call site | The logic may belong at the call site; extract only when a second caller appears |
| Configurable, general-purpose system solves a specific bounded problem | Generality is speculative; prefer the specific form and generalise when the second use-case arrives |
| New type count exceeds the distinct responsibilities in the problem statement | Wrong decomposition seam; the implementer may have solved a more general problem than asked |
| Implementation is longer than the problem statement | Complexity may be incidental (over-engineering) rather than essential (domain complexity) |
| A new `Manager`, `Handler`, or `Helper` class with no clear invariant | Name signals a grab-bag; split by responsibility or collapse to free functions |
| New type expresses a generic shape that an existing language / standard / project facility already covers | Reinvention of a generic concept (range / view / span / pair / optional / variant). Use the standard form; introducing a domain-named wrapper hides what the type *is* and forces every reader to learn a new vocabulary for an old idea. See [Generic-shape reinvention](#generic-shape-reinvention) below. |

### Generic-shape reinvention

When introducing a new type, ask: *"Is the structural shape of this type a generic concept that already has a standard form?"* If yes, prefer the standard form unless there is a concrete justification for the wrapper.

Common shapes and their standard forms:

| Shape | Standard form |
|---|---|
| Pointer + count, read-only iteration | project span type / `std::span<T>` (C++20) — has `begin / end / size / data / operator[]` for free |
| Compile-time-sized fixed array | project fixed-array type / `std::array<T, N>` |
| "Either a value or nothing" | `std::optional<T>` |
| Two related values returned together | a named struct (`pair` carries no semantic information at the call site) |
| Type-erased "one of N alternative types" | `std::variant<...>` |
| Borrowed iteration over an existing contiguous container | project span type constructed from the container; do not wrap |

The smell, concretely: a class named `FooThingList` / `FooValueRange` / `FooViewOfBars` whose entire body is a constructor taking `(T*, size_t)` plus `begin / end / size`. That is a project span type with extra steps. The wrapper is justified only when it carries semantics the generic form cannot — e.g. an invariant on the contents (`SortedAssetIds` is non-empty and sorted), a non-trivial constructor that validates, or a method whose meaning depends on knowing the elements are `T` specifically.

Raise as **SHOULD**: replace with the standard form. Cite the standard type and what semantics, if any, the wrapper carries that the standard type does not — the author then either justifies the wrapper or removes it.

**Do not raise** when the wrapper carries a real invariant the generic form cannot encode (the `SortedAssetIds` example above), when the type is part of a deliberately stable public ABI that pre-dates the standard form, or when the wrapper exists to forbid a dangerous overload (e.g. deleting `(T&&)` to forbid temporaries — the generic form would not).

### DRY check

Identify repeated structure before, during, and after writing:

- **Two blocks with the same control flow, different literal values** → candidate for a loop, template, or named helper.
- **Parallel class hierarchies growing in lockstep** → candidate for a single parameterised type or a shared base.
- **The same condition checked in multiple call sites** → candidate for a named predicate or a type-system encoding.
- **Copy-pasted code with one field changed** → almost always a loop or a template parameter.

**DRY is not reinvention.** Reinvention is duplicating an *existing project utility*; DRY is duplicating logic *within the current change*. Both are findings; the remediation differs: reinvention → use the existing utility; DRY → extract or parameterise within the new code.

**Do not over-apply.** Three similar lines are better than a premature abstraction. Raise only when the extracted form is genuinely simpler to read and maintain than the instances — not merely shorter.

## API design

### Foundational rules

- **Total functions over partial functions** when the input space is small and the failure mode is well-defined. Prefer a total mapping that defines behaviour for every input combination over a partial function that asserts on "impossible" combinations -- the assert is technical debt the moment a new code path constructs the impossible input.
- **Named predicates over enum comparison at call sites.** `IsBackgroundWorker()` reads better than `GetProcessMode() == ProcessMode::BackgroundWorker` and survives mode-set evolution; flips happen in one place.
- **Facets over flags.** When a process has multiple orthogonal classifications (mode, topology, linkage), aggregate facets in a struct rather than maintaining N parallel booleans.

### Minimal and complete checklist

Apply to every new or changed class and public function group. The minimal/complete test is the L2 layer of the **Layered design review** (see `SKILL.md`).

**Minimal** -- nothing unnecessary in the public surface:

| Smell | Signal | Tier |
|---|---|---|
| Single-implementation interface | One class inheriting `IFoo` with no second concrete implementation in the codebase | SHOULD: collapse to a concrete class; remove the `I` prefix abstraction |
| Middle-man class | Every public method immediately delegates to a single member with no added logic | SHOULD: remove the indirection; callers can use the inner type directly |
| Unused / untested public member | A public method with zero call sites inside the diff and no test exercising it | SHOULD: delete or make private; YAGNI |
| Superfluous overload set | Two overloads whose bodies are identical after the implicit conversion | SHOULD: delete the narrower overload |

**Complete** -- nothing required but missing from the public surface:

| Smell | Signal | Tier |
|---|---|---|
| Leaky abstraction | Caller must `static_cast` to the concrete type, read a public field, or call a sibling type's method to perform a legitimate operation | MUST: the missing operation belongs on the abstraction |
| Ordering requirement, unencoded | A comment like "must call Init() before Use()" with no type enforcing the sequence | MUST: use a builder, factory, or RAII guard whose constructor performs the required first step |
| Required context passed by convention | Callers always pass the same `context` or `allocator` argument that the type could own | SHOULD: make it a constructor parameter or a member |

### C++17-specific API design smells

These patterns are observable at the declaration level and should be caught at L2 before descending to implementation.

| Smell | Signal | Tier |
|---|---|---|
| Boolean behaviour selector | `void Process(bool fast)` where `true` and `false` paths do fundamentally different things | SHOULD: two named functions (`ProcessFast()` / `ProcessNormal()`) or a `enum class Speed` overload. Boolean params invert silently. |
| Homogeneous parameter list | Three or more adjacent parameters of the same type: `f(int x, int y, int z)` | SHOULD: named parameter struct. Argument-swap bugs are invisible to the compiler and the call site. |
| Primitive obsession on API boundary | `int userId`, `bool isEditor`, `std::string assetPath` each crossing multiple public APIs as a raw type | SHOULD: strong-type with a thin `enum class` or a named wrapper. Each call site becomes self-documenting; wrong-type bugs move to compile time. |
| `std::pair` return where a named struct exists | `std::pair<bool, Foo>` or `std::pair<std::string, int>` as a return type | SHOULD: named struct or `std::optional<Foo>`. `pair.first` / `pair.second` at the call site carries no semantic information. |
| Output parameter instead of return value | `void GetResult(Result& out)` when the function always sets `out` | SHOULD: return `Result` by value (rely on NRVO/move) or `std::optional<Result>` if the function can fail. |
| Non-const reference parameter that is output-only | `void Populate(std::vector<Foo>& out)` that always clears and refills `out` | SHOULD: return `std::vector<Foo>` by value; a non-const ref implies in-out, which is misleading when only out. |

### Naming and call-site readability

- **Verb + noun** for mutating functions: `RegisterCallback`, `BuildIndex`, `ClearCache`.
- **Is / Has / Can** prefix for predicates that return `bool`: `IsEnabled()`, `HasPendingWork()`.
- **Get** prefix only for cheap, non-allocating observers that return an existing value. Use `Compute`, `Build`, or `Resolve` when the function does real work. Callers make performance assumptions from the name.
- **Try** prefix for functions that may fail and return `std::optional<T>` or a bool + out-param: `TryResolve`, `TryParse`. Makes the failure path visible at the call site.
- Avoid Hungarian notation for non-member names; use it for member variables (`m_Name`) and statics (`s_Cache`, `g_Instance`) where the project codebase establishes it.

### Encapsulation: free functions that should be static members

A free function whose name carries the class as a prefix (`<Class><Method>(...)`, `<Class>_<Method>(...)`) or whose only meaningful argument is a nested type of one class (`<Class>::<NestedEnum>`, `<Class>::<NestedStruct>`) is a static member in disguise. Move it inside the class.

| Smell (free function shape) | Better as | Why |
|---|---|---|
| `FooBarToString(Foo::Bar)` | `Foo::BarToString(Foo::Bar)` (or `Foo::ToString(Foo::Bar)`) | Class scope removes the redundant `Foo` prefix; reads cleaner; discoverable via `Foo::` completion. |
| `FooModeValidValues()` returning a list of `Foo::Mode` tokens | `Foo::ModeNames()` static member | The list belongs to `Foo`; the free function pretends it doesn't. |
| `MakeFooFromArgv(int, char**)` with no other dependencies | `Foo::FromArgv(int, char**)` static factory | Factory is a class concern; the free function hides the relationship. |
| `IsFooReady(const Foo&)` taking `Foo` by const-ref and reading only its public state | `bool Foo::IsReady() const` | The free-function form forces a `(ctx)` argument that the member form makes implicit; the member is what call sites want to write. |

**Why it matters:**

- **Discoverability.** `Foo::` IDE completion surfaces every operation on `Foo` in one list. Free functions named `Foo*` only appear if the caller already knows the prefix to type.
- **Naming.** Class scope eats the redundant prefix. `ProcessContext::ModeNames()` reads as a property of the class; `ProcessContextModeValidValues()` reads as if the class name and the operation are accidentally adjacent strings.
- **Access.** A static member can read the class's private statics or call its private helpers; a free function cannot, which forces a wider public surface than the operation actually needs.
- **Coupling is declared.** A static member states "this operation is part of `Foo`". A free function in the same TU states nothing — the relationship is implicit and easy to break (the free function and the class can drift into separate files, separate modules, separate translation phases).

**When to keep the free function (legitimate exceptions):**

- The function lives in a *different module* and uses the class but is not part of its API. A logging helper `LogFooState(const Foo&)` in the logging module is correctly a free function — it belongs to logging, not to `Foo`.
- The function operates *across* multiple classes' nested types, so no single class is the natural owner: `bool ModesAreCompatible(Foo::Mode, Bar::Mode)`.
- The function exists as a deliberate **singleton-deferring wrapper** over a member: `bool IsFooReady() { return Foo::GetInstance().IsReady(); }`. The instance form is the member; the no-arg form is the free wrapper. (See the dual-form predicate pattern in `cpp-modernisation.md > Globals, singletons, and testability seam`.)
- The function is a non-virtual extension that genuinely cannot be a member (e.g. an `operator<<` for streaming, an `swap` overload found by ADL).

**Finding shape (for use in review reports):**

| Severity | Trigger |
|---|---|
| **SHOULD** | Free function in the same TU/header as `Foo`, named `Foo<Suffix>(...)` or taking `Foo::<NestedType>` as its primary argument, with no instance state of its own and no legitimate-exception justification. Move to `static` member of `Foo`; drop the redundant `Foo` prefix from the name. |
| **NICE** | Free function operating on a `Foo` argument by const-ref that only reads public observers — could be a const member but is not currently. Acceptable to leave if other callers benefit from the free shape (composability, ADL). Flag for awareness, not for blocking. |

## Reinvention catalogue

Quick-reference of the shapes most commonly reinvented. Grep here **before** approving any new local helper of the same shape.

If an org overlay is present (`../org/references/`), load it now -- org-specific utilities (project string libraries, container types, argv helpers, singletons, memory allocators) are catalogued there with exact file paths and function names.

For projects without an org overlay, check these generic shapes before writing a new helper:

| Shape | Check for |
|---|---|
| Case-insensitive string compare | Project string utilities directory |
| Argv flag / value extraction | Project argv or CLI utilities |
| Path manipulation (extension, join, normalise) | Project path utilities |
| Enum flags / enum-to-string reflection | Project enum utilities |
| Span-like read-only view over contiguous data | `std::span<T>` (C++20) or project equivalent |
| Process-lifetime singleton | Project singleton template |
| Format-style string construction | Project formatting utility; avoid `snprintf` + manual string concatenation |

## Header / boundary discipline

### Project-level boundary rules

- Cross-platform: include paths are case-sensitive on Linux / macOS. Always match the on-disk filename casing exactly (`String.h`, not `string.h`).
- If an org overlay is present, load it for project-specific boundary rules (allowed header contents, module-crossing restrictions, policy allowlist conventions).

---

## File organisation

Authority: C++ Core Guidelines SF.*, LLVM Coding Standards, Google C++ Style Guide. Apply to every new file and every file the diff touches.

### File extensions and naming

Use `.h` for all C++ headers and `.cpp` for all translation units. Do not introduce `.hpp`, `.hxx`, `.cc`, or `.cxx` — they are inconsistent with the codebase convention and break tooling assumptions (editors, grep, build rules).

Use `.inl` exclusively for template or `inline` implementation files that are `#include`d at the **bottom** of their owning `.h`. They are not standalone compilation units.

**Filename must match the primary class/struct name exactly**, including casing. `class FooManager` belongs in `FooManager.h` / `FooManager.cpp`. Mismatches are a build-time hazard on Linux/macOS (case-sensitive filesystems) and break every grep-by-class-name workflow.

### One primary type per file pair

Each public class or struct gets its own `.h` / `.cpp` pair. Small, tightly coupled helpers — a struct used only as a return value of that class's API, a tag type, a trivial RAII guard — may live in the same file. Unrelated types sharing a header are SHOULD-split: when a reader searches for `Bar`, they should not land in `Foo.h`.

### `#pragma once`

All new headers use `#pragma once`. It is simpler, faster to compile (the compiler never reopens the file), and immune to guard-name collisions. Do not mix with traditional `#ifndef` guards in new code. (C++ Core Guidelines SF.8.)

### What belongs in a header

| Belongs in `.h` | Reason |
|---|---|
| Class / struct / enum declarations | Required by all TUs that use the type |
| `inline` function definitions ≤ ~5 lines | Compiler sees them at every call site |
| Template definitions (all of them) | Must be visible at instantiation point |
| `constexpr` functions and variables | Must be visible for constant-folding |
| Type aliases, `using`, `enum class` | Shared vocabulary |
| Forward declarations for types used only as pointer / reference | Avoids dragging full headers |

| Must NOT be in a header | Consequence |
|---|---|
| `using namespace X;` at namespace or file scope | Silently pollutes every including TU; caller cannot undo it |
| Anonymous namespace definitions | Each TU gets its own copy — not "private" to the header; causes ODR surprises |
| Non-trivial function definitions (>~5 lines) | Multiplies build time: compiled once per including TU instead of once |
| File-scope mutable `static` variables | Same as anonymous namespace: per-TU copies, not a global singleton |
| Unnecessary `#include` for types used only as pointer / reference | Drags transitive headers into every including TU; use a forward declaration instead |

### What belongs in a `.cpp`

- All non-trivial function definitions.
- `static` member variable definitions.
- Heavy `#include` dependencies — push them here and keep the header lean.
- Anonymous namespace helpers that are genuinely file-local.
- Singleton static storage definitions (explicit template specialization, e.g. `template<> T* Singleton<T>::s_Instance = nullptr;`, or project equivalent).
- Explicit template instantiations for known types: `template class Foo<int>;`

### Template implementations — the `.inl` pattern

When template method bodies are large (more than ~20 lines total), extract them into a `.inl` file to keep the header readable:

```cpp
// FooCache.h — declares the template
#pragma once
template<typename T>
class FooCache
{
public:
    [[nodiscard]] T* TryGet(std::string_view key) noexcept;
    void Insert(std::string_view key, T value);
private:
    std::unordered_map<std::string, T> m_Map;
};
#include "FooCache.inl"   // definitions follow

// FooCache.inl — defines the template methods
template<typename T>
T* FooCache<T>::TryGet(std::string_view key) noexcept
{
    auto it = m_Map.find(key);
    return it != m_Map.end() ? &it->second : nullptr;
}
```

For templates instantiated over a known, fixed set of types, prefer **explicit instantiation** in a `.cpp` to keep the `.h` declaration-only:

```cpp
// FooCache.cpp
#include "FooCache.h"
template class FooCache<Widget>;
template class FooCache<Texture>;
```

Explicit instantiation moves compilation cost to one TU and gives the linker a single definition to deduplicate.

### Include order in `.cpp` files

```cpp
#include "Foo.h"          // 1. Corresponding header FIRST -- catches missing-include bugs
                           //    in the header immediately
#include <algorithm>       // 2. Standard library headers
#include <optional>

#include "Core/String.h"   // 3. Project / engine headers (most stable last)
#include "Core/Utilities/Word.h"
```

Putting the corresponding header first is a hard rule (LLVM, Google): if `Foo.h` fails to include its own dependencies, `Foo.cpp` will fail to compile immediately — rather than accidentally compiling because some other header pulled them in first, hiding the bug from other TUs.

### Class member ordering

Public before private. Callers read public; implementation detail is noise.

```cpp
class Foo
{
public:
    // 1. Type aliases and nested types
    using Handle = int;

    // 2. Static constants
    static constexpr int kMaxItems = 64;

    // 3. Constructors / destructor / assignment
    Foo();
    ~Foo();
    Foo(const Foo&) = delete;
    Foo& operator=(const Foo&) = delete;

    // 4. Public methods (most important / most called first)
    [[nodiscard]] Result DoThing() noexcept;
    [[nodiscard]] std::string_view GetName() const noexcept;

private:
    // 5. Private types (implementation details)
    struct State { ... };

    // 6. Private methods
    void InternalHelper();

    // 7. Data members (always private)
    State  m_State;
    int    m_Count{0};
};
```

### Finding table

| Smell | Signal | Tier |
|---|---|---|
| `using namespace X;` at namespace scope in a header | Silently pollutes every including TU; caller cannot undo it | **MUST** |
| Anonymous namespace in a header | Not file-local — each TU gets its own copy; ODR hazard | **MUST** |
| Filename casing does not match primary class name | `class FooManager` in `fooManager.h` — linker / build fails on Linux/macOS | **MUST** |
| Template defined only in `.cpp` with no explicit instantiation | Other TUs get a linker error for the missing symbol | **MUST** |
| `.hpp` / `.hxx` / `.cc` / `.cxx` extension in a `.h` / `.cpp` codebase | Inconsistency breaks tooling, grepping, and build rules | **SHOULD** |
| Non-trivial function body (>5 lines) defined inline in the class declaration | Compiled once per including TU; bloats incremental build time | **SHOULD** |
| Full `#include` in a header where a forward declaration would suffice | Drags transitive headers into every including TU | **SHOULD** |
| Multiple unrelated public types in one header | Grep by class name surfaces unrelated code | **SHOULD** |
| Large template implementation (>~20 lines) directly in `.h` with no `.inl` | Header becomes hard to read; use the `.inl` include pattern | **SHOULD** |
| `#ifndef` include guard in a new file (codebase uses `#pragma once`) | Inconsistency; verbose; guard names can collide | **NICE** |
| Corresponding `.cpp` does not include its own `.h` first | Hides missing-include bugs in the header from other TUs | **NICE** |
| `private:` section declared before `public:` | Forces callers to scroll past implementation detail to find the API | **NICE** |

*Extend any section above when a new idiom, reinvention-catalogue entry, or file-organisation rule is validated across multiple PRs. After extending this file, commit and push -- see [Contributing](../../README.md#contributing).*
