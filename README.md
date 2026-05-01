# Agentic-CPP

AI agent personas for C++17 development, for use with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [Cursor](https://cursor.com).

**cpp-write** authors to standard before you start. **cpp-review** catches L0--L3 issues in code diffs and design plans. **cpp-simplify** rewrites from findings. **cpp-project-init** bootstraps a new project. Shared C++17 reference material (modernisation, idioms, commenting hygiene, anti-patterns) is loaded by all four.

---

## Skills

| Skill | When to invoke | What it does |
|---|---|---|
| **cpp-write** | Before authoring a new class, public API, or module | Loads reference material and applies a 7-step authoring checklist to produce zero-finding code on the first pass |
| **cpp-review** | After substantive C++ changes | L0--L3 layered design review: intent, structural/boundary, API contract, implementation. Also supports **plan review mode** -- catch issues in a design document before any code is written |
| **cpp-simplify** | After L0/L1 MUST findings from cpp-review | Applies the Rewrite Brief from cpp-review to rewrite the commit cleanly |
| **cpp-project-init** | Once per new project | Stamps `.cursor/rules/cpp-standards.mdc`, a `## C++ Skills` section in `AGENTS.md`, and a base `.clang-tidy` into the project |

Shared reference material in `cpp/references/` is loaded by all four skills:

| File | Purpose |
|---|---|
| `cpp-idioms.md` | Reinvention catalogue, API design smells, file organisation rules |
| `cpp-modernisation.md` | C++17 idiom tiers, project-specific type overlay, globals/testability seam pattern |
| `cpp-commenting.md` | Doc comment MUST/SHOULD table, doc templates, ownership annotation conventions |
| `cpp-anti-patterns.md` | Finding categories learned not to raise; overriding principle |

---

## Rules at a glance

The reference material encodes these themes across all four skills:

| Rule | One-liner |
|---|---|
| **Reinvention** | Don't recreate a utility that already exists -- grep before you write |
| **File location** | Code lives where a teammate would search for it six months from now |
| **API naming** | Names encode the question the call site is actually asking |
| **Type-system contracts** | Encode invariants in types, not prose -- `[[nodiscard]]`, `noexcept`, `static_assert` |
| **Comment hygiene** | WHY not WHAT; no phase/roadmap labels; public surfaces need doc comments |
| **Modernisation** | Prefer C++17 idioms and project-specific types (`core::*`) over raw-standard equivalents |
| **Simplification / DRY** | The simplest correct shape is the right shape; repeated structure signals a missed abstraction |
| **Globals and testability** | File-statics and latched singletons create cross-test order-dependence |
| **Testability paths** | Additive API first, then structural refactor, then (last resort) signature change |
| **Semantic contract drift** | New API that weakens an existing type's implicit guarantee requires user discussion |
| **Retroactive coverage** | Adding tests to uncovered APIs is always valid -- flag the missing seam, not the test |
| **L0--L3 hierarchy** | Review descends Intent → Structural → API → Implementation; MUST at any layer stops the rest |
| **Plan first** | Run plan-review mode before writing code -- L0/L1 fixes cost nothing at the design stage |
| **Gaps and assumptions** | Ask rather than assume when no directive covers a design choice |
| **Iterative review** | Loop until clean; retrospective captures decisions-without-directive for encoding |

---

## Review layers (L0–L3)

All four skills share a layered review framework applied by `cpp-review` and mirrored proactively by `cpp-write`. Each layer is a strict gate: a MUST finding at any layer stops the review from descending to the next until the finding is addressed.

| Layer | Name | Question | Fires on |
|---|---|---|---|
| **L0** | Intent / Decomposition | Is this the right thing, at the right scope, with the right complexity? | Commit message mismatches, dead scaffolding, over-engineering, simpler solution exists |
| **L1** | Structural / Boundary | Is it structured correctly and in the right place? | Wrong abstraction, module boundary violation, DRY violation, single-impl interface |
| **L2** | API / Contract | Is the public surface correct and complete? | Naming smells, missing `[[nodiscard]]` / `noexcept`, unencoded ordering constraints, `std::*` on project-typed API |
| **L3** | Implementation | Is the implementation idiomatic and documented? | Legacy idioms, modernisation failures, missing ownership annotations, stale comments |

`cpp-review` runs L0–L3 in code-review mode and L0–L2 in plan-review mode (L3 is skipped for plans — no implementation to inspect). A MUST at L0 or L1 defers all lower-layer findings until the structural issue is resolved; they are listed under "Deferred pending redesign" rather than dropped.

---

## Installation

### Option A -- live location (recommended: edit once, use everywhere)

Clone directly into your Cursor user skills directory so the live files are the repo:

```bash
# Back up any existing cpp skills first if needed
git clone https://github.com/CraigHutchinson/Agentic-CPP.git "%USERPROFILE%\.cursor\skills"
```

On macOS / Linux:

```bash
git clone https://github.com/CraigHutchinson/Agentic-CPP.git ~/.cursor/skills
```

Skills are then available at the paths the personas expect (`~/.cursor/skills/cpp-write/SKILL.md`, etc.).

### Option B -- separate clone, copy to skills directory

```bash
git clone https://github.com/CraigHutchinson/Agentic-CPP.git
# Windows:
xcopy /E /I Agentic-CPP\* "%USERPROFILE%\.cursor\skills\"
# macOS / Linux:
cp -r Agentic-CPP/* ~/.cursor/skills/
```

---

## Global User Rule (Cursor)

Add the following to **Cursor Settings → Rules** so every Agent session knows these skills exist:

```
When writing or reviewing C++ code, apply the following workflow:

- Before authoring a new class, public API, or module: invoke the cpp-write skill at `~/.cursor/skills/cpp-write/SKILL.md` to front-load standards and prevent review findings.
- After substantive C++ changes: invoke the cpp-review skill at `~/.cursor/skills/cpp-review/SKILL.md` to catch API, structural, and modernisation issues.
- Before implementing from a plan or design document: invoke cpp-review in plan review mode -- catches L0/L1 issues before any code is written.
- After L0/L1 MUST findings from cpp-review: apply the Rewrite Brief using the cpp-simplify skill at `~/.cursor/skills/cpp-simplify/SKILL.md`.

Full C++ reference material (reinvention catalogue, modernisation playbook, idiom checklist, commenting hygiene):
`~/.cursor/skills/cpp/references/`
```

---

## Per-project setup

Run `cpp-project-init` in any new C++ project to stamp the project-level Cursor rule and AGENTS.md section automatically. If an org overlay is present (`~/.cursor/skills/org/references/`), the skill loads it and appends project-specific constraint blocks (custom allocators, type preferences, build macros) on top of the generic C++ conventions.

---

## Workflow

```
Design doc / plan
      │
      ▼
cpp-review (plan mode)   ← catch L0/L1 before writing
      │ passes
      ▼
cpp-write                ← author to standard, zero-finding target
      │
      ▼
cpp-review (code mode)   ← verify after authoring
      │ L0/L1 MUST fires
      ▼
cpp-simplify             ← apply Rewrite Brief
```

---

## Contributing

The `cpp/references/` files are the shared knowledge base. Improvements to any of them benefit all four skills simultaneously and should be pushed back to this repo so the whole team gets the update.

### When to extend each file

| File | Trigger |
|---|---|
| `cpp-anti-patterns.md` | A finding type is rejected with the same reason on two or more PRs |
| `cpp-modernisation.md` | A new safe-modernisation pattern is validated and proven consistent |
| `cpp-idioms.md` | A new project utility enters the reinvention catalogue, or an API design smell is confirmed |
| `cpp-commenting.md` | A recurring comment anti-pattern or suppression is identified |

### Commit workflow

After extending any reference file, commit and push immediately so the change is live for the whole team:

```bash
git -C ~/.cursor/skills add cpp/references/<filename>.md
git -C ~/.cursor/skills commit -m "<filename>: <what changed> -- <why>"
git -C ~/.cursor/skills push
```

Commit message convention: name the file, state the change (suppress / add / update), and give the one-line reason -- the same "WHY not WHAT" rule that applies to all code commits. The file history becomes the team's accumulated review judgement.

### Skill files

Changes to `SKILL.md` files (new sections, updated invocation patterns, new worked examples) follow the same workflow. Pull requests welcome for substantial changes.
