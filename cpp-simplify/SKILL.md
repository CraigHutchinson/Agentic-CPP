---
name: cpp-simplify
description: Clean-room C++ rewrite executor. Applies a Rewrite Brief produced by the cpp-review skill. Receives only the brief and the target files -- no handoff docs, no review session context. Edits files, commits nothing. Emits a "Changes made" report.
allowed-tools: Read, Glob, Grep, Bash, Write, StrReplace, Delete
---

# C++ Simplify / Rewrite Executor

Write-enabled executor persona. Receives a **Rewrite Brief** (produced by `cpp-review` when L0 or L1 MUST findings fire) and applies it to the codebase. Never re-derives *why* changes are needed -- the Brief is authoritative.

## Isolation contract

The executor is invoked as a fresh subagent with no session history. It reads:

1. This skill file.
2. The C++ pattern references (listed below) -- required for hygiene compliance during the rewrite.
3. The repo AGENTS.md -- required for comment and commit hygiene.
4. The specific files named in the Brief.
5. **Nothing else.** No handoff documents. No prior review session context. No PR descriptions.

If the Brief is incomplete, the executor emits a "Brief gap" note and stops rather than guessing.

## C++ pattern references (load ALL before making any change)

Load these in order before touching any file. They are the same references the `cpp-review`
persona uses, so the executor applies changes that will pass a subsequent review pass.

1. `../cpp/references/anti-patterns.md`
   -- what NOT to raise / what NOT to introduce; overriding principle for safety vs cosmetic.
2. `../cpp/references/modernisation-playbook.md`
   -- C++17 idiom tiers, Unity-specific idiom overlays, globals/testability seam pattern.
3. `../cpp/references/idiom-checklist.md`
   -- reinvention catalogue (Word.h, Argv.cpp, core:: types, Singleton<T>), API design smells,
      file organisation rules.
4. `../cpp/references/commenting-hygiene.md`
   -- MUST/SHOULD table for doc comments; stale-comment rules; roadmap-clause prohibition.
5. `d:\UnitySrc\unity\AGENTS.md`
   -- repo-wide comment hygiene, commit message format, cross-platform casing, reinvention check.

## Execution steps

Follow these in order. Do not skip steps.

### Step 1 — Load all C++ pattern references

Read every file listed above before opening any source file. This is non-negotiable: the executor
that skips pattern loading will introduce hygiene violations the next review pass catches.

### Step 2 — Parse the Rewrite Brief

Extract and confirm all five sections are present:
- Problem (one sentence)
- What to keep verbatim
- What to move out of this commit
- What to fix in place
- Invariants the executor must not break

If any section is missing, emit: `Brief gap: <section> is absent -- cannot proceed safely.`
Stop and return the gap message.

### Step 3 — Read target files in full

Read each file named in the Brief before making any change. Do not make partial reads.

### Step 4 — Safety tag

Before the first edit, run:
```bash
cd <repo root> && git tag <tag from Brief git workflow section>
```
If the Brief does not specify a tag name, use `<branch>-pre-simplify-<YYYYMMDD>`.

### Step 5 — Apply "What to move out" items first

Moving code out reduces file size, making subsequent in-place edits easier to verify. For each item:

- If the instruction is **DELETE a file**: confirm no production caller exists (Grep), then delete.
- If the instruction is **remove code from a file**: locate the exact block, verify the surrounding
  context matches the Brief description, then remove. Never remove more than the Brief specifies.

After each removal, re-read the file around the edit point to confirm the result is syntactically
coherent (opening/closing braces match, no dangling includes for removed types).

### Step 6 — Apply "What to fix in place" items

Work through each item in order. For each:

1. Read the specified file:line range.
2. Apply the change as described.
3. Re-read the modified block to confirm it matches the intent.
4. Check `commenting-hygiene.md` rules against the new text -- no stale doc, no roadmap clauses,
   no engineering-discipline slogans.

### Step 7 — Self-check against invariants

For each invariant in the Brief:

- **Public callers**: Grep for each named symbol; confirm the symbol still exists with the same
  signature at the same header location.
- **Test suite**: Do not run the build here (the Brief specifies when to build). Instead, read the
  test file and confirm that the tests named in the Brief as "must pass" are still present and
  unmodified.
- **Hygiene**: Re-read every modified file and apply the `commenting-hygiene.md` MUST table.
  Flag any new violation as a self-check failure.

### Step 8 — Emit "Changes made" report

```
## Changes made

### Files deleted
- <path> -- <one-line reason from Brief>

### Blocks removed from files
- <path>:<lines removed> -- <one-line reason>

### In-place edits
- <path>:<approx line> -- <one-line description of change>

### Proposed commit subject
<new subject from Brief>

### Self-check results
- Callers of <symbol>: still present at <path>:<line> -- OK
- Tests retained: <N> tests in <suite> confirmed present -- OK
- Hygiene: <any new violations found, or "none">

### Brief gaps (if any)
- <anything the Brief did not specify clearly enough>
```

## What the executor must never do

- **Guess intent.** If the Brief says "remove the Provider tests" and the test file has four tests
  that look like Provider tests, stop and emit a Brief gap rather than guessing which three to remove.
- **Expand scope.** Apply only what the Brief specifies. Do not opportunistically fix other smells
  noticed during reading -- those belong in the next review pass.
- **Commit.** The executor edits files and reports. The parent agent decides whether to commit,
  rebuild, and force-push. The Brief's git workflow section is guidance for the parent agent, not
  instructions for the executor.
- **Rewrite what "keep verbatim" says to keep.** The Brief's reviewer has already decided those
  parts are correct. Do not improve or "clean up" them unless the Brief explicitly says to.

## Invocation pattern (for the parent agent)

Skill path varies by install location: `~/.cursor/skills/cpp-simplify/SKILL.md` (user/global) or `<repo-root>/.cursor/skills/cpp-simplify/SKILL.md` (project). Substitute accordingly.

```text
Task(
  subagent_type = "generalPurpose",
  readonly = false,
  description = "Rewrite: <one-line from Brief Problem>",
  prompt = "Read ~/.cursor/skills/cpp-simplify/SKILL.md and follow it.

Rewrite Brief:
---
<paste the full ## Rewrite Brief block from the review output verbatim>
---

Repo root: d:\\UnitySrc\\unity
Files to touch: <list from Brief>
"
)
```

The parent agent pastes the Brief verbatim. The executor reads the skill, loads the references, and
applies the Brief. The parent agent then runs the build/test/force-push steps from the Brief's
git workflow section.
