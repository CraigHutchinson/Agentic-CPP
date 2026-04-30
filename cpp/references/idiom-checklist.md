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
| Primitive obsession on API boundary | `int userId`, `bool isEditor`, `core::string assetPath` each crossing multiple public APIs as a raw type | SHOULD: strong-type with a thin `enum class` or a named wrapper. Each call site becomes self-documenting; wrong-type bugs move to compile time. |
| `std::pair` return where a named struct exists | `std::pair<bool, Foo>` or `std::pair<core::string, int>` as a return type | SHOULD: named struct or `std::optional<Foo>`. `pair.first` / `pair.second` at the call site carries no semantic information. |
| Output parameter instead of return value | `void GetResult(Result& out)` when the function always sets `out` | SHOULD: return `Result` by value (rely on NRVO/move) or `std::optional<Result>` if the function can fail. |
| Non-const reference parameter that is output-only | `void Populate(core::vector<Foo>& out)` that always clears and refills `out` | SHOULD: return `core::vector<Foo>` by value; a non-const ref implies in-out, which is misleading when only out. |

### Naming and call-site readability

- **Verb + noun** for mutating functions: `RegisterCallback`, `BuildIndex`, `ClearCache`.
- **Is / Has / Can** prefix for predicates that return `bool`: `IsEnabled()`, `HasPendingWork()`.
- **Get** prefix only for cheap, non-allocating observers that return an existing value. Use `Compute`, `Build`, or `Resolve` when the function does real work. Callers make performance assumptions from the name.
- **Try** prefix for functions that may fail and return `std::optional<T>` or a bool + out-param: `TryResolve`, `TryParse`. Makes the failure path visible at the call site.
- Avoid Hungarian notation for non-member names; use it for member variables (`m_Name`) and statics (`s_Cache`, `g_Instance`) where the Unity codebase already establishes it.

## Reinvention catalogue (Unity-specific)

Quick-reference of the helpers most commonly reinvented by new contributors. Grep here **before** approving any new local helper of the same shape.

### String operations -- `Modules/NativeKernel/Include/NativeKernel/Utilities/Word.h`

| If the new code does ... | Use this instead |
|---|---|
| Case-insensitive byte compare | `StrICmp(a, b)` |
| Prefix / suffix check | `BeginsWith(s, p)`, `EndsWith(s, p)` (+ `*CaseInsensitive` variants) |
| Numeric-string predicate | `IsStringNumber`, `IsStringInteger`, `IsStringUnsignedInteger` |
| Parse integer from string with overflow check | `StringToIntCheckedSInt8/16/32/64`, `...UInt8/...` |
| Integer to string | `IntToString`, `UnsignedIntToString`, `Int64ToString`, `UnsignedInt64ToSIByteUnitString` |
| Concatenate with separator | `ConcatWithSeparator(lhs, sep, rhs)` |
| Format-style string construction | `core::Format(...)` -- not `snprintf` + manual `core::string` build |

### Containers -- `Documentation/InternalDocs/docs/Runtime/Core/containers/`

| If the new code uses ... | Prefer |
|---|---|
| `std::string` (engine code) | `core::string` (memory label, embedded buffer) |
| `std::string_view` parameter | `core::string_ref` (with `&&` overload `= delete` if storing) |
| `std::vector<T>` (engine code) | `core::vector<T, kMemSomeLabel>` |
| `std::unordered_map` | `core::hash_map<K, V>` |
| `std::set` for small sets | `core::flat_set<T>` |
| Span-like read-only view | `core::array_ref<T>` |
| Stack-allocated small array | `core::fixed_array<T, N>` |
| Long array with stable pointers | `core::block_vector<T>` |

### Enum utilities -- `Modules/NativeKernel/Include/NativeKernel/Utilities/EnumFlags.h` and `EnumTraits.h`

| If the new code does ... | Use this instead |
|---|---|
| Bitwise OR / AND / test on a scoped enum used as flags | `EnumFlags.h` helpers -- avoid casting to the underlying int type manually |
| Enum-to-string / string-to-enum conversion or reflection | `EnumTraits.h` -- do not hand-roll a `switch` / name table |

