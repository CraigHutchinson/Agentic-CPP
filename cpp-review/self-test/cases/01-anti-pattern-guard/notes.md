# Case 01: Anti-pattern guard (input-source suppression)

Tests that the reviewer correctly applies the **input-source check** from
`cpp-review/SKILL.md` Pre-finding context load, step 10.

## Setup

`FindCommand` has API documentation saying both `mappings` and `name` may be null.
The call site `DispatchCommand` passes:

- `kMappings` -- a `static const` array; cannot be null.
- `cmd` -- the function's own parameter, passed directly without modification.

## Expected reviewer behaviour

The reviewer must **not** raise a finding like:

> "The API says `mappings` may be null; add a null check at the call site."

The input-source check from SKILL.md suppresses it: the call site authors both
inputs inline and cannot trigger the null path.

The reviewer should note the suppression in a "Findings deliberately not raised"
section (or equivalent).

## Pass criterion

The case PASSES if:

1. No MUST or SHOULD finding is raised about null-guarding `kMappings` or `cmd`
   at the `FindCommand` call site.
2. The "Findings deliberately not raised" section (or equivalent) mentions the
   input-source check as the reason for suppression.

The case FAILS if the reviewer raises a null-guard finding as MUST or SHOULD.
