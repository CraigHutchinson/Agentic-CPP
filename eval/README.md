# cpp-review evaluation harness

Two scripts for testing the `cpp-review` skill and generating versioned release notes.

## Setup

```sh
pip install -r eval/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## `eval.py` -- run self-tests

```sh
# All cases, single pass
python eval/eval.py --case all --model claude-sonnet-4-6

# Single case
python eval/eval.py --case cases/00-comprehensive --model claude-sonnet-4-6

# Consistency measurement (3 independent passes per case)
python eval/eval.py --case all --model claude-sonnet-4-6 --runs 3
```

Exit codes: `0` all cases pass, `1` one or more fail.

Results are appended to `cpp-review/self-test/results/run-log.md`.
Per-run JSON is written to `cpp-review/self-test/results/<timestamp>-<case>.output.json`
(gitignored).

### How scoring works

Each `expected.yaml` defines:

- **`must_fire`**: findings that must appear in the review output.
  Each entry has a `keywords` list and a `match` rule (`any_N` or `all_N`).
  A finding is "caught" if any extracted finding line contains enough keywords.
- **`must_not_fire`**: findings that must be suppressed.
  The case fails if the review output triggers any of these.
- **`thresholds`**: `min_recall` (default 0.80) and `max_noise_ratio` (default 0.35).

Recall = caught / total_expected.
Noise ratio = unexpected findings / total findings.

## `release_notes.py` -- generate release delta table

Used by `.github/workflows/self-test.yml` during the release job.

```sh
# Compute delta vs. a previous tag
python eval/release_notes.py --prev-tag v0.1.0 --model claude-sonnet-4-6
```

Outputs a markdown table to stdout and writes `body` to `GITHUB_OUTPUT` when
the env var is set (CI mode).

## Adding a new test case

1. Create `cpp-review/self-test/cases/<NN-name>/`.
2. Add one or more C++ input files (`.h`, `.cpp`).
3. Write `expected.yaml` with `must_fire`, `must_not_fire`, and `thresholds`.
4. Write `notes.md` explaining each defect and the pass criterion.
5. Run `python eval/eval.py --case cases/<NN-name>` to verify.
