# Agentic-CPP

AI agent personas for C++ development: an authoring persona that front-loads standards before writing, an architect reviewer that works against code diffs and design plans, a rewriter that applies findings, and a project bootstrapper. Shared reference material covers modernisation, idioms, commenting hygiene, and anti-patterns.

Designed for use with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [Cursor](https://cursor.com).

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
| `idiom-checklist.md` | Reinvention catalogue, API design smells, file organisation rules |
| `modernisation-playbook.md` | C++17 idiom tiers, project-specific type overlay, globals/testability seam pattern |
| `commenting-hygiene.md` | Doc comment MUST/SHOULD table, doc templates, ownership annotation conventions |
| `anti-patterns.md` | Finding categories learned not to raise; overriding principle |

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

Run `cpp-project-init` in any new C++ project to stamp the project-level Cursor rule and AGENTS.md section automatically. The skill auto-detects Unity engine projects and selects the appropriate constraint block (Unity-specific `core::*` types, `UNITY_NEW`, `Singleton<T>` vs. generic C++ conventions).

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
| `anti-patterns.md` | A finding type is rejected with the same reason on two or more PRs |
| `modernisation-playbook.md` | A new safe-modernisation pattern is validated and proven consistent |
| `idiom-checklist.md` | A new project utility enters the reinvention catalogue, or an API design smell is confirmed |
| `commenting-hygiene.md` | A recurring comment anti-pattern or suppression is identified |

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
