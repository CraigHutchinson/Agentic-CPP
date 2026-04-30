# Modernisation Playbook

Companion to `anti-patterns.md`. Where the anti-pattern guard tells the reviewer **what NOT to raise**, this playbook tells the reviewer **what TO raise**: legacy idioms that should be modernised when seen in new or touched code.

Shared C++ reference. Loaded by `cpp-write` (step 5, implementation idioms), `cpp-review` (step 9, modernisation check), and `cpp-simplify` (step 1, reference load). Apply **after** the reinvention check (`idiom-checklist.md > Reinvention catalogue`) so project-specific utilities (`core::*`, `Word.h`, `Argv.cpp`) take precedence over generic standard-library modernisation.

The structure mirrors the `clang-tidy modernize-*` check family, which is the industry-canonical enumeration of legacy idioms with known remediations. If the team ever wires those checks into CI, findings here map 1:1 to a check name.

## Authority and prior art

- **C++ Core Guidelines** (Stroustrup, Sutter) -- normative source for the resource-management (R.*), interface (I.*), expression (ES.*), and type (Type.*) rules cited inline below.
- **LLVM Coding Standards** -- the closest analogue to this codebase's convention: "When both C++ standard library and LLVM support libraries provide similar functionality, it is generally preferable to use the LLVM library if there isn't a specific reason to favor the C++ implementation." This codebase follows the same pattern with `core::*` types over `std::*`.
- **Chromium Modern C++ feature list** -- useful negative space: even modern codebases ban `std::bind`, discourage `std::shared_ptr` for owned-by-default, and avoid `std::regex` / `std::random` engines for size and performance reasons. Aligns with this playbook's preference for project utilities and lambdas over `bind`.
- **`clang-tidy modernize-*` checks** -- canonical enumeration of legacy idioms with known automated remediations. Entries below cite the corresponding check name in parentheses.

## Tier guidance

- **MUST** -- the legacy idiom introduces a real defect class (UB, leak, lifetime hazard, double-free, removed-from-standard symbol).
- **SHOULD** -- the modern form removes a footgun, encodes an invariant in the type system, or replaces a hand-rolled pattern with a project utility.
- **NICE** -- modernisation that is purely a clarity / consistency win.

The "Migration cost is not a suppression reason" rule from `anti-patterns.md > Overriding principle` applies. Cost informs the tier, not the decision to flag.

## Project-specific overlay (read first)

For this codebase, these in-house types are preferred over their `std::` equivalents in engine code. Findings against `std::*` use in engine code are MUST on public API surfaces and SHOULD in implementation files:

| In-house | Replaces | Notes |
| --- | --- | --- |
| `core::string` / `core::wstring` | `std::string` / `std::wstring` | Memory label, embedded buffer for small strings |
| `core::string_ref` | `std::string_view` (when interfacing with engine) | Lifetime safety pattern: declare `&&` overload `= delete` if storing |
| `core::vector<T, kMemLabel>` | `std::vector<T>` | Allocator-aware; label is meaningful |
| `core::hash_map` / `core::hash_set` | `std::unordered_map` / `std::unordered_set` | |
| `core::flat_set` / `core::flat_map` | `std::set` / `std::map` for small / cache-friendly cases | |
| `core::array_ref<T>` | hand-rolled `data + size` view; iterator-pair parameter | The canonical span-like read-only view |
| `core::fixed_array<T, N>` | stack-allocated arrays | |
| `core::block_vector<T>` | long arrays where stable pointers matter | |
| `core::Format(...)` | `snprintf` + manual `core::string` build | Carries memory label |
| `StrICmp` / `BeginsWith` / `EndsWith` (`Word.h`) | hand-rolled string compares | |
| `HasArgument` / `GetArgumentValue` (`Argv.cpp`) | hand-rolled argv classification | |

Reference: `Documentation/InternalDocs/docs/Runtime/Core/containers/`.

## Memory and lifetime

