# Sub0 style profile

Style profile for the Sub0 library family (Sub0Pipeline, Sub0ECS, Sub0Pub and siblings). Selected per `../references/cpp-profile-selection.md`; schema defined there. Owner decisions recorded 2026-10; the `STYLE_GUIDE.md` files in the libraries are summaries of this profile and lose to it where they disagree.

**The generic core has not been neutralised yet.** Its examples still show `.h`, PascalCase methods, `m_` members and `<Basename>Tests.cpp`. For a Sub0 project this profile wins wherever the two disagree. Do not raise the generic finding; raise the profile rule.

## Selection markers

- A `project(Sub0...` line in the root `CMakeLists.txt`, or
- an `include/sub0*` directory.

Explicit form (preferred): a line `style-profile: sub0` in the project's `AGENTS.md`, `CLAUDE.md` or `STYLE_GUIDE.md`.

## Superseded generic guidance

For Sub0 projects, ignore these generic statements and examples:

| Generic text (file > section) | Sub0 replacement | Rule |
|---|---|---|
| `cpp-idioms.md` > File extensions and naming: "Use `.h` ... Do not introduce `.hpp`"; finding-table row `.hpp` = SHOULD | `.hpp` / `.cpp` only | S06 |
| `cpp-idioms.md` > File extensions and naming: filename matches class name "including casing" (`FooManager.h`) | snake_case (`foo_manager.hpp`) | S06 |
| `cpp-idioms.md` > Naming; `cpp-write` Step 4 and Examples B-D: `RegisterCallback`, `BuildIndex`, `IsEnabled()` | camelCase (`registerCallback`, `buildIndex`, `isEnabled()`) | S01 |
| `cpp-idioms.md` > Naming ("`m_Name`, `s_Cache`, `g_Instance`") and the class-ordering example (`m_State`) | `camelCase_` data members | S12 |
| `cpp-idioms.md` > finding table: `#ifndef` guard = NICE | `#pragma once` required, SHOULD | S05 |
| `cpp-idioms.md` > Include order example (`"Foo.h"`, `"Core/String.h"`) | own headers library-rooted (`"sub0pipeline/job.hpp"`); the order itself is open (O7) | S04 |
| `cpp-commenting.md` > Function / method doc template and severity rows: `@param[in\|out\|in,out]` is MUST | plain `@param` is the rule; directional tags are allowed, never required | S02 |
| `cpp-commenting.md` > `@file` template using `@brief` | no `@brief` anywhere | S03 |
| `cpp-review` step 8 / `cpp-idioms.md`: test file is `<Basename>Tests.cpp` | `test_<topic>.cpp` | S09 |
| `cpp-review` step 8: PascalCase example paths (`Feature/Foo.cpp`) | snake_case paths | S06 |
| README / `cpp-modernisation.md`: C++17 baseline | Sub0 uses C++20 or C++23 per library; open (O5) | O5 |

## Report configuration

Fill the placeholders from the project, then run the commands in each rule's `detect` field verbatim. Shell: bash with `rg` (ripgrep) and `grep -E`. `set -f` stops the shell expanding the glob arguments.

```bash
set -f
LIB=sub0pipeline; LIBU=SUB0PIPELINE; CMAKE_LIB=Sub0Pipeline
SCOPE="include src platform tests examples"
G='-g *.hpp -g *.cpp -g !**/vendor/** -g !**/build*/**'
PUBLIC="include platform"        # trees whose headers are the public interface
EXEMPT='^(push_back|emplace_back|pop_back|request_stop|stop_requested|stop_possible|get_token|get_stop_token|get_allocator|hardware_concurrency|notify_one|notify_all|try_lock|try_lock_for|try_lock_until|fetch_add|fetch_sub|compare_exchange_weak|compare_exchange_strong|lower_bound|upper_bound|equal_range|tag_invoke)$'
```

`EXEMPT` is the list of names that mirror a standard-library protocol. A match means "exempt, verify": check the declaration really implements or mirrors that protocol (for example `RunScope::request_stop` mirrors `std::stop_source`). It is never counted as a violation. Extend the list per project; do not silently drop names from it.

Triage classes for any name list: **rename** (project-owned public name), **exempt, verify** (matches `EXEMPT` or is required by a standard protocol), **non-name** (the match is a call into the standard library, CMake or a macro, not a declaration the project owns).

## Rules

