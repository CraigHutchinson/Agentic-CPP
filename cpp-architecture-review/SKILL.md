---
name: cpp-architecture-review
description: Whole-system architecture and coherence review across one or more C++ repositories that serve one product family. Reviews the approach itself (technique, algorithm, numerical method), algorithmic redundancy (the same quantity computed twice, the same formula implemented in several places), the same problem solved differently in parallel (boundary rules, sign conventions, error channels, units, ids, result idioms, determinism flags), DRY across repositories (tooling, scripts, workflows, test helpers), contracts that upcoming work will build on, and claims (docs, perf gaps, parity) against the code. It consolidates its findings into canonical decisions and an ordered plan. Complements cpp-review: cpp-review judges a diff, plan or single repository through layers L0-L3, and this skill judges whether the parts form one coherent solution. Invoke at phase boundaries (before a new milestone builds on existing contracts), after a burst of parallel or delegated work, or when asked for a holistic, consolidation or cross-project review. Read-only until the plan is accepted.
allowed-tools: Read, Glob, Grep, Bash
---

# Architecture and coherence review

A per-change review asks "is this change good?". This review asks "is the *system* the right solution, and
is it one solution?". It catches what diff reviews miss:

- **Parallel work.** Two pieces of work each pass review, but they solved the same problem in two different
  ways.
- **Duplicated computation.** A formula computed by two representations agrees only to rounding.
- **Unsettled contracts.** A contract that the next milestone will sum, extend or inherit is not yet fixed.
- **Unused API.** An API was added "for later" and never had a consumer.

## When to invoke

- **At a phase boundary,** before the next milestone builds on existing contracts. This is the cheapest
  fix point: once a second consumer exists, a sign convention or a result shape is expensive to change.
- **After a burst of parallel or delegated work** (several agents or authors, several repositories).
- **On request** for a "holistic", "consolidation", "approach" or "cross-project" review.
- **Skip** single-change reviews; use `cpp-review` for those.

## Inputs

- **Repositories and snapshots.** Record the commit of every repository reviewed; findings cite
  `repo:path:line` at those commits.
- **Decision records.** The ADRs, design documents and roadmaps the code claims to follow. Contradictions
  between them and the code are findings.
- **Reference implementations.** Upstream ports, oracles and golden data. When reviews disagree about a
  rule (for example, an equality boundary), the reference implementation settles it. Read it; don't
  vote.

## Lenses

Apply every lens. Each finding carries an ID, a severity (High, Medium, Low), a lens, its location, the
finding, a proposed fix, an owner (which repository) and an effort (S, M, L).

### A. Approach and technique

- **Is the algorithm the right one** for the size, accuracy and determinism the system needs? Name the
  known method, with a citation where useful, and say why the chosen one is better or worse. For example:
  a tree-sparse factorisation against a dense one, a windowed search against a brute-force scan, a
  projection along the support normal against a vertical one.
- **Hot paths:** per-call allocation, work that can be prepared once and reused, branchy code where a
  status aggregate would do, and an ordinary library call (`fmax`, `hypot`) that compiles to a slow
  external call on one toolchain.
- **Numerics:**
  - floating-point contraction and its control across all targets, including header-inline code compiled
    with the consumer's flags;
  - the source of transcendental functions;
  - subnormals;
  - NaN and range guards before any float-to-integer conversion;
  - operand order where bit-exact parity is claimed.

### B. Algorithmic redundancy

- **The same quantity computed through two representations** (for example, a quaternion half-angle path
  and a rotation-matrix path from one joint angle). This costs twice the work, and the results agree only
  to rounding.
- **The same formula in several places:** library, reference adapter, test transcription. Keep exactly one
  implementation, and give it an independent check (finite differences, an energy identity, a brute-force
  oracle) instead of copies.
- **Recomputation per call** of data that could be prepared once: segment normals, reciprocals, windows.

### C. Same problem, solved differently

Build an **inventory**: for each concept, list every implementation and its rule. Concepts that drift
often:

| Concept | Typical drift |
|---|---|
| Boundary and ownership rules | Half-open against closed against asymmetric cell or interval rules |
| Sign and direction conventions | "Spreading" force against generalized force; normal orientation |
| Result and status idioms | `std::optional`, status aggregates and `std::expected` used for the same role |
| Error channels | Several error types for "bad caller input"; validation helpers copied |
| Units and time at boundaries | Raw `double` against quantities; time as a float against ticks |
| Identifiers and sentinels | Two "none" sentinels; roles used as ids without hash or invalid value |
| Steppers and solvers | Two state shapes or time contracts; a planned third family |
| Determinism flags | Per-file lists that differ by compiler |
| Names and spelling | One fixture under two names; regional spelling mixed |