| Legacy idiom | Modern form | Tier | Authority |
| --- | --- | --- | --- |
| `new T(...)` / `delete` pair owned by raw pointer (`modernize-make-unique`) | `std::unique_ptr<T>` + `std::make_unique<T>(...)`; project equivalent if the touched module has one | MUST when a leak / double-delete path exists; SHOULD otherwise | Core Guidelines R.20, R.23 |
| `T*` parameter that is conceptually owning (`modernize-pass-by-value` for sinks) | `std::unique_ptr<T>` parameter (sink) or `T&` (non-owning, non-null) | MUST | Core Guidelines I.11 |
| Manual `try { ... } catch { delete; throw; }` cleanup | RAII wrapper / `std::unique_ptr` / scope guard | MUST | Core Guidelines E.6 |
| `0` or `NULL` for pointer values (`modernize-use-nullptr`) | `nullptr` | SHOULD | Type-safe; participates correctly in overload resolution |
| Pointer arithmetic over an array | range-for / `core::array_ref<T>` | SHOULD | Eliminates off-by-one and bounds bugs |
| `std::auto_ptr` (`modernize-replace-auto-ptr`) | `std::unique_ptr` | MUST | `auto_ptr` is removed from the standard |
| Raw-pointer member with an unclear ownership story | `std::unique_ptr` (owning) or non-owning observer comment + `[[nodiscard]]` factory | SHOULD | Caller intent should be type-checked |

## Containers and views

| Legacy idiom | Modern form | Tier |
| --- | --- | --- |
| Hand-rolled `struct { T* data; size_t size; }` "view" | `core::array_ref<T>` | MUST -- this is reinvention of a documented project utility and forces every consumer into index loops |
| `const char*` + separate `size_t length` parameter | `core::string_ref` parameter by value (consider `&&` overload `= delete` if storing) | SHOULD |
| Iterator-pair function parameter (`begin, end`) for project containers | `core::array_ref<T>` / range parameter | SHOULD |
| Out-parameter `bool f(Result& out)` for "may fail" | `std::optional<Result> f()` or `[[nodiscard]]` enum disposition | SHOULD -- caller can't forget to check the disposition |
| Multiple out-parameters (`modernize-use-nodiscard`-adjacent) | Return a struct + structured bindings | SHOULD |
| C-style array as parameter (`modernize-avoid-c-arrays`) | `std::array<T, N>` (fixed) or `core::array_ref<T>` (variable) | SHOULD |
| `container.push_back(T(args...))` (`modernize-use-emplace`) | `container.emplace_back(args...)` | NICE -- raise as SHOULD when the temporary holds a non-trivial resource |
| `s.length() == 0` | `s.empty()` | NICE |

## Loops

| Legacy idiom | Modern form | Tier |
| --- | --- | --- |
| `for (size_t i = 0; i < v.size(); ++i)` over a container (`modernize-loop-convert`) | range-for `for (const auto& x : v)` | SHOULD |
| `for (Iter it = v.begin(); it != v.end(); ++it)` (`modernize-loop-convert`) | range-for | SHOULD |
| Index loop where the index is unused | range-for | MUST when the index loop is the only reason a hand-rolled `data + size` view exists -- both findings collapse into the `core::array_ref` migration |
| Manual `find` / `count` loops | `std::find_if` / `std::count_if` / `std::any_of` / `std::all_of` | NICE; SHOULD when the manual loop hides the predicate intent |
| Map iteration via `it->first` / `it->second` | Structured bindings: `for (const auto& [key, val] : map)` | SHOULD -- eliminates `first`/`second` ambiguity and documents intent at the declaration site. Already in use in the codebase (GfxBuffer, SchemaGenerator, ManagedAttributeManager). |
| `std::tie(a, b) = f()` for multi-value return unpacking | Structured bindings: `auto [a, b] = f()` | NICE |

## Type system