### S01 method-case
- **value:** public functions and methods are `camelCase`. Exempt: names that mirror or are required by a standard-library protocol (`begin`/`end`/`size`/`swap`, `request_stop`/`stop_requested`, `operator` names, customisation points such as `tag_invoke`).
- **status:** decided
- **why:** one case across the family; protocol names stay as the standard spells them so generic code and range-for keep working.
- **correct:** `bool waitAll() noexcept;`   `iterator begin() const noexcept;`
- **incorrect:** `bool wait_all() noexcept;`
- **detect:** declarations with a snake_case name (headers are the public interface; sources, tests and examples are internal):
  ```bash
  D='^\s*(?!return\b|//|\*|/\*|#|using\b|typedef\b|else\b|co_return\b|throw\b)(?:\[\[\w+\]\]\s*)*(?:(?:static|virtual|inline|constexpr|consteval|explicit|friend|extern)\s+)*(?:[A-Za-z_][\w:]*(?:<[^;()]*>)?[\s*&]+)+([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\s*\('
  rg -N -I -o -P "$D" -r '$1' -g '*.hpp' $PUBLIC | tr -d '\r' | sort | uniq -c | sort -rn   # public names
  rg -N -I -o -P "$D" -r '$1' $G $SCOPE | tr -d '\r' | sort | uniq -c | sort -rn          # all names
  ```
  Split the name list with `grep -E "$EXEMPT"` (exempt, verify) and the rest. False positives: a call such as `pool.push_back(x);` or `auto r = make_thing(x);` that happens to look like a declaration (read the line); local variables declared with constructor syntax.
- **severity:** STYLE/SHOULD for a public name (it breaks the API, so report it under "API-breaking" in an audit); STYLE/NICE for an internal name.
- **overrides:** `[OVERRIDE]` `cpp-idioms.md > Naming and call-site readability` (PascalCase examples). The verb/predicate shape rules there still apply.

### S02 doxygen-interfaces
- **value:** every interface (what a library user or a Doxygen consumer sees) carries a Doxygen comment: `@param` for every parameter, `@return` for every non-void result, `@tparam` for every template parameter a caller supplies, and `@note` and similar as applicable, plus ownership, lifetime and thread-safety where they matter. Exempt from the tag requirement: `override` declarations (they inherit the base documentation), defaulted or deleted special members, and operators with their conventional meaning. Prose `//` comments are for internal code only. Directional `@param[in]` / `[out]` is **not** required; plain `@param` is the rule.
- **status:** decided
- **why:** the header is the contract; a Doxygen consumer must see it, and the tags are what make it checkable.
- **correct:** `/** Looks up a job by name. @param name Case-sensitive job name. @return The job, or an invalid handle. @note Thread-safe. */`
- **incorrect:** `// looks up a job` above a public declaration; a public function with no comment; a `/** */` block with prose only on a multi-parameter function.
- **detect:** judgement, sampled (see the audit mode). Candidate generators, both for headers only:
  ```bash
  # blocks whose first paragraph holds no sentence (starts with a tag, or never reaches a full stop)
  rg -n -U -P '/\*\*[ \t]*@(?!brief\b)[a-z]|/\*\*(?![ \t\r\n*]*@brief)(?:(?!\*/)[^.])*?(?:\*/|\n[ \t]*\*?[ \t]*@(?!p\b)[a-z])' -g '*.hpp' $PUBLIC
  # plain // comment directly above a declaration
  rg -n -U -P '^[ \t]*//(?!/)[^\n]*\n[ \t]*(?:\[\[nodiscard\]\][ \t]*)?(?:template\b[^\n]*\n[ \t]*)?(?:(?:static|virtual|inline|constexpr|explicit)[ \t]+)*(?:class|struct|enum|[\w:<>,*&]+[ \t*&]+\w+[ \t]*\()' -g '*.hpp' $PUBLIC
  ```
  False positives: the second generator also fires in `private:` sections, where prose is allowed; `override` declarations inherit the base documentation. Missing ownership, lifetime and thread-safety notes cannot be grepped; read the public class docblocks in the sample.
- **severity:** STYLE/SHOULD (a missing docblock on a public declaration is also a generic MUST in `cpp-commenting.md`; report it once, under the generic MUST, not twice).
- **overrides:** `[OVERRIDE]` `cpp-commenting.md > Function / method doc template`, "Required tags" and the severity-table rows demanding `@param[in|out|in,out]`. Everything else in that file still applies.

