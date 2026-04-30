---
name: cpp-project-init
description: Bootstrap a new C++ project with the cpp-write / cpp-review / cpp-simplify skill ecosystem. Creates .cursor/rules/cpp-standards.mdc (auto-attached on C++ files via glob), adds a C++ Skills section to AGENTS.md or CLAUDE.md, and optionally creates a base .clang-tidy. Invoke once when starting a new project or repository. Safe to re-run: reports conflicts rather than overwriting.
allowed-tools: Read, Glob, Grep, Bash, Write, Edit
---

# C++ Project Init

One-shot setup skill. Stamps the C++ skill ecosystem into the current working directory. Produces a setup report listing every file created, appended, or skipped.

## What it creates

| File | Action | Purpose |
|---|---|---|
| `.cursor/rules/cpp-standards.mdc` | Create (skip if exists) | Auto-attaches C++ standards and skill pointers when C++ files are in Agent context |
| `AGENTS.md` or `CLAUDE.md` | Create or append section | Adds `## C++ Skills` pointing to cpp-write, cpp-review, cpp-simplify |
| `.clang-tidy` | Create (skip if exists) | Base `modernize-*` / `readability-*` / `bugprone-*` configuration |

## Execution steps

Follow in order. Do not skip steps.

### Step 1 -- Detect project state

1. Confirm the current working directory is the project root (contains a `src/` or source tree, or a build file, or a `.git/`). If unsure, ask before proceeding.
2. Check for `.cursor/rules/cpp-standards.mdc` -- record: create or skip.
3. Check for `AGENTS.md` -- if absent, check for `CLAUDE.md`. Record which file to append to, or that neither exists.
4. Check for `.clang-tidy` -- record: create or skip.
5. Check whether `.cursor/rules/` directory exists; note if it needs to be created.

### Step 2 -- Detect project variant

Check for Unity-specific markers to decide which constraint block to include in the project rule:

```bash
# Unity project if any of these exist:
ls Modules/NativeKernel 2>/dev/null || ls Runtime/Misc 2>/dev/null || grep -r "UNITY_NEW" --include="*.h" -l -m1 2>/dev/null
```

Record: `unity` (Unity engine codebase) or `generic` (any other C++ project). This selects the constraint block written in Step 3.

### Step 3 -- Write .cursor/rules/cpp-standards.mdc

Create `.cursor/rules/` if it does not exist. Then write the file below.

For a **Unity** project, include the Unity constraint block. For a **generic** project, include the generic constraint block. Both share the same header and skill-invocation table.

```mdc
---
description: C++ authoring and review standards. Auto-attaches when C++ files are in Agent context. Points the agent to cpp-write (before authoring) and cpp-review (after changes).
globs: "**/*.cpp,**/*.h,**/*.hpp,**/*.inl,**/*.cc"
alwaysApply: false
---

# C++ Standards

## Skill invocation

| Trigger | Skill |
|---|---|
| Before writing a new class, public API, or module | **cpp-write** (`~/.cursor/skills/cpp-write/SKILL.md`) |
| After substantive C++ changes | **cpp-review** (`~/.cursor/skills/cpp-review/SKILL.md`) |
| Before implementing -- to review a plan or design doc | **cpp-review** (plan review mode) |
| After L0/L1 MUST findings | **cpp-simplify** (`~/.cursor/skills/cpp-simplify/SKILL.md`) |

Full reference material: `~/.cursor/skills/cpp/references/`

---

## MUST constraints (produce review findings if violated)
```

**Append for Unity projects:**

```mdc
**Types** -- use `core::*` not `std::*` in engine code:
- `core::string` / `core::string_ref` (not `std::string` / `std::string_view`)
- `core::vector<T, kMemLabel>` (not `std::vector`) -- `T` must be trivially relocatable; self-pointers or intrusive-list nodes cause silent reallocation corruption
- `core::hash_map` / `core::hash_set` / `core::array_ref<T>` for maps, sets, spans
- MUST on public API; SHOULD in implementation-only code

**Memory** -- engine heap objects:
- `UNITY_NEW(kMemLabel, T)(args)` / `UNITY_DELETE(ptr)` -- raw `new`/`delete` bypasses memory profiling; MUST when raw pointer escapes scope
- `std::make_unique<T>` acceptable for RAII-scoped objects only
- `kMem*` labels must be chosen deliberately; `kMemDefault` without a comment is a SHOULD finding

**Global state:**
- `Singleton<T>` (`Modules/NativeKernel/Include/NativeKernel/Utilities/Singleton.h`) for all process-lifetime or cached state
- Never file-statics, function-local statics, or namespace-scope mutable caches
- `Singleton<T>::ScopedOverride` for test isolation -- never `#if ENABLE_UNIT_TESTS_WITH_FAKES`

**Reinvention check** -- before writing any utility:
- String ops → `Word.h` (`StrICmp`, `BeginsWith`, `EndsWith`, `core::Format`)
- Argv → `Argv.cpp` (`HasArgument`, `GetArgumentValue`)
- Path ops → `PathNameUtility.h`; enum ops → `EnumFlags.h` / `EnumTraits.h`

---

## SHOULD constraints