| Legacy idiom | Modern form | Tier |
| --- | --- | --- |
| Unscoped `enum E { A, B }` for a closed set of values | `enum class E : T { A, B }` | SHOULD -- removes implicit conversions to int and namespace pollution |
| `typedef T MyType;` (`modernize-use-using`) | `using MyType = T;` | NICE; SHOULD when the typedef hides a function pointer or template alias that `using` would make readable |
| C-style cast `(T)x` | `static_cast<T>(x)` / `reinterpret_cast<T>(x)` / `const_cast<T>(x)` | SHOULD; MUST when the C-cast silently strips const or reinterprets across unrelated types |
| Tag dispatch / SFINAE for compile-time branching | `if constexpr (...)` | SHOULD |
| Functor class with `operator()` defined inline at the call site | Lambda | SHOULD |
| `std::bind(f, _1, x)` (`modernize-avoid-bind`) | Lambda `[x](auto a) { return f(a, x); }` | SHOULD -- lambdas are inlinable, debuggable, and don't have `bind`'s argument-forwarding pitfalls. Chromium bans `std::bind` outright. |
| Hand-rolled tagged union: `enum Kind { A, B } kind; union { TypeA a; TypeB b; } data;` | `std::variant<TypeA, TypeB>` + `std::visit` | SHOULD -- eliminates manual lifetime management of the union, prevents accessing the wrong member, and enables exhaustive handling via `std::visit` with an overload set. Raise as MUST when the existing code has UB paths (wrong-member access, missing destructor call on non-trivial alternatives). |
| `std::visit` with a large chain of `std::get_if<T>` / `if`/`else` on a `std::variant` | `std::visit` with an overload-set lambda (C++17 `overloaded` idiom) | NICE; SHOULD when missing alternatives would be silently ignored |
| Virtual override without `override` keyword (`modernize-use-override`) | Add `override` | SHOULD -- catches signature drift at compile time |
| Class with virtual functions but no `final` where leaf | Add `final` on the class or method | NICE |
| `std::less<int>` template argument (`modernize-use-transparent-functors`) | `std::less<>` | NICE |

## Constructors and initialisation

| Legacy idiom | Modern form | Tier |
| --- | --- | --- |
| Default constructor that throws (`modernize-use-noexcept`) | Default constructor `noexcept` + factory or two-phase init | SHOULD |
| Move constructor not declared `noexcept` for a movable type | Add `noexcept` if it really doesn't throw | SHOULD -- enables `vector<T>` to use move on growth |
| Member initialisation in constructor body for fixed values (`modernize-use-default-member-init`) | Default member initialisers in the class body | NICE |
| `T x = T(...)` for explicit construction | `T x{...}` brace-init | NICE; SHOULD when the brace-init prevents narrowing conversions (Core Guidelines ES.23) |
| Hand-rolled trivial `Foo() {}` (`modernize-use-equals-default`) | `Foo() = default;` | NICE -- preserves triviality and POD-ness |
| Private undefined copy ctor / assignment for non-copyable types (`modernize-use-equals-delete`) | `Foo(const Foo&) = delete;` | SHOULD -- compile-time error rather than link-time |
| `f(void)` parameter list (`modernize-redundant-void-arg`) | `f()` | NICE |
| `throw()` exception specification (`modernize-use-noexcept`) | `noexcept` | SHOULD -- `throw()` is deprecated |

## Concurrency