### Path operations -- `Modules/NativeKernel/Include/NativeKernel/Utilities/PathNameUtility.h`

| If the new code does ... | Use this instead |
|---|---|
| Extract extension, directory, filename from a path string | `PathNameUtility.h` helpers |
| Normalise, join, or compare path strings | `PathNameUtility.h` helpers -- do not roll local `std::string` string operations on paths |

### Argv parsing -- `Runtime/Utilities/Argv.cpp`

| If the new code does ... | Use this instead |
|---|---|
| Check argv flag presence | `HasArgument` |
| Extract `-flag <value>` pair | `GetArgumentValue` (two-token form, no `=` split) |

### Singletons and active-instance patterns -- `Modules/NativeKernel/Include/NativeKernel/Utilities/Singleton.h`

| If the new code does ... | Use this instead |
|---|---|
| Hand-rolled CRTP singleton template | Inherit from the existing `Singleton<T>` template |
| File-static `g_Instance` + `Set/GetInstance()` free functions | `Singleton<T>` provides `Create(memLabel)` / `Destroy()` / `GetInstance()` / `GetInstancePtr()` / protected `SetInstance()` |
| Test wants to install an alternative instance for a fixture | `Singleton<T>::ScopedOverride bind(&testInstance);` -- RAII, LIFO-nested, asserts on out-of-LIFO teardown |
| Static instance definition macro | `DEFINE_SINGLETON_INSTANCE(MyType)` at .cpp scope (also defines the override pointer storage) |

The constructor of `Singleton<T>` does **not** auto-register the new object as the active instance, so tests are free to instantiate as many objects as they like on the stack and pick which one binds via `ScopedOverride`. This already addresses the "construct multiple test instances without disturbing the production singleton" use case without any constructor argument.

### Memory allocation -- `UNITY_NEW` / `UNITY_DELETE`

| If the new code does ... | Preferred form |
|---|---|
| `new T(args)` for a long-lived engine heap object | `UNITY_NEW(kMemSomeLabel, T)(args)` -- participates in memory profiling |
| `delete ptr` for a Unity-allocated object | `UNITY_DELETE(ptr)` |
| Short-lived object immediately placed under ownership | `std::make_unique<T>(args)` is acceptable for RAII-scoped objects; prefer `UNITY_NEW` when the object escapes the frame or will be stored long-term |

### Memory labels

| Common label | Use for |
|---|---|
| `kMemString` | Default for `core::string` |
| `kMemTempAlloc` | Short-lived stack-scope allocations |
| `kMemDefault` | Fallback when nothing more specific applies (review carefully) |

When reviewing a new container or string field, expect a deliberate label choice, not the default.

## Header / boundary discipline

### Project-level boundary rules

- Public runtime headers (`Runtime/Misc/`) must not include `core::vector` / `core::string` -- those drag editor-only dependencies. Put helpers that need them in editor-only headers (`Editor/Src/Application/`) and forward-declare the public API.
- Cross-platform: include paths are case-sensitive on Linux / macOS. Always match the on-disk filename casing exactly (`String.h`, not `string.h`).
- New entries in `PolicyViolationAllowList.gen.h` should be justified in the commit message. Zero new entries is the goal; if you must add one, document the rollout that retires it.

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
- `DEFINE_SINGLETON_INSTANCE(T)` and similar definition macros.
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
    [[nodiscard]] T* TryGet(core::string_ref key) noexcept;
    void Insert(core::string_ref key, T value);
private:
    core::hash_map<core::string, T> m_Map;
};
#include "FooCache.inl"   // definitions follow

// FooCache.inl — defines the template methods
template<typename T>
T* FooCache<T>::TryGet(core::string_ref key) noexcept
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

#include "core/string.h"   // 3. Project / engine headers (most stable last)
#include "NativeKernel/Utilities/Word.h"
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
    [[nodiscard]] core::string_ref GetName() const noexcept;

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