For each concept, propose one **canonical** rule, name its owner, and state the migration risk.

### D. DRY across repositories

- Duplicated scripts, CI workflows, vendored dependencies and test-support helpers.
- Duplicated tracking that raises the same alert twice (for example, two manifests watching one upstream
  file).
- Prefer one shared home that every consumer already locates, such as the shared tooling repository.
  Each consumer keeps only its own data.

### E. Contracts before builders

- List every contract that the next milestone will **sum, extend or inherit**: element responses, stepper
  signatures, result shapes, ids, grid rules. Any disagreement there is High severity, because it is
  cheapest to fix now.
- APIs with **no consumer** are debt under "grow by use". Either adopt them in the consumer they were
  built for, or withdraw them.

### F. Evidence and claims

- **Documents against code:** READMEs, design documents, decision records and "status" lines.
- **Performance claims reproduce:** open gaps, "bit-identical" statements, and every new API with a
  hand-written twin. Never accept a speedup that came from weakening the reference.
- **Tests are independent evidence,** not transcriptions of the formula under test.
- **Gates enforce what they claim,** and CI runs what the documents say it runs.

### G. Tooling and process

- Gates: whether they fail open or closed, whether they measure the commit that ships, locking, atomic
  writes, recorded seeds.
- CI coverage: every compiler and target class whose behaviour differs, for example an FMA-capable build
  when determinism is claimed.

## Process

1. **Scope.** Record the snapshot commits, the decision records and the reference implementations.
2. **Fan out the lenses.** Use several independent read-only reviewers, run in parallel when delegation
   is available: one per repository (whole-repository `cpp-review` L0-L3 plus lenses A, B and F), one
   for cross-repository coherence (lenses C, D and E), and one for tooling and process (lens G). Each
   reports a findings table and its proposed order.
3. **Verify before accepting.** Re-read the code behind each High finding. Settle disagreements with the
   reference implementation. Re-measure performance claims on a quiet machine: concurrent builds produce
   false regressions, and recorded gaps may no longer reproduce.
4. **Consolidate.** Merge duplicate findings across the reports, keeping their source IDs. Then produce:
   - **Canonical decisions** (D1…Dn): one row per topic, with the decision, its sources and its owner.
     The reviewer decides wherever a directive, a reference or the evidence settles it.
   - **Correctness defects:** fix these first.
   - **Redundancy removed:** a list of "N implementations become one".
   - **An ordered plan:** waves aligned with the roadmap. Each contract wave lands before the milestone that
     builds on it. Parallel waves touch disjoint repositories or directories.
   - **Owner decisions:** only questions that no directive, reference or evidence settles (policy, risk
     appetite). Give one recommendation for each.
5. **Publish** the consolidated review in `docs/reviews/YYYY-MM-DD-<topic>.md`, in the most private
   repository whose internals it describes, so public repositories never name private ones. Keep a
   progress table in it that is updated as each wave merges.
6. **Execute and verify.** Each wave is reviewed, merged and verified by building and testing on every
   compiler class the decision affects. Results that differ from the plan's expectations, such as a gap
   that did not reproduce or a rule settled differently, are recorded in the review document.

## Output format

```markdown
# Consolidated review and plan (YYYY-MM-DD)
- Scope / inputs (repos @ commits, reviewer reports and their ID prefixes)
## 1. Verdict           (3-6 sentences: sound or not, and the shape of the problems)
## 2. Canonical decisions   | # | Topic | Decision | Sources |
## 3. Correctness defects   | Defect | Source |
## 4. Algorithmic redundancy removed   (bullets: "X implementations -> one")
## 5. Ordered plan          | Wave | Work | Repo | Agent/owner |
## 6. Owner decisions       (numbered, each with a recommendation)
## 7. Progress              | Wave | State |
```

## Relationship to the other skills

- **`cpp-review`** supplies the per-repository L0-L3 analysis that this review consumes. It stays the tool
  for individual changes and plans.
- **`cpp-write`** applies the canonical decisions while authoring. Add any decision that should bind future
  code to the project's STYLE_GUIDE or decision records, so later reviews can cite it as a directive.
- **`cpp-simplify`** can execute a wave whose findings are mechanical rewrites.

## Anti-patterns

- **A list of findings with no consolidation.** The value is in the canonical decisions and the order.
- **Voting between reviewers** on a rule that a reference implementation can settle.
- **Accepting performance claims, "fixed" gaps or "bit-identical" statements without re-measuring or
  re-diffing.**
- **Asking the owner questions that the evidence answers.** Decide them, and record the reasoning.
- **Publishing private-repository internals into a public repository's documents.**