- `[[nodiscard]]` on predicates, `Try*`, observers, `Compute*` / `Resolve*`
- `noexcept` on pure observers and default/move constructors; document terminate-on-failure when wrapping a throwing callee
- Named predicates over enum comparison: `IsBackgroundWorker()` not `GetMode() == Mode::Background`
- No boolean behaviour selectors (`void Process(bool fast)`) -- two named functions or `enum class` parameter
- `#pragma once` (not `#ifndef` guards); filename must exactly match class name including casing (build fails on Linux/macOS on mismatch)
- Raw pointer members require an ownership annotation: `// owning`, `// non-owning`, `// optional-owning`
- Comments explain WHY; no phase/roadmap narrative (`// Phase D will fix this` → `// [TICKET-NNN]`)
```

**Append for generic (non-Unity) projects:**

```mdc
**Types** -- prefer project-established types over `std::*` equivalents. Check the reinvention catalogue (`~/.cursor/skills/cpp/references/idiom-checklist.md > Reinvention catalogue`) for project-specific type preferences before using standard-library alternatives.

**Memory** -- follow the project's allocation conventions. Prefer `std::unique_ptr` / `std::make_unique` for owned heap objects; avoid raw `new`/`delete` outside RAII wrappers.

**Global state:**
- Never use file-statics, function-local statics, or namespace-scope mutable variables for cached or process-lifetime state -- they are testability-hostile (latched once per process, no reset hook)
- Prefer an instantiable provider class with a scoped-active binding (see `~/.cursor/skills/cpp/references/modernisation-playbook.md > Globals, singletons, and testability seam`)

**Reinvention check** -- before writing any utility, grep the project's utility directories for an existing equivalent. Duplicating a project utility is a MUST finding in review.

---

## SHOULD constraints

- `[[nodiscard]]` on predicates, `Try*` functions, observers, and `Compute*` / `Resolve*`
- `noexcept` on pure observers and default/move constructors
- Named predicates over enum comparison at call sites
- No boolean behaviour selectors -- two named functions or `enum class` parameter
- `#pragma once` in all new headers; filename must match class name exactly including casing
- Raw pointer members require an ownership annotation: `// owning`, `// non-owning`
- Comments explain WHY; no phase/roadmap narrative (`// [TICKET-NNN]` references for tracked deferrals)
```

### Step 4 -- Append C++ Skills section to AGENTS.md / CLAUDE.md

Read the target file (if it exists). Search for an existing `## C++ Skills` heading. If found, skip. If not found, append:

```markdown
## C++ Skills

Three skills manage the C++ authoring and review workflow. Full reference material lives in `~/.cursor/skills/cpp/references/`.

| When | Skill | Invoke condition |
|---|---|---|
| Before writing a new class, public API, or module | **cpp-write** | Proactively before authoring |
| After substantive C++ changes | **cpp-review** | Proactively after authoring |
| Before implementing -- to review a plan or design doc | **cpp-review** (plan mode) | Explicitly, with plan doc as input |
| After L0/L1 MUST findings | **cpp-simplify** | With Rewrite Brief from cpp-review as input |

The `.cursor/rules/cpp-standards.mdc` project rule auto-attaches the most important constraints to Agent sessions when C++ files are in context. The skills carry the full reference material and worked examples.
```

If neither `AGENTS.md` nor `CLAUDE.md` exists, create `AGENTS.md` with only this section.

### Step 5 -- Create .clang-tidy (if not present)

```yaml
---
# Base C++ modernisation configuration.
# Project-specific suppressions belong below this comment.
Checks: >
  modernize-*,
  readability-*,
  bugprone-*,
  performance-*,
  -modernize-use-trailing-return-type,
  -readability-magic-numbers,
  -readability-named-parameter
WarningsAsErrors: ''
HeaderFilterRegex: ''
FormatStyle: file
```

### Step 6 -- Emit setup report

```
## C++ project init complete

### Files created
- .cursor/rules/cpp-standards.mdc   -- auto-attaches C++ standards on C++ files
- AGENTS.md (or CLAUDE.md)          -- C++ Skills section appended [or created]
- .clang-tidy                       -- base modernize-*/readability-*/bugprone-* config

### Files skipped (already exist -- review manually)
- <list any skipped files and the reason>

### Next steps
1. Open Cursor Settings → Rules and confirm the global User Rule is present
   (text: "When writing or reviewing C++ code, invoke cpp-write before authoring
   and cpp-review after changes..."). If absent, add it -- it is the global
   catch-all that fires regardless of which project is open.

2. Commit .cursor/rules/cpp-standards.mdc and .clang-tidy to the repository
   so the whole team benefits from the auto-attach rule.

3. If this is a Unity project: verify the Unity constraint block is present in
   cpp-standards.mdc (core::* types, UNITY_NEW, Singleton<T>). If not,
   re-run cpp-project-init -- it auto-detects Unity via filesystem markers.

4. Run cpp-review in plan review mode before the first implementation task:
   invoke with the plan or design document as input to catch L0/L1 issues early.
```

## What the skill must never do

- Overwrite any existing `.cursor/rules/cpp-standards.mdc`, `.clang-tidy`, `AGENTS.md`, or `CLAUDE.md`. Report the conflict, show what would have been written, and stop.
- Create files outside the current working directory.
- Run a build or modify source files.
