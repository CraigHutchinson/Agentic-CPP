# cpp-review self-test suite

Self-contained test cases for the `cpp-review` skill. Each case is a C++ snippet
(or snippet pair) with deliberate defects and a machine-parseable oracle
(`expected.yaml`) naming which findings must and must not fire.

## Cases

| # | Directory | Checks exercised | Must-fire | Must-not-fire |
| --- | --- | --- | --- | --- |
| 00 | `00-comprehensive` | Stranger Q1/Q5; L2 API smells (bool selectors, pair return); L3 (C-cast, unscoped enum, typedef, index loop); reinvention; testability bypass | 11 | 1 |
| 01 | `01-anti-pattern-guard` | Input-source suppression -- reviewer must NOT raise null-guard finding | 0 | 1 |
| 02 | `02-l0-dead-code` | L0 production-caller audit -- class with zero callers ships as dead code | 1 | 0 |

See each case's `notes.md` for the defect map and pass criteria.

## Running

### Via the evaluation harness (recommended)

```sh
# From repo root
pip install -r cpp/eval/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

# All cases, single pass
python cpp/eval/eval.py --case all --model claude-sonnet-4-6

# Single case
python cpp/eval/eval.py --case cases/00-comprehensive --model claude-sonnet-4-6

# Consistency measurement (3 passes per case)
python cpp/eval/eval.py --case all --model claude-sonnet-4-6 --runs 3
```

Results are written to `results/run-log.md` (committed) and
`results/<timestamp>-<case>.output.json` (gitignored).

### Manual run

1. Open a chat session with a Claude model that has access to this repository.
2. Use this prompt (substituting the case path):

```
Review the files in cpp-review/self-test/cases/00-comprehensive/ using cpp-review.
When done, compare your findings against expected.yaml in the same directory and
emit a PASS/FAIL table: one row per must-fire entry (caught?) and one row per
must-not-fire entry (correctly suppressed?).
```

3. Record results in `results/run-log.md` manually.

## Token cost estimate

| Component | Approximate tokens |
| --- | --- |
| `cpp-review/SKILL.md` | ~11,000 |
| 4 reference files (`cpp/references/`) | ~15,000 |
| Test case input files (all 3 cases) | ~1,500 |
| **Total input context** | **~27,500** |
| Review output (all 3 cases) | ~2,000--4,000 |

At Sonnet 4.6 rates (May 2026): ~$0.04--$0.07 per complete run of all three cases.

## Results

See [`results/run-log.md`](results/run-log.md) for the full run history.
Release tags are gated on ≥ 80% recall across all cases.