### S03 autobrief
- **value:** no `@brief` tag. The first sentence of a doc comment is the brief and must be a complete sentence ending in a full stop; it may wrap onto a second line.
- **status:** decided
- **why:** one form; the generic reference already prefers autobrief, and a brief that is not a sentence truncates in generated documentation.
- **correct:** `/** Returns the number of registered jobs. */`
- **incorrect:** `/** @brief Number of jobs */`   `/** @return Total number of jobs. */` (no brief sentence)
- **detect:**
  ```bash
  rg -n '@brief' $G $SCOPE                 # tag present: mechanical fix
  # first paragraph of a doc block has no sentence: use the S02 first generator
  ```
  False positives for the second: none known beyond blocks that hold only `@copydoc`.
- **severity:** STYLE/SHOULD
- **overrides:** `[OVERRIDE]` the `@brief` in the `cpp-commenting.md > File-level @file block placement` template.

### S04 include-style
- **value:** `""` for the library's own headers, `<>` for system and third-party headers. Own-header paths are library-rooted (`"sub0pipeline/job.hpp"`), never bare relative (`"job.hpp"`, `"../job.hpp"`).
- **status:** decided (quoting and rooting only; ordering is open, see O7)
- **why:** a bare relative include lets the compiler pick the wrong `job.hpp` or `types.hpp` when two directories contain one; that is ambiguous and prone to build-system error.
- **correct:** `#include "sub0pipeline/job.hpp"` then `#include <vector>` then `#include <doctest/doctest.h>`
- **incorrect:** `#include <sub0pipeline/job.hpp>`   `#include "job.hpp"`   `#include "../job.hpp"`
- **detect:**
  ```bash
  rg -n -P "#\s*include\s*<$LIB/" $G $SCOPE                       # own header in angle brackets
  rg -n -P "#\s*include\s*\"(?!$LIB/)[^\"]*\"" $G $SCOPE         # quoted, not library-rooted
  ```
  False positives for the second: a quoted vendored third-party header (`"doctest.h"`) violates only the `<>` half, and only if the vendor directory is on the include path; a test-tree helper header (`"test_helpers.hpp"`) has no library root, so list it separately and raise it as a question, not a finding.
- **severity:** STYLE/SHOULD
- **overrides:** none. Replaces the Sub0Pipeline and Sub0Pub `STYLE_GUIDE.md` include sections.

### S05 pragma-once
- **value:** every header starts with `#pragma once`; no named include guards.
- **status:** decided
- **why:** simpler, no guard-name collisions.
- **correct:** `#pragma once`
- **incorrect:** `#ifndef CROG_SUB0PUB_BROKER_SUBSCRIBE_HPP`
- **detect:**
  ```bash
  rg --files-without-match '#pragma once' -g '*.hpp' -g '!**/vendor/**' $SCOPE       # headers lacking it
  rg -n -P '^\s*#\s*ifndef\s+\w+(_HPP|_H|_H_|_HPP_|_INCLUDED)\b' -g '*.hpp' $SCOPE   # named guards
  ```
  False positive: an `#ifndef` that provides a feature-flag default rather than a guard (inspect the next line for the matching `#define` and whether the file also has `#pragma once`).
- **severity:** STYLE/SHOULD
- **overrides:** `[OVERRIDE]` `cpp-idioms.md > File organisation` finding table (`#ifndef` guard = NICE).

### S06 file-names
- **value:** headers `.hpp`, sources `.cpp`, names snake_case; a file is named after its primary type (`class JobGroup` lives in `job_group.hpp`). No `.h`, `.cc`, `.cxx`, `.inl`, and no uppercase or hyphens in source file names.
- **status:** decided
- **why:** consistent discovery by file name; one extension family.
- **correct:** `include/sub0pipeline/job_group.hpp`
- **incorrect:** `JobGroup.h`, `jobGroup.hpp`, `job-group.hpp`
- **detect:**
  ```bash
  rg --files $SCOPE -g '*.{h,cc,cxx,hxx,inl}' -g '!**/vendor/**'                          # wrong extension
  rg --files $SCOPE -g '*.{hpp,cpp}' -g '!**/vendor/**' | tr -d '\r' | grep -E '[A-Z-]'   # case or hyphen
  ```
  Primary-type naming is judgement (S07). False positives: third-party sources outside `vendor/`; generated files.