| Legacy idiom | Modern form | Tier |
| --- | --- | --- |
| Manual `mutex.lock()` / `mutex.unlock()` | `std::lock_guard` / `std::scoped_lock` (deadlock-free for multi-mutex) | MUST -- exception safety; manual lock/unlock leaks the lock on throw |
| Volatile for thread synchronisation | `std::atomic<T>` | MUST -- `volatile` is not a synchronisation primitive |
| Hand-rolled DCL singleton with manual fences | `std::call_once` + `std::once_flag`, OR `static` local (Meyer's singleton, thread-safe init) | SHOULD |
| `std::random_shuffle` (`modernize-replace-random-shuffle`) | `std::shuffle(..., generator)` | MUST -- removed from the standard |
| `std::uncaught_exception()` (`modernize-use-uncaught-exceptions`) | `std::uncaught_exceptions()` (plural, returns count) | SHOULD -- single-form deprecated |

## Compile-time

| Legacy idiom | Modern form | Tier |
| --- | --- | --- |
| Runtime `Assert` for property knowable at compile time | `static_assert(...)` | SHOULD |
| `static_assert(cond, "")` with empty message (`modernize-unary-static-assert`) | `static_assert(cond);` | NICE |
| `#define` constants (`modernize-macro-to-enum` for closed sets) | `constexpr` variable / `inline constexpr` / `enum class` | SHOULD |
| Macro-based conditional compilation that could be `if constexpr` | `if constexpr` | SHOULD |
| `#include <stdio.h>` (`modernize-deprecated-headers`) | `#include <cstdio>` | NICE |

## Return-value contracts

| Legacy idiom | Modern form | Tier |
| --- | --- | --- |
| Function whose result must be checked but isn't `[[nodiscard]]` (`modernize-use-nodiscard`) | Add `[[nodiscard]]` | SHOULD -- see `idiom-checklist.md > [[nodiscard]] heuristics` for when |
| Function that conceptually never throws but isn't `noexcept` | Add `noexcept` | SHOULD -- enables move-semantics optimisations and signals intent. Document the "terminate-on-failure" contract for any wrapped non-`noexcept` callee. |
| Returning by `const T&` to a local | Return by value + rely on RVO / NRVO / move | MUST -- dangling reference is UB |
| `return Foo(args)` from a function returning `Foo` (`modernize-return-braced-init-list`) | `return {args};` when readability improves | NICE |

## Globals, singletons, and testability seam

Process-wide mutable state -- file-static caches, namespace-scope flags, ad-hoc DCL singletons, "first call wins" Meyer's singletons that latch a value -- creates an order-dependence between tests that the test harness cannot undo. Symptoms in review:

- Helpful comments such as "populated once at first call -- usually long before any test fixture installs its fakes".
- A `#if ENABLE_UNIT_TESTS_WITH_FAKES` (or equivalent) branch that bypasses the cache *only in test builds* to recover testability. The bypass is the admission that the design is testability-hostile.
- A free-function accessor (`GetThing()`) backed by `s_Thing` / `g_Thing` file-statics that hold both the value and its initialised flag.
- Tests that pass individually but fail when run together, or whose pass/fail depends on the order specified by the test runner.

| Legacy idiom | Modern form | Tier |
| --- | --- | --- |
| File-static cache + `std::once_flag` / atomic flag accessed only via a free function | Derive from the project's `Singleton<T>` template (CRTP, with `ScopedOverride` for tests); cache lives as instance state; tests bind a fresh instance via `Singleton<T>::ScopedOverride` | MUST when the file-static cache forces a `#if TEST_BUILD` bypass elsewhere; SHOULD when tests work today but could not exercise alternative configurations without binary divergence |
| Function-local `static` of a non-trivial type owning cached state (`static Cache c;` inside a free-function accessor) | Same as file-static: extract the cache into an instance owned by a `Singleton<T>`-derived class | MUST -- function-local statics are testability-hostile in the same way as file-statics: latched once per process, no reset hook, scoped-override impossible. The narrower scope is purely lexical and does not improve test isolation. (Narrow exceptions: write-only diagnostic counters that nothing depends on for behaviour, and Meyer's-singleton holders for genuinely immutable values that have no plausible test alternative.) |
| Namespace-scope mutable variables that any TU can read after init | Instance state on a `Singleton<T>`-derived class; reads go through `T::GetInstance()` | SHOULD |
| Hand-rolled DCL with `std::atomic<bool>` + `std::mutex` at namespace scope | Same caching logic as instance members of a class that inherits the project's `Singleton<T>`; the singleton template handles instance lookup | SHOULD -- the caching pattern stays; what changes is *who owns the state* (an instantiable class, not the TU) |
| `static T* g_Active = nullptr;` set by a `SetThing(T*)` function with no scope discipline | `Singleton<T>::ScopedOverride` RAII handle: ctor reseats the active pointer, dtor restores the previous, copy/move deleted, asserts on out-of-LIFO teardown | MUST -- the bare setter has no "restore previous on test teardown" guarantee, leading to cross-test pollution |
| New project introducing the pattern from scratch | Reuse the existing `Singleton<T>` template at the project's canonical utility location; do **not** introduce a parallel `Provider` template alongside it | MUST -- introducing a parallel template is reinvention; if `Singleton<T>` lacks a needed feature, extend it additively |

**Why the class-based form wins for tests:**

- Each fixture constructs a fresh derived instance on the stack; the destructor unwinds the override deterministically. No global "reset for testing" helper needed.
- The production code path (`T::GetInstance()`) and the test code path are identical -- the only difference is which instance is active. No `#if` divergence; no test-only API surface.
- Multiple alternative configurations (different policies, different inputs, different injected dependencies) coexist in the same binary. Parameterised tests pick the configuration via constructor argument.
- The "first call wins" hazard becomes "first call wins on this instance" -- bounded to the test's stack frame.

**Recommended pattern: extend the project's existing `Singleton<T>` template.**

This codebase already ships a CRTP `Singleton<T>` at `Modules/NativeKernel/Include/NativeKernel/Utilities/Singleton.h` that:

- Does **not** auto-register the constructed object as the active instance -- tests are free to instantiate as many objects on the stack as they need without disturbing the production singleton.
- Exposes `Create(memLabel)` / `Destroy()` / `SetInstance(...)` for production lifecycle.
- Provides a `Singleton<T>::ScopedOverride` RAII handle (LIFO-nested, copy/move deleted, asserts on out-of-order teardown) for installing a test alternative for the duration of a fixture.
- Uses a `DEFINE_SINGLETON_INSTANCE(MyType)` macro at .cpp scope to define the static storage.

**Production declaration:**

```cpp
class Provider : public Singleton<Provider>
{
public:
    [[nodiscard]] Context Get() noexcept;     // cached on first call (per instance)

private:
    std::atomic<bool> m_Cached{false};
    std::mutex        m_Mutex;
    Context           m_Cache{};
};

// In Provider.cpp:
DEFINE_SINGLETON_INSTANCE(Provider);

// Free-function accessor preserves the call-site contract.
[[nodiscard]] Context GetContext() noexcept { return Provider::GetInstance().Get(); }
```

**Test usage:**

```cpp
TEST(F, ContextHonoursLegacyFakeAtFixtureSetup)
{
    Provider testInstance;                              // fresh; no inherited cache
    Singleton<Provider>::ScopedOverride bind(&testInstance);
    InstallLegacyFake(...);                             // observed because cache is empty
    CHECK_EQUAL(expected, GetContext());                // reads through GetInstance() -> testInstance
}
```

If `Singleton<T>` is missing a feature your test pattern needs, **extend it additively**; do not introduce a parallel template. Parallel-template reinvention is itself a MUST finding under the reinvention check.

**Suppression:** when the cache truly is process-immutable for the lifetime of the binary (compile-time-derived constant, configuration loaded once before any test fixture runs, no `#if TEST_BUILD` bypass exists) the file-static is acceptable. The tell that you do **not** have this case: a test-only branch in the accessor.

## Worked examples

### Example A -- hand-rolled view -> `core::array_ref`

```cpp
struct StringListView
{
    const char* const* data;
    size_t size;
};

for (size_t i = 0; i < view.size; ++i)
    use(view.data[i]);
```

becomes

```cpp
using StringListView = core::array_ref<const char*>;

for (const char* token : view)
    use(token);
```

Wins: range-for, no off-by-one, `begin()`/`end()` for std-algorithm interop, project utility instead of reinvention. Tier: **MUST** because the reinvention check is the dominant rule.

### Example B -- manual lock/unlock -> `std::scoped_lock`

```cpp
m_Mutex.lock();
auto value = m_Map.at(key);
m_Mutex.unlock();
return value;
```

becomes

```cpp
std::scoped_lock guard(m_Mutex);
return m_Map.at(key);
```

Wins: exception safety (the original leaks the lock on `at` throwing), deadlock-free multi-mutex variant available, intent visible. Tier: **MUST**.

### Example C -- out-parameter -> `std::optional`

```cpp
bool TryParseToken(const char* s, ApplicationMode& out);
```

becomes

```cpp
[[nodiscard]] std::optional<ApplicationMode> TryParseToken(const char* s) noexcept;
```

Wins: caller cannot forget to check; result and presence travel together; no need to default-initialise `out` at the call site. Tier: **SHOULD**.

### Example D -- `std::bind` -> lambda

```cpp
auto handler = std::bind(&Foo::Handle, this, std::placeholders::_1, kFlag);
```

becomes

```cpp
auto handler = [this](Event e) { return Handle(e, kFlag); };
```

Wins: inlinable, debuggable, no placeholder forwarding pitfalls, captures are explicit. Tier: **SHOULD** (Chromium bans `std::bind` entirely; this codebase doesn't go that far but the lambda is preferred).

### Example E -- raw `new` -> `std::make_unique`

```cpp
Widget* w = new Widget(args);
// ... use w ...
delete w;
```

becomes

```cpp
auto w = std::make_unique<Widget>(args);
// ... use w; destruction is automatic on scope exit ...
```

Wins: leak-free under exceptions, ownership visible at the type level, no manual `delete`. Tier: **MUST** when the original has any code path that could leak (early return, throw, branch); SHOULD when the lifetime is locally obvious but the modernisation removes a class of bug.

### Example F -- file-static cache -> instantiable provider with stack-scoped override

```cpp
namespace
{
#if !ENABLE_UNIT_TESTS_WITH_FAKES
    std::atomic<bool>      s_Cached{false};
    std::mutex             s_Mutex;
    Context                s_Cache{};
#endif
}

Context GetContext() noexcept
{
#if ENABLE_UNIT_TESTS_WITH_FAKES
    // Tests fake the inputs per-fixture; the production cache (set on
    // first call, usually before fixture setup) would mask the fake.
    return Compute();
#else
    if (s_Cached.load(std::memory_order_acquire)) return s_Cache;
    std::lock_guard<std::mutex> lock(s_Mutex);
    if (s_Cached.load(std::memory_order_relaxed)) return s_Cache;
    s_Cache = Compute();
    s_Cached.store(true, std::memory_order_release);
    return s_Cache;
#endif
}
```

becomes (using the project's existing `Singleton<T>` template at `Modules/NativeKernel/Include/NativeKernel/Utilities/Singleton.h`)

```cpp
// In ContextProvider.h:
class ContextProvider : public Singleton<ContextProvider>
{
public:
    [[nodiscard]] Context Get() noexcept
    {
        if (m_Cached.load(std::memory_order_acquire)) return m_Cache;
        std::scoped_lock lock(m_Mutex);
        if (m_Cached.load(std::memory_order_relaxed)) return m_Cache;
        m_Cache = Compute();
        m_Cached.store(true, std::memory_order_release);
        return m_Cache;
    }

private:
    std::atomic<bool> m_Cached{false};
    std::mutex        m_Mutex;
    Context           m_Cache{};
};

// In ContextProvider.cpp:
DEFINE_SINGLETON_INSTANCE(ContextProvider);

Context GetContext() noexcept { return ContextProvider::GetInstance().Get(); }
```

Wins: identical production code path and test code path; no `#if TEST_BUILD` bypass; each test instantiates a fresh `ContextProvider` and binds it via `Singleton<ContextProvider>::ScopedOverride` for its scope; deterministic teardown; multiple alternative configurations can coexist in the same binary; reuses the project's canonical CRTP singleton (no parallel template). Tier: **MUST** when the original carries the `#if TEST_BUILD` bypass (the bypass *is* the evidence of a testability defect); **SHOULD** when no bypass exists today but the file-static would force one to be added the moment a test wants alternative inputs.

---

*Add new patterns below as the team encounters consistent modernisation opportunities. The playbook is paired with `anti-patterns.md`: this file enumerates the WIN cases, that one enumerates the SUPPRESS cases. The overriding principle (safety-improving modernisation is never cosmetic) lives in `anti-patterns.md`.*
