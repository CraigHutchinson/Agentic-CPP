# Case 03: STYLE category, Sub0 profile

Tests the **STYLE category** of `cpp-review/SKILL.md` and the Sub0 profile
(`cpp/sub0-references/sub0-profile.md`). Unlike cases 00-02 this case needs the
profile in context, so `expected.yaml` carries a top-level `profile: sub0`; the
harness (`cpp/eval/eval.py`) then loads the selection rule and the profile and
tells the reviewer the project declares `style-profile: sub0`.

## Setup

One header, `input.hpp`, for a Sub0Pipeline-style library. It is otherwise clean:
docblocks, `[[nodiscard]]`, `noexcept`, ownership and thread-safety notes. The
design layers (L0-L3) should have little to say; the point is the STYLE section.

## Defect map

| ID | Defect | Location | Rule | Tier |
| --- | --- | --- | --- | --- |
| S1 | Named include guard `SUB0PIPELINE_JOB_QUEUE_HPP` | top and bottom | S05 pragma-once | STYLE/SHOULD |
| S2 | `<sub0pipeline/job.hpp>` (own header in angle brackets) and `"types.hpp"` (bare relative) | includes | S04 include-style | STYLE/SHOULD |
| S3 | `@brief` on the `JobQueue` docblock | class docblock | S03 autobrief | STYLE/SHOULD |
| S4 | `push_job` is snake_case on a public method | `JobQueue` | S01 method-case | STYLE/SHOULD |
| S5 | Plain `//` comment on public `empty()` | `empty()` | S02 doxygen-interfaces | STYLE/SHOULD |
| S6 | `m_count` member prefix | private section | S12 member-names | STYLE/SHOULD |

## Must-not-fire

1. `request_stop`, `begin`, `end`, `size` and `swap` are standard-protocol names.
   `request_stop` is documented as mirroring `std::stop_source`. S01 exempts them;
   the reviewer may list them as "exempt, verify" but must not ask for renames.
2. `kIdle` / `kBusy` are enumerators under open item O1 (constants and
   enumerators). A `[STYLE / QUESTION]` entry is correct; a finding asking for
   a rename is not.

## Pass criterion

At least five of the six defects caught (recall >= 0.80) and neither must-not-fire
phrase appears. Style findings should be tallied per rule, so one numbered
`[STYLE / ...]` entry per rule is expected, not one per occurrence (S4 and S6 are
single occurrences here; S2 is two occurrences and should appear as one entry).

Not run in this change: the harness needs an API key. The files were checked only
for shape against cases 00-02.