- **severity:** STYLE/SHOULD
- **overrides:** `[OVERRIDE]` `cpp-idioms.md > File extensions and naming`; the `cpp-review` step 8 rule that a header and its source share a basename keeps its principle, with snake_case names.

### S07 one-primary-type-per-header
- **value:** one primary type per header; tightly coupled helpers (tag types, return structs, trivial guards) may share it.
- **status:** decided
- **why:** a reader finds a type from the file tree alone.
- **correct:** `executor/priority_executor.hpp` declares `PriorityExecutor` and its private helpers.
- **incorrect:** `types.hpp` collecting several unrelated public types.
- **detect:** judgement. Candidate list: `rg -c -P '^(?:template\s*<[^>]*>\s*)?(?:class|struct)\s+[A-Z]\w+[^;]*$' -g '*.hpp' $PUBLIC` counts namespace-scope type declarations per header; read any header with 3 or more, and any header whose name does not match its first type.
- **severity:** STYLE/SHOULD (generic `cpp-idioms.md > One primary type per file pair` is the same principle at SHOULD; report once).
- **overrides:** none.

### S08 folders-and-umbrella
- **value:** headers grouped by concept in coherent folders, each folder with an umbrella header that includes its members (`executor/` with `executors.hpp`); a top-level umbrella (`sub0pipeline/sub0pipeline.hpp`) includes everything; internal helpers live in `detail/`.
- **status:** decided
- **why:** the file tree maps the concepts, and users can include one area at a time.
- **correct:** `sub0pipeline/executor/*.hpp` plus `sub0pipeline/executors.hpp`
- **incorrect:** a folder of headers with no umbrella; an umbrella missing a member.
- **detect:**
  ```bash
  for d in $(cd include/$LIB && ls -d */ 2>/dev/null | tr -d '/'); do ls include/$LIB/$d.hpp include/$LIB/${d}s.hpp 2>/dev/null | head -1 | grep -q . || echo "no umbrella for $d/"; done
  ```
  Then check each umbrella includes every sibling header (judgement). The `${d}s.hpp` form accepts a plural umbrella name.
- **severity:** STYLE/NICE
- **overrides:** none.

### S09 test-names
- **value:** tests are doctest, one file per topic named `test_<topic>.cpp`; shared test helpers `test_<topic>.hpp`.
- **status:** decided
- **why:** `ctest` and file listings group by prefix.
- **correct:** `tests/test_cancel.cpp`
- **incorrect:** `tests/CancelTests.cpp`
- **detect:** `rg --files tests -g '*.cpp' -g '!**/vendor/**' -g '!test_*.cpp'`. False positives: benchmark or audit programs (`bench_*.cpp`, `audit_*.cpp`) are not tests; list them as "exempt, verify" if they follow a documented `bench_` / `audit_` prefix.
- **severity:** STYLE/NICE
- **overrides:** `[OVERRIDE]` `cpp-review` step 8 / `cpp-idioms.md` (`<Basename>Tests.cpp`).

