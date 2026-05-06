#!/usr/bin/env python3
"""cpp-review self-test evaluation harness.

Loads the cpp-review skill and reference files, calls the Claude API with each
test case, scores findings against the YAML oracle, and records token usage.

Usage:
    python cpp/eval/eval.py --case all --model claude-sonnet-4-6
    python cpp/eval/eval.py --case cases/00-comprehensive --model claude-sonnet-4-6
    python cpp/eval/eval.py --case all --model claude-sonnet-4-6 --runs 3
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent.parent
SKILL_ROOT = REPO_ROOT / "cpp-review"
REFS_DIR = REPO_ROOT / "cpp" / "references"
SELF_TEST_DIR = SKILL_ROOT / "self-test"
CASES_DIR = SELF_TEST_DIR / "cases"
RESULTS_DIR = SELF_TEST_DIR / "results"

REFERENCE_FILES = [
    REFS_DIR / "cpp-anti-patterns.md",
    REFS_DIR / "cpp-commenting.md",
    REFS_DIR / "cpp-idioms.md",
    REFS_DIR / "cpp-modernisation.md",
]

INPUT_EXTENSIONS = {".h", ".hpp", ".cpp", ".c", ".cc"}

# Approximate USD cost per million tokens (Sonnet 4.6, May 2026).
PRICE_PER_1M_INPUT = 3.00
PRICE_PER_1M_OUTPUT = 15.00


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    parts = [(SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")]
    for ref in REFERENCE_FILES:
        if ref.exists():
            parts.append(f"\n\n---\n# {ref.name}\n\n{ref.read_text(encoding='utf-8')}")
    return "\n".join(parts)


def load_case_inputs(case_dir: Path) -> str:
    files = sorted(p for p in case_dir.iterdir() if p.suffix in INPUT_EXTENSIONS)
    if not files:
        raise FileNotFoundError(f"No input files found in {case_dir}")
    parts = []
    for f in files:
        parts.append(f"### {f.name}\n\n```cpp\n{f.read_text(encoding='utf-8').rstrip()}\n```")
    return "\n\n".join(parts)


def load_oracle(case_dir: Path) -> dict:
    oracle_path = case_dir / "expected.yaml"
    with oracle_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def extract_findings(response_text: str) -> list[dict]:
    """Extract structured findings from a review response.

    The skill emits findings in one of several markdown formats depending on
    model version and temperature:
      **1.** [MUST] body...          (bold number, plain tier)
      1. **[MUST]** body...          (plain number, bold tier)
      **1.** `[MUST]` body...        (bold number, backtick tier)
      1. `[MUST]` body...            (plain number, backtick tier)
      1. [MUST] body...              (plain, no decoration)
    Also handles compound tiers: [MUST / L0-ESCALATION-STOP].
    """
    findings = []
    # [`*] matches either a backtick or an asterisk (decoration characters).
    pattern = re.compile(
        r"^\*{0,2}\d+\.\*{0,2}\s+[`*]{0,2}\[(?P<tier>[A-Z][A-Z0-9\s/\-]*)\][`*]{0,2}\s+(?P<body>.+)$",
        re.MULTILINE,
    )
    for m in pattern.finditer(response_text):
        tier_raw = m.group("tier").strip()
        tier = tier_raw.split("/")[0].strip()
        findings.append({"tier": tier, "raw": m.group(0), "body": m.group("body")})
    return findings


def match_keywords(text: str, entry: dict) -> bool:
    """Return True when text satisfies the keyword rule in an oracle entry."""
    keywords = entry.get("keywords", [])
    match_rule = entry.get("match", "any_1")
    text_lower = text.lower()
    matched = sum(1 for k in keywords if k.lower() in text_lower)
    if match_rule.startswith("any_"):
        required = int(match_rule.split("_")[1])
        return matched >= required
    if match_rule.startswith("all_"):
        return matched == len(keywords)
    return matched >= 1


def score_case(findings: list[dict], oracle: dict) -> dict:
    must_fire = oracle.get("must_fire", [])
    must_not_fire = oracle.get("must_not_fire", [])

    combined_text = " ".join(f["raw"] for f in findings)

    fire_results = []
    for entry in must_fire:
        caught = match_keywords(combined_text, entry)
        fire_results.append({"id": entry["id"], "signal": entry["signal"], "caught": caught})

    suppress_results = []
    for entry in must_not_fire:
        fired = match_keywords(combined_text, entry)
        suppress_results.append({"signal": entry["signal"], "fired": fired, "passed": not fired})

    total_expected = len(must_fire)
    caught_count = sum(1 for r in fire_results if r["caught"])
    recall = caught_count / total_expected if total_expected > 0 else 1.0

    false_positives = sum(
        1 for f in findings
        if not any(match_keywords(f["raw"], e) for e in must_fire)
    )
    total_findings = len(findings)
    noise_ratio = false_positives / total_findings if total_findings > 0 else 0.0

    suppress_passed = all(r["passed"] for r in suppress_results)

    return {
        "recall": recall,
        "noise_ratio": noise_ratio,
        "caught": caught_count,
        "total_expected": total_expected,
        "false_positives": false_positives,
        "total_findings": total_findings,
        "suppress_passed": suppress_passed,
        "fire_results": fire_results,
        "suppress_results": suppress_results,
    }


# ---------------------------------------------------------------------------
# API call and result packaging
# ---------------------------------------------------------------------------

def run_case(case_dir: Path, system_prompt: str, model: str,
             client: anthropic.Anthropic) -> dict:
    oracle = load_oracle(case_dir)
    case_input = load_case_inputs(case_dir)
    user_message = (
        f"Review the following C++ files.\n\n{case_input}\n\n"
        "Produce a numbered findings list following the format in your skill instructions."
    )

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = response.content[0].text
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = (
        input_tokens / 1_000_000 * PRICE_PER_1M_INPUT
        + output_tokens / 1_000_000 * PRICE_PER_1M_OUTPUT
    )

    findings = extract_findings(response_text)
    score = score_case(findings, oracle)

    thresholds = oracle.get("thresholds", {})
    min_recall = thresholds.get("min_recall", 0.80)
    max_noise = thresholds.get("max_noise_ratio", 0.35)

    passed = (
        score["recall"] >= min_recall
        and score["noise_ratio"] <= max_noise
        and score["suppress_passed"]
    )

    return {
        "case": case_dir.name,
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost, 5),
        "recall": round(score["recall"], 3),
        "noise_ratio": round(score["noise_ratio"], 3),
        "caught": score["caught"],
        "total_expected": score["total_expected"],
        "false_positives": score["false_positives"],
        "total_findings": score["total_findings"],
        "suppress_passed": score["suppress_passed"],
        "passed": passed,
        "fire_results": score["fire_results"],
        "suppress_results": score["suppress_results"],
        "response": response_text,
    }


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def append_run_log(result: dict) -> None:
    log_path = RESULTS_DIR / "run-log.md"
    if not log_path.exists():
        log_path.write_text(
            "# cpp-review self-test run log\n\n"
            "Formula: context ≈ SKILL.md (~11k) + 4 refs (~15k) + case files (~1.5k)\n\n"
            "| Date | Model | Case | Recall | Noise | In-tok | Out-tok | Cost | Pass |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n",
            encoding="utf-8",
        )
    ts = result["timestamp"][:10]
    row = (
        f"| {ts} | {result['model']} | {result['case']} "
        f"| {result['caught']}/{result['total_expected']} ({result['recall']:.0%}) "
        f"| {result['noise_ratio']:.0%} "
        f"| {result['input_tokens']:,} "
        f"| {result['output_tokens']:,} "
        f"| ${result['cost_usd']:.4f} "
        f"| {'PASS' if result['passed'] else 'FAIL'} |\n"
    )
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(row)


def save_output(result: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = result["timestamp"][:19].replace(":", "-")
    stem = f"{ts}-{result['case']}"
    out_path = RESULTS_DIR / f"{stem}.output.json"
    summary = {k: v for k, v in result.items() if k != "response"}
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    response_path = RESULTS_DIR / f"{stem}.response.txt"
    response_path.write_text(result.get("response", ""), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Console output
# ---------------------------------------------------------------------------

def print_summary(result: dict) -> None:
    status = "PASS" if result["passed"] else "FAIL"
    print(f"\n{'=' * 60}")
    print(f"Case: {result['case']}  [{status}]")
    print(f"  Recall:    {result['caught']}/{result['total_expected']} ({result['recall']:.0%})")
    print(f"  Noise:     {result['noise_ratio']:.0%}  ({result['false_positives']} unexpected)")
    print(f"  Tokens:    {result['input_tokens']:,} in / {result['output_tokens']:,} out")
    print(f"  Cost:      ${result['cost_usd']:.4f}")
    print(f"  Suppress:  {'OK' if result['suppress_passed'] else 'FAILED'}")
    for r in result["fire_results"]:
        icon = "+" if r["caught"] else "-"
        print(f"    [{icon}] {r['id']}: {r['signal']}")
    for r in result["suppress_results"]:
        icon = "+" if r["passed"] else "- FIRED (should be suppressed)"
        print(f"    [{icon}] suppress: {r['signal']}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="cpp-review self-test harness")
    parser.add_argument("--case", default="all",
                        help="Case directory name, path, or 'all'")
    parser.add_argument("--model", default="claude-sonnet-4-6")
    parser.add_argument("--runs", type=int, default=1,
                        help="Independent passes per case (>1 measures consistency)")
    args = parser.parse_args()

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    print("Loading system prompt...")
    system_prompt = load_system_prompt()

    if args.case == "all":
        cases = sorted(p for p in CASES_DIR.iterdir() if p.is_dir())
    else:
        candidate = Path(args.case)
        cases = [CASES_DIR / candidate.name if not candidate.is_absolute() else candidate]

    if not cases:
        print("ERROR: no cases found", file=sys.stderr)
        sys.exit(1)

    all_passed = True
    for case_dir in cases:
        if not case_dir.exists():
            print(f"ERROR: case directory not found: {case_dir}", file=sys.stderr)
            sys.exit(1)
        for run_idx in range(args.runs):
            label = f" (run {run_idx + 1}/{args.runs})" if args.runs > 1 else ""
            print(f"\nRunning {case_dir.name}{label}...")
            result = run_case(case_dir, system_prompt, args.model, client)
            print_summary(result)
            out_path = save_output(result)
            append_run_log(result)
            print(f"  Output: {out_path}")
            if not result["passed"]:
                all_passed = False

    print(f"\n{'=' * 60}")
    print(f"Overall: {'PASS' if all_passed else 'FAIL'}")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
