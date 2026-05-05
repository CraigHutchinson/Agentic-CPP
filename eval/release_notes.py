#!/usr/bin/env python3
"""Generate release notes delta table from run-log.md.

Reads the current and previous run-log rows, computes token and cost deltas,
and outputs markdown to stdout + GitHub Actions GITHUB_OUTPUT.

Usage (local):
    python eval/release_notes.py --prev-tag v0.1.0 --model claude-sonnet-4-6

Usage (CI -- called by self-test.yml release job):
    PREV=$(git describe --abbrev=0 HEAD~1 2>/dev/null || echo "")
    python eval/release_notes.py --prev-tag "$PREV" --model claude-sonnet-4-6
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
RUN_LOG = REPO_ROOT / "cpp-review" / "self-test" / "results" / "run-log.md"


def parse_run_log(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or "---" in line or line.startswith("| Date"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 9:
            continue
        rows.append({
            "date":    cells[0],
            "model":   cells[1],
            "case":    cells[2],
            "recall":  cells[3],
            "noise":   cells[4],
            "in_tok":  cells[5],
            "out_tok": cells[6],
            "cost":    cells[7],
            "pass":    cells[8],
        })
    return rows


def tag_date(tag: str) -> str | None:
    if not tag:
        return None
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%ci", tag],
            capture_output=True, text=True, check=True,
        )
        return r.stdout.strip()[:10]
    except subprocess.CalledProcessError:
        return None


def parse_tok(s: str) -> int:
    return int(s.replace(",", "")) if s.replace(",", "").isdigit() else 0


def parse_cost(s: str) -> float:
    try:
        return float(s.lstrip("$"))
    except ValueError:
        return 0.0


def agg(rows: list[dict]) -> dict | None:
    if not rows:
        return None
    in_toks = [parse_tok(r["in_tok"]) for r in rows]
    out_toks = [parse_tok(r["out_tok"]) for r in rows]
    costs = [parse_cost(r["cost"]) for r in rows]
    # Use the last row's recall/noise as representative (final run of a batch)
    return {
        "recall": rows[-1]["recall"],
        "noise":  rows[-1]["noise"],
        "in_tok": sum(in_toks),
        "out_tok": sum(out_toks),
        "cost":   sum(costs),
    }


def tok_delta(a: int, b: int) -> str:
    d = b - a
    pct = d / a * 100 if a else 0
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:,} ({sign}{pct:.1f}%)"


def build_notes(current: dict | None, prev: dict | None,
                model: str, cur_ver: str, prev_ver: str) -> str:
    lines = ["## Self-test results", ""]
    lines.append(f"Evaluated with: `{model}` (skill version: {cur_ver})")
    lines.append("")

    if current and prev:
        lines += [
            f"| Metric | {prev_ver} | {cur_ver} | Delta |",
            "| --- | --- | --- | --- |",
            f"| Recall | {prev['recall']} | {current['recall']} | -- |",
            f"| Noise ratio | {prev['noise']} | {current['noise']} | -- |",
            f"| Input tokens | {prev['in_tok']:,} | {current['in_tok']:,} | {tok_delta(prev['in_tok'], current['in_tok'])} |",
            f"| Output tokens | {prev['out_tok']:,} | {current['out_tok']:,} | {tok_delta(prev['out_tok'], current['out_tok'])} |",
            f"| Cost per run | ${prev['cost']:.4f} | ${current['cost']:.4f} | -- |",
        ]
    elif current:
        lines += [
            f"| Metric | {cur_ver} |",
            "| --- | --- |",
            f"| Recall | {current['recall']} |",
            f"| Noise ratio | {current['noise']} |",
            f"| Input tokens | {current['in_tok']:,} |",
            f"| Output tokens | {current['out_tok']:,} |",
            f"| Cost per run | ${current['cost']:.4f} |",
        ]
    else:
        lines.append("No run-log data found.")

    lines += ["", "Raw results attached as release assets."]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prev-tag", default="")
    parser.add_argument("--model", default="claude-sonnet-4-6")
    args = parser.parse_args()

    all_rows = parse_run_log(RUN_LOG)

    # Current: last N rows where N = number of cases (up to 3)
    n_cases = 3
    current_rows = all_rows[-n_cases:] if len(all_rows) >= n_cases else all_rows

    prev_rows: list[dict] = []
    if args.prev_tag:
        cutoff = tag_date(args.prev_tag)
        if cutoff:
            prev_rows = [r for r in all_rows if r["date"] <= cutoff][-n_cases:]

    cur_ver = os.environ.get("GITHUB_REF_NAME", "current")
    prev_ver = args.prev_tag or "previous"

    body = build_notes(agg(current_rows), agg(prev_rows), args.model, cur_ver, prev_ver)
    print(body)

    gh_output = os.environ.get("GITHUB_OUTPUT", "")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as fh:
            fh.write(f"body<<EOF\n{body}\nEOF\n")


if __name__ == "__main__":
    main()