### S10 layout
- **value:** 4-space indent, no tabs. Allman braces (opening brace on its own line) for namespaces, types, functions **and control flow**. Measured 2026-10-06 over headers, sources, tests and examples, control-flow statements only: Sub0ECS 242 own-line and 0 same-line; Sub0Pub 53 own-line and 5 same-line; Sub0Pipeline 0 own-line and 158 same-line. Two of the three libraries are Allman in practice, including Sub0Pub against its own `STYLE_GUIDE.md`; Sub0Pipeline follows its guide's same-line rule and is the outlier to convert. The Sub0Pipeline and Sub0Pub guides, which say control flow takes a same-line brace, are superseded by this rule.
- **status:** decided
- **why:** one layout; matches the code.
- **correct:** `if (x)` newline `{`
- **incorrect:** `if (x) {`
- **detect:**
  ```bash
  rg -c -P '^\t' $G $SCOPE                                                                                          # tabs
  rg -n -P '^\s*(?:\}\s*)?(?:if|else|for|while|switch|do|try|catch)\b.*\{\s*$' $G $SCOPE   # control flow, same-line brace (includes `for (a; b; c) {`)
  rg -n -P '^\s*(?:template\s*<[^>]*>\s*)?(?:class|struct|union|namespace|enum(?:\s+class)?)\b[^;()]*\{\s*$' $G $SCOPE   # type or namespace, same-line brace
  # candidates: function, method or test-case body opened on the signature's line
  rg -n -P '^\s*(?!(?:if|else|for|while|switch|do|try|catch|namespace|class|struct|union|enum|return)\b)[^=\[\]]*\)\s*(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?(?:final\s*)?(?:->\s*[\w:<>,\s&*]+)?\{\s*$' $G $SCOPE
  ```
  False positives: a `do {` inside a macro; a type opened on one line with a braced initialiser. The function generator also catches the last line of a multi-line control-flow condition (`&& ready) {`), which is a real violation counted under control flow, and it deliberately skips any line containing `[`, `]` or `=`, so lambda bodies and braced initialisers are exempt. Tally per tree (`include`, `src`, ...) because trees often differ. Measured on Sub0Pipeline before its conversion: 174 control-flow, 73 type or namespace, 121 function-generator lines; all three were 0 afterwards.
- **severity:** STYLE/NICE (a formatter should own this; see Q-FORMAT)
- **overrides:** none.

### S11 type-case
- **value:** types, templates, aliases and enumerations are PascalCase.
- **status:** decided
- **why:** distinguishes types from functions.
- **correct:** `class DesktopExecutor`
- **incorrect:** `class desktop_executor`
- **detect:** `rg -n -P '^\s*(?:template\s*<[^>]*>\s*)?(?:class|struct|enum(?:\s+class)?)\s+(?:\[\[\w+\]\]\s*)?(?!std\b|class\b|struct\b)([a-z_]\w*)\b(?!::|\s*;)' $G $SCOPE`. False positives: trait types deliberately mirroring the standard (`is_x`, `x_t`), which are "exempt, verify". Type aliases (`using`) are judgement.
- **severity:** STYLE/SHOULD
- **overrides:** none.

### S12 member-names
- **value:** data members are `camelCase_` (trailing underscore); no `m_` or `s_` prefix, no leading underscore.
- **status:** decided
- **why:** members are visible at a glance without a prefix.
- **correct:** `std::atomic<uint32_t> inFlight_{0};`
- **incorrect:** `m_inFlight`, `inFlight`
- **detect:**
  ```bash
  rg -n -P '\b[ms]_[A-Za-z]' $G $SCOPE                                                                              # m_ / s_ prefix
  rg -n -P '^\s*(?!//|\*)[A-Za-z_][A-Za-z0-9_:<>,*& ]*[ \t*&]_[a-z]\w*[ \t]*(?:\[[^\]]*\])?[ \t]*(?:\{|=|;)' $G $SCOPE   # leading-underscore declaration
  ```
  A member with no underscore at all cannot be grepped reliably: judgement from the sample. False positives: identifiers from third-party headers; a user-defined-literal suffix (`"x"_job`) is excluded by the declaration shape.
- **severity:** STYLE/SHOULD
- **overrides:** `[OVERRIDE]` `cpp-idioms.md > Naming` and the examples using `m_` / `s_` / `g_`; `cpp-write` Examples B and D.

### S13 interface-prefix
- **value:** a virtual interface (a class whose purpose is pure virtual functions) has an `I` prefix. A library with no virtual interfaces has no such types.
- **status:** decided
- **why:** the cost of dynamic dispatch is visible in the name.
- **correct:** `class IExecutor`
- **incorrect:** `class Executor` containing `virtual ... = 0;`
- **detect:** `rg -l '=\s*0\s*;' -g '*.hpp' $SCOPE` lists candidate headers; read each class name in them. False positives: a concrete class that merely contains a pure-virtual member by design (rare). A concept-based customisation point has no virtuals and no prefix.
- **severity:** STYLE/SHOULD
- **overrides:** none (generic `cpp-idioms.md` already uses the `I` prefix).

### S14 macro-and-cmake-prefix
- **value:** macros and CMake options carry the library prefix `SUB0<LIB>_` (upper case).
- **status:** decided
- **why:** avoids collisions across the family.
- **correct:** `#define SUB0PIPELINE_TRACE 0`   `option(SUB0PIPELINE_BUILD_TESTS ...)`
- **incorrect:** `#define TRACE 0`
- **detect:**
  ```bash
  rg -n -P "^\s*#\s*define\s+(?!${LIBU}_)\w+" $G $SCOPE
  rg -n -P "^\s*option\(\s*(?!${LIBU}_)\w+" -g 'CMakeLists.txt' -g '*.cmake' .
  ```
  False positives: macros that configure a third-party header before including it (`DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN`, `ANKERL_NANOBENCH_IMPLEMENT`): "exempt, verify". Plain `set()` variables are not options.
- **severity:** STYLE/SHOULD
- **overrides:** none.

### S15 cmake-alias
- **value:** each library exports an alias target `Sub0X::Sub0X`.
- **status:** decided
- **why:** consumers link one stable name whether the library is vendored or installed.
- **correct:** `add_library(Sub0Pipeline::Sub0Pipeline ALIAS sub0pipeline)`
- **incorrect:** consumers linking the bare target name only.
- **detect:** `rg -n "add_library\(\s*${CMAKE_LIB}::${CMAKE_LIB}\s+ALIAS" -g CMakeLists.txt .` should return one hit.
- **severity:** STYLE/SHOULD
- **overrides:** none.

### S16 nodiscard
- **value:** audit rule, not a mechanical one. Flag a function that lacks `[[nodiscard]]` where discarding its result is a wasted computation or a likely usage error: a pure query, a factory or builder result that is the point of the call, a status or error return, an acquired resource. Do not flag fluent builder methods returning `*this`, nor functions called for their side effect whose return value is incidental.
- **status:** provisional (the exact definition still needs design thought; refine this block rather than inventing a second rule)
- **why:** a dropped result of these kinds is almost always a bug the compiler can catch for free.
- **correct:**
  - `[[nodiscard]] bool contains(JobId) const noexcept;` (pure query)
  - `[[nodiscard]] std::expected<void, PipelineError> run(...);` (status)
  - `[[nodiscard]] Job addJob(...);` (the result is the point of the call)
  - `Builder& withName(std::string_view);` (fluent, returns `*this`: no attribute)
  - `bool notify() noexcept;` called for its effect with the return incidental: no attribute. A status return whose loss matters stays flagged.
- **incorrect:**
  - `std::size_t size() const noexcept;` (pure query, no attribute)
  - `std::expected<void, Error> validate();` (status silently droppable)
- **detect:** judgement. Mechanical candidate generator (single-line headers only; a multi-line signature is missed):
  ```bash
  N1='^(?![^\n]*\[\[nodiscard\]\])(?![ \t]*(?:return|using|friend|//|\*|/\*))[ \t]+(?:(?:static|virtual|inline|constexpr)[ \t]+)*(?!void\b)[\w:<>,*&]+(?:[ \t*&]+)[a-zA-Z_]\w*\([^;{]*\)[ \t]*const\b[^;{]*[;{]'
  N2='^(?![^\n]*\[\[nodiscard\]\])(?![ \t]*(?:return|using|//|\*|/\*))[ \t]+[^\n]*(?:std::expected<|\bbool\b)[^\n(=]*\b[a-zA-Z_]\w*\([^\n]*(?:;|\{|\}|,|\()[ \t]*$'
  rg -n -P "$N1" -g '*.hpp' $PUBLIC     # const (query) members without the attribute
  rg -n -P "$N2" -g '*.hpp' $PUBLIC     # status-like returns without the attribute
  ```
  Read each hit and decide against the value above. False positives: a lambda in a default argument, an `override` whose base already carries the attribute, a `bool` that is a genuine side-effect convenience. A lambda written at class or namespace scope matches the candidate pattern (seen in Sub0Pipeline `pipeline.hpp`); it is not a function declaration.
- **severity:** STYLE/CANDIDATE. Report each candidate with a short justification ("pure query", "status return", ...); never report a count of functions lacking the attribute.
- **overrides:** refines `cpp-idioms.md > [[nodiscard]] heuristics` for Sub0; where the two disagree on a case, this block wins.

## Open items

Report each as a **question** carrying the stated preference. Never a finding, never counted as a violation. Tally the current spread so the owner can see it.

### O1 constants-and-enumerators
- **value:** preference: no prefix, `enum class`, CapitalCase type-like names (`Timeout`, `Invalid`, `MaxWorkers`). Today the libraries differ: `k` prefix (Sub0Pipeline enumerators, Sub0ECS constants), `c` prefix (Sub0Pipeline and Sub0Pub constants), unprefixed enumerators (Sub0Pub).
- **status:** open
- **why:** a prefix repeats information the type already carries; under review.
- **correct / incorrect:** not asserted.
- **detect:**
  ```bash
  rg -o -N -I -P '\bk[A-Z]\w+\b' $G $SCOPE | sort | uniq -c | sort -rn    # k prefix
  rg -o -N -I -P '\bc[A-Z]\w+\b' $G $SCOPE | sort | uniq -c | sort -rn    # c prefix
  rg -n -P '^\s*enum\s+(?!class|struct)' $G $SCOPE                        # unscoped enum
  ```
  False positives for `c[A-Z]`: any camelCase identifier beginning with `c` (for example a parameter named `cGroup`); read before counting. An unscoped `enum` is a separate generic finding (`cpp-modernisation.md`).
- **severity:** STYLE/QUESTION
- **overrides:** none.

### O2 namespace-scheme
- **value:** preference: `sub0::pipeline` if a cross-library audit of sub-namespaces and aliases allows it; today `sub0pipeline`, `sub0ecs`, and bare `sub0` (Sub0Pub).
- **status:** open
- **why:** the full name avoids conflicts; the nested form reads cleaner. Needs the cross-library audit first.
- **correct / incorrect:** not asserted.
- **detect:** `rg -o -N -I 'namespace [a-z0-9_:]+' $G $SCOPE | sort | uniq -c`
- **severity:** STYLE/QUESTION
- **overrides:** none.

### O3 template-spacing
- **value:** preference: undecided. Two `STYLE_GUIDE.md` files say `template< typename F >`; the code is tight (`template<typename F>`).
- **status:** open
- **why:** documentation and code disagree.
- **detect:** `rg -c -P 'template\s*<\s' $G $SCOPE` versus `rg -c -P 'template\s*<\S' $G $SCOPE` (sum per tree).
- **severity:** STYLE/QUESTION
- **overrides:** none.

### O4 error-handling
- **value:** preference: undecided; partly domain-driven. Today: `std::expected` plus an exceptions switch (Sub0Pipeline), no exceptions and no RTTI (Sub0ECS), assert-or-throw (Sub0Pub).
- **status:** open
- **why:** embedded targets constrain it.
- **detect:** `rg -c -P 'std::expected|\bthrow\b|\bnoexcept\b|\btry\s*\{' $G $SCOPE` (tally only).
- **severity:** STYLE/QUESTION
- **overrides:** none.

### O5 language-level
- **value:** preference: undecided. Sub0Pipeline and Sub0Pub C++23, Sub0ECS C++20. The generic baseline is C++17.
- **status:** open
- **why:** the features available differ.
- **detect:** `rg -n 'CXX_STANDARD|cxx_std_' -g CMakeLists.txt -g '*.cmake' .`
- **severity:** STYLE/QUESTION
- **overrides:** none (the generic C++17 baseline is superseded as a baseline, not as a rule).

### O6 test-dependencies
- **value:** preference: undecided. Vendored in two libraries, fetched with CPM in one.
- **status:** open
- **why:** reproducibility versus duplication.
- **detect:** `rg -n 'FetchContent|CPM|vendor' -g CMakeLists.txt -g '*.cmake' .`
- **severity:** STYLE/QUESTION
- **overrides:** none.

### O7 include-order
- **value:** preference: undecided. Only quoting and rooting (S04) are decided. Today: ECS std first then project; Pub project first; generic corresponding-header first.
- **status:** open
- **why:** three orders in use.
- **detect:** judgement; do not tally.
- **severity:** STYLE/QUESTION
- **overrides:** none.

### O8 multi-line-doc-comment-form
- **value:** preference: `/** */` for any multi-line doc comment, as the generic reference and all three style guides say. Sub0Pipeline contains stacked `///` blocks.
- **status:** open
- **why:** the owner decisions do not mention the form.
- **detect:** `rg -n -U -P '^[ \t]*///(?!<)[^\n]*\n[ \t]*///(?!<)' -g '*.hpp' $PUBLIC`. False positive: two adjacent single-line docs for different declarations (rare).
- **severity:** STYLE/QUESTION
- **overrides:** none (generic `cpp-commenting.md` MUST stays in force until the owner decides).

### Q-FORMAT formatter-config
- **value:** none of the three libraries has `.clang-format`, `.clang-tidy` or `.editorconfig`. Layout rules (S10) would be better owned by a formatter than by review; whether to add one is a question for the owner.
- **status:** open
- **why:** mechanical layout does not belong in review.
- **detect:** `ls .clang-format .clang-tidy .editorconfig 2>/dev/null`
- **severity:** STYLE/QUESTION
- **overrides:** none.
