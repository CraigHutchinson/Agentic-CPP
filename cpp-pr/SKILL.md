---
name: cpp-pr
description: Slack message author for PR work -- "PR" doubles as **p**ull-**r**equest and **p**ublic-**r**elations. Use when the user asks for a Slack post, DM, channel announcement, status update, review request, or merged/landed celebration about a PR, a PR stack/chain, or related engineering work that ends up in Slack rather than in GitHub. Produces Slack-mrkdwn-correct copy in a fenced text block ready to paste verbatim -- never GitHub-flavoured markdown. Audience-aware: defaults to channel-tone wording unless DM is specified.
allowed-tools: Read, Glob, Grep, Bash
---

# C++ PR -- Slack messages for pull-requests / public-relations

Companion to `cpp-write` and `cpp-review`. Where those two land the code, this one lands the **message about the code** -- in Slack, where the syntax is different and the audience is broader than a PR reviewer.

## When to invoke

Invoke when the user asks for any of:

- A Slack post announcing a new PR or PR stack/chain.
- A DM to a reviewer asking for eyes.
- A merged-PR celebration / handoff message.
- A status update on stack progress.
- Any team-facing copy where the output lands in Slack, **not** in a GitHub PR body / README / commit message.

If the destination is a GitHub PR body, README, or commit message, this skill does **not** apply -- those use GitHub-flavoured markdown and a different tone. Use the standard PR-body conventions instead.

## Critical -- Slack does not parse GitHub markdown

Slack uses its own flavour called **mrkdwn**. Pasting GitHub markdown directly produces literal `**` / `[text](url)` / `# heading` text on screen unless the user's workspace has the optional "format messages with markup" preference enabled. Workspaces with that preference disabled (a common default) show the raw characters -- exactly the failure mode this skill exists to prevent.

| You want | GitHub markdown | Slack mrkdwn |
|---|---|---|
| Bold | `**bold**` | `*bold*` |
| Italic | `*italic*` or `_italic_` | `_italic_` |
| Strikethrough | `~~strike~~` | `~strike~` |
| Inline code | `` `code` `` | `` `code` `` (same) |
| Code block | ```` ```lang ```` | ```` ``` ```` (no language tag) |
| Block quote | `> line` | `> line` (same) |
| Link with text | `[text](url)` | `<url\|text>` |
| Bare link | `<url>` or `url` | `<url>` or bare URL |
| Heading | `# H1` | none -- use `*BOLD LINE*` and a blank line |
| Bullet list | `- item` | `• item` or `- item` (Slack does not auto-format consistently across workspaces; literal `•` is safest) |
| Numbered list | `1. item` | `1. item` literal -- Slack does **not** auto-renumber |
| User mention | n/a | `<@U12345>` (use the Slack ID, not display name) |
| Channel mention | n/a | `<#C12345\|channel-name>` |
| Broadcast | n/a | `<!here>` / `<!channel>` -- use sparingly |

Notes:
- Inline `<url|text>` and the literal pipe `|` separator are required. Without the `|`, Slack renders the visible URL verbatim.
- Slack's GitHub Enterprise app may unfurl PR links into rich cards. That is usually desirable for PR announcements; the `<url|short-text>` form keeps the inline text compact while the unfurl card does the heavy lifting.

## Output shape -- copy-paste-ready

**Always** deliver the message inside a fenced text block:

````text
<the Slack message body, with mrkdwn syntax, verbatim>
````

This protects the literal `*bold*` / `<url|text>` characters from being re-rendered by the assistant's own markdown layer before reaching the user. The user copies the fence body verbatim into Slack.

Never deliver Slack copy as inline prose in the assistant's response -- the `*` characters get consumed by the rendering layer and the user sees a misleading preview.

## Audience-aware defaults

Slack messages live on a tone spectrum from **team channel announcement** (broadest, most context-establishing) to **direct message to one colleague** (warmest, most assumes shared context). Pick the channel default unless the user specifies otherwise.

| Dimension | Channel default | DM default |
|---|---|---|
| Opener | `Hey team` / `Heya` (workspace-neutral) | `Heya <Name>` / `Hi <Name>` |
| Audience presumption | Few have context -- restate the work | Recipient has some context -- skip the long preamble |
| Length | Up to ~12 lines is fine | Aim for ≤ 6 lines |
| @mention | Avoid `<!here>` / `<!channel>` unless time-critical | Direct mention of recipient is fine |
| Sign-off | "Thanks!" / generic | "Cheers" / first-person warm |
| Emoji density | 1-2 across the whole post | Up to 3, slightly playful is fine |

When unsure, use audience-agnostic wording -- the opener "Heya" reads naturally in both channel and DM. "Hey team" is channel-only.

## Emoji vocabulary

Slack inline emoji uses `:name:` syntax. The vocabulary below is the standard set that ships in every Slack workspace; custom workspace emojis (`:pr:`, `:gh-pr:`, `:eng-team:`, etc.) are not standard -- use them only when the user has confirmed they exist.

| Use | Standard emoji | Notes |
|---|---|---|
| "Please review" gentle ask | `:pray:` 🙏 | Friendly nudge, not subservient |
| "Eyes please" | `:eyes:` 👀 | Standard PR-review shorthand |
| Merged / landed | `:white_check_mark:` ✅ | Land/merge confirmation |
| Shipped / released | `:rocket:` 🚀 | After merge to trunk |
| Celebration / milestone | `:tada:` 🎉 | Stack landed, epic closed |
| Coffee / casual chat | `:coffee:` ☕ | "Happy to chat on a call" |
| Wave | `:wave:` 👋 | DM opener |
| Heads-up | `:bulb:` 💡 | Surfacing a finding / suggestion |
| Build / in-flight | `:construction:` 🚧 | Draft / WIP / blocked |
| New work | `:sparkles:` ✨ | New feature / module |
| Question | `:question:` ❓ | Asking for input |
| Blocker / urgent | `:warning:` ⚠️ | Stalled PR, needs immediate action |
| Blocked / waiting | `:hourglass:` ⏳ | Waiting on external dependency or approval |
| Test/CI failure | `:x:` ❌ | Build broken, tests failing |
| Collaboration / pairing | `:handshake:` 🤝 | Co-authored or cross-team review |
| Discussion / feedback | `:speech_balloon:` 💬 | Consolidating review feedback, design discussion |

**Custom emoji handling.** If the user mentions a custom workspace emoji exists (e.g. "`:pr:` for the PR icon"), you may use it. If you have not been told it exists, do not guess -- a `:pr:` that the workspace lacks renders as literal `:pr:` text, which is uglier than no emoji at all.

**Density rule.** 1-2 emojis per message is friendly. 3+ becomes noise. Status-line emojis in a bullet list (e.g. one `:white_check_mark:` per landed-PR row) don't count against this -- they're functional, not decorative.

## Synopsis line shape

Each PR line follows the same compact shape:

```
*<short title>* — <what it adds>; <what it unlocks or replaces, when non-obvious>. <url|#NNNNNN>
```

Constraints:
- **Title** is short and human-readable. No PR-number prefix -- the link carries that. Bold via `*...*`.
- **Synopsis** is ≤ 15 words. Two clauses max, em-dash or semicolon separator.
- **Inline code** spans for symbol names (`Class<T>`, `kEnumValue`, `argv-flag`).
- **Link** at the end: `<url|#NNNNNN>` (visible text = the PR number, the link itself is the full URL).
- **No implementation detail** that needs the diff to follow -- mention only what a reader who has not opened the PR needs to decide whether to click.

## Templates

### Template 1 -- PR stack / chain announcement (channel)

````text
Heya :pray: the <epic / topic> stack is ready for eyes whenever you have a moment.

<N> PRs, each sized for a single sitting. Easiest in order, base → consumer:

1. *<PR-1 title>* — <one-line synopsis>. <https://.../pull/<N1>|#<N1>>
2. *<PR-2 title>* — <one-line synopsis>. <https://.../pull/<N2>|#<N2>>
3. *<PR-3 title>* — <one-line synopsis>. <https://.../pull/<N3>|#<N3>>
...

Bite-sized by design, no rush.

Happy to walk through any of them on a call if it helps :coffee:
````

### Template 2 -- Single PR review request (channel or DM)

````text
<opener> -- small PR up if you've got 15 minutes: *<title>* <https://.../pull/<N>|#<N>>

<2-line synopsis: what / why>

No rush.
````

### Template 3 -- Merged / shipped (channel)

````text
:white_check_mark: *<title>* just landed -- <one-line "what it unlocks">. <https://.../pull/<N>|#<N>>

Thanks to <reviewers> for the review!
````

### Template 4 -- Stack progress / status (channel)

````text
Quick update on the <epic> stack:

:white_check_mark: *<PR-1 title>* — landed. <url|#N1>
:eyes: *<PR-2 title>* — in review. <url|#N2>
:construction: *<PR-3 title>* — draft, blocked on <thing>. <url|#N3>

Next milestone: <one-line>.
````

### Template 5 -- DM review ask (warmer)

````text
Heya :wave: got a small PR up: *<title>* <https://.../pull/<N>|#<N>>

<two-line synopsis>

No rush -- just thought you'd be the right pair of eyes given <reason>.
````

### Template 6 -- Blocked / help needed (channel)

````text
:warning: *<title>* is blocked -- <reason>. <https://.../pull/<N>|#<N>>

<details: what decision or input is needed>

Pinging <@person> for visibility / decision. Thanks!
````

Use this when a PR is stalled due to an external blocker, design decision, or dependency. Keep the reason concise; the GitHub unfurl will provide detail. If waiting for a specific person, mention them directly rather than using `<!channel>`.

### Template 7 -- Post-merge follow-up (channel)

````text
:white_check_mark: *<title>* landed. <https://.../pull/<N>|#<N>>

*Next steps:*
• <migration guide / deprecation notice / docs to update>
• <follow-up PR or ticket link if applicable>
• <timeline / deadline if applicable>

See the PR for detailed context.
````

Use this when a merge introduces new tooling, a breaking change, a deprecation, or a multi-phase migration. Gives the team a clear handoff and prevents parallel duplicate work.

### Template 8 -- Feedback consolidated, ready to merge (channel or DM)

````text
:speech_balloon: *<title>* -- addressed all feedback, ready to go. <https://.../pull/<N>|#<N>>

Changes in latest commit:
• <change 1>
• <change 2>

<mention original reviewer if DM, or "thanks to reviewers" if channel>
````

Use this when review comments have been incorporated and you're signalling that re-review is not needed (or only spot-check is needed). Keeps momentum in the review cycle.

### Template 9 -- Large / complex PR with extra context (channel)

````text
:eyes: *<title>* is up for review -- heads-up that this one is chunky. <https://.../pull/<N>|#<N>>

_Why it's large:_ <one-line explanation of scope>

_Suggested review order:_
1. <commit 1 or file 1> — <why this first>
2. <commit 2 or file 2> — <why this second>

*Key decision points:* <design choice 1>, <design choice 2>. Happy to walk through async or on a call if that helps.

No rush, but flagging it up-front so the scope doesn't surprise you.
````

Use this sparingly -- only for PRs that are genuinely too large to review in one sitting. Provide a suggested review order and call out the design decisions that shaped the size. Offer call-based walkthrough to reduce review friction.

## Gathering accurate PR data

Before composing, verify PR numbers, titles, base branches, and statuses against GitHub. Do not paraphrase from memory -- a wrong PR number in a Slack post is embarrassing and hard to retract.

For a stack rooted in the current branch:

```bash
# List the user's open PRs in the target repo with extended status
gh pr list --repo <owner>/<repo> --author "@me" --state open \
  --json number,title,headRefName,baseRefName,isDraft,url,createdAt,statusCheckRollup,reviewDecision \
  --limit 20

# Inspect one PR's full details including CI status and reviews
gh pr view <N> --repo <owner>/<repo> \
  --json number,title,headRefName,baseRefName,isDraft,url,body,statusCheckRollup,reviewDecision,reviews

# Quick CI status check for a PR
gh pr checks <N> --repo <owner>/<repo>
```

Key fields for Slack messaging:
- **`isDraft`**: Draft status (`:construction:` emoji if true, `:eyes:` if false and in-review).
- **`statusCheckRollup`**: CI/test status. States: `EXPECTED` (pending), `SUCCESS`, `FAILURE`, `PENDING`. Use `:x:` for `FAILURE`, `:hourglass:` for `PENDING`.
- **`reviewDecision`**: Review state. Values: `APPROVED`, `CHANGES_REQUESTED`, `REVIEW_REQUIRED`, `COMMENTED`. Helps determine if more eyes are needed.
- **`baseRefName`**: Base branch (e.g. `main`, `develop`, `release/2.0`). For stack reconstruction, walk the chain: PR-1 bases on repo default, PR-2 bases on PR-1's head, etc.

For a stack the user already named, walk the `baseRefName → headRefName` chain from each PR's JSON to reconstruct the order. Verify each PR's `isDraft` so the status-line emoji is accurate.

**Important:** Verify CI status before announcing "ready for review" in a stack announcement. If a PR shows `FAILURE` in `statusCheckRollup`, mention the blocker in Template 4 or Template 6 instead of the standard Templates 1-3.

If a PR's title contains conventional prefixes (`[EAD-NNNN]`, `feat:`, `fix:`, `cpp-17:`), strip them from the Slack title -- the link gives the PR number, and the Slack reader does not need the convention markers.

## Thread management and cross-team PRs

**When to post in-thread vs. top-level:**

| Scenario | Strategy |
|---|---|
| PR announcement in a dedicated channel | Top-level post. This is why it exists. |
| PR announcement in a shared team channel | Top-level post. Team members can ignore or follow-thread if interested. |
| Follow-up on existing PR thread (e.g., "status update" on a PR from yesterday) | Reply in-thread. Keeps the conversation localized. |
| Cross-team PR that needs visibility outside primary reviewer group | Top-level in a shared channel (e.g. `#architecture`, `#api-review`). Include a "context for those unfamiliar" preamble if the work spans teams. |
| One-off design discussion or decision point | Top-level in the relevant design channel. Reference the PR, don't bury it in a thread. |

**For cross-team or dependency PRs:**

Add a context block at the top before the PR line:

```
*Context for new-team folks:* <epic name> — <why this affects your team>. 

[Then the PR line or stack as usual.]
```

Example:

```
*Context:* EAD-2112 refactors the runtime parameter system. This touches the command-line argv parsing that the Tools team consumes.

[PR stack follows...]
```

This takes one line and prevents twelve "why does this matter to us?" questions downstream.

## C++-specific messaging considerations

**API-stability PRs** should note backward-compatibility explicitly:

```
*Breaking API change:* <Class>::<Method>() signature changed from <old> to <new>.
Affects: <list of known consumers>. Migration path in the PR.
```

**Large refactorings** deserve a post-merge migration guide (Template 7) rather than burying the API changes in PR description:

```
:white_check_mark: *Refactor: Lifetime ownership annotations on core::vector* landed.

*Migration:* Move from `vector<T*>` to `vector<core::unique_ptr<T>>` per [link]. 
Three team leads already on the change; happy to help with your module.
```

**Performance-critical PRs** benefit from a quick benchmark callout (without full numbers -- the PR has those):

```
*Perf win:* <N>ms shaved off Editor startup, replaces three allocations with one stack buffer per frame.
```

**Cleanup/modernization PRs** should acknowledge the "invisible work" explicitly in merge announcements:

```
:white_check_mark: Modernized Parser to C++17 — string_view, std::optional, auto
(Technical debt. No behavioral change; full test coverage retroactively added.)
```

This signals to non-C++ team members that it's "maintenance" not "feature", and prevents "why did we spend time on this?" discussions.


| # | Check | Pass criterion |
|---|---|---|
| 1 | Bold uses single asterisks | No `**...**` anywhere |
| 2 | Links use angle-bracket-pipe form | No `[text](url)` -- only `<url\|text>` or bare `<url>` |
| 3 | Numbered list items written literally | Each line starts with `1.` / `2.` / ... -- Slack does not renumber |
| 4 | Emoji density | ≤ 2 decorative emojis total (functional status-line emojis in a list are exempt) |
| 5 | Opener fits the audience | "team" / "everyone" for channel, name or "Heya" for DM |
| 6 | Length | Channel ≤ ~12 lines; DM ≤ ~6 lines |
| 7 | Closing line is non-pushy | "no rush" / "whenever you have time" / "happy to walk through" |
| 8 | Delivered inside a fenced text block | The message body sits inside ```` ```text ```` ... ```` ``` ```` |
| 9 | URLs are full `https://` | No relative paths, no `gh pr view <N>` shorthand |
| 10 | No GitHub-only features | No `<details>`, no relative file links, no check-status badges |
| 11 | Custom emojis confirmed | Only used when the user has stated they exist in the workspace |
| 12 | PR titles stripped of convention prefixes | No `[EAD-####]` / `feat:` / `fix:` in the Slack-visible title |

## Output protocol

1. **Confirm audience** -- channel vs DM. If unspecified, default to channel; note the default in your response.
2. **Confirm custom emojis** -- if the user has mentioned `:pr:` or similar, use it; otherwise stick to the standard set above.
3. **Gather PR data** via `gh pr list` / `gh pr view` -- verify numbers, titles, base branches, draft status. Skip if the user has already supplied the data inline.
4. **Pick the template**, fill the slots.
5. **Run the quality checklist** -- every line.
6. **Deliver inside a fenced text block.**
7. **Offer 1-2 tone-tuning toggles below the fence** (e.g. "swap `:pray:` for `:eyes:` if you want it less reverent"; "drop the call offer if the team is a different timezone"). Keep these short -- the message is the deliverable, the toggles are optional adjustments.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| `**bold**` in delivered message | Renders literally in workspaces without "format with markup" enabled | Use `*bold*` |
| `[#105207](https://...)` | GitHub markdown -- renders as literal text in Slack | Use `<https://...\|#105207>` |
| Pasting raw `https://...` URLs everywhere | Visually loud; consumes line space | Use `<url\|#N>` for compact rendering |
| Including PR review badges / `<details>` / file paths | GitHub-only rendering primitives | Strip; rely on the unfurl card or a brief synopsis |
| Three or more decorative emojis | Reads as performative, not friendly | Cap at 2; let prose carry the warmth |
| Heading syntax `# H1` / `## H2` | Renders as literal `#` characters | Use `*BOLD LINE*` + a blank line |
| Auto-numbered list reliance | Slack does not renumber on edit | Type the numbers literally; renumber by hand if you reorder |
| Hardcoded `<!channel>` for non-urgent posts | Pings everyone in the channel | Omit broadcast mentions unless the user explicitly asks |
| Forgetting the fenced text block | Assistant renders the `*` and the user sees the wrong preview | Always wrap output in ```` ```text ```` ... ```` ``` ```` |
| Announcing a large refactor without migration guide | Team scrambles to figure out how to consume the new API | Use Template 7 post-merge to provide migration path |
| Burying breaking-change info in a stack | Reviewers and downstream teams miss the incompatibility | Call it out in the opener: "*Breaking API change:* <Class>::<Method>" |
| Not mentioning which branch a PR targets | Readers assume main; PR lands on release branch or wrong team branch | Always include base branch in complex stacks, especially cross-team |
| Slack announcement with wrong PR number | Link points to the wrong work; causes confusion and retraction | Always verify `gh pr view <N>` output before pasting into Slack |
| Mixing emoji conventions (`:construction:` for both "in-flight" and "needs work") | Status ambiguity | Use `:construction:` for in-flight/draft, `:warning:` for needs-immediate-attention, `:x:` for failed CI |
| Announcing "ready for review" when CI is failing | Wastes reviewer time; looks careless | Check `gh pr checks <N>` or `statusCheckRollup` before posting |
| Generic "please review" with no synopsis | Reviewer has no signal whether to click | Always include 1-2 line synopsis of what the PR does |
| Long-term stalled PR not mentioned in status updates | Gives false impression that work is progressing | Template 4 should include draft/blocked PRs explicitly; don't hide stalled work |

## Common mistakes and lessons learned

**Mistake 1: Stack order confusion**

*Problem:* Announcing a 4-PR stack but listing them in the wrong base-to-consumer order. Reviewer opens PR #2, gets merge conflicts because PR #1 hasn't merged yet.

*Prevention:* Always run `gh pr view <N> --json baseRefName,headRefName` for each PR in order. Verify the chain: PR-1 bases on `main`, PR-2 bases on PR-1's branch, etc. Walk the chain before posting.

**Mistake 2: Stranded PRs in archived branches**

*Problem:* Announcing a PR against an old release branch without noting it. Team assumes it's going to trunk and waits for trunk merge; PR lands only on `release/1.8`.

*Prevention:* In Template 1 (stack announcement), if any PR bases on a non-trunk branch, note it: "PRs #1-3 against main; #4 against release/1.8 for backport."

**Mistake 3: Double-announcing the same PR**

*Problem:* Announcing a PR in two channels (e.g., team channel and #architecture channel). Reviewers cross-comment in both threads; feedback gets split.

*Prevention:* Choose one primary channel per PR. If it's important enough for two channels, post the primary in one and a brief "see #channel for discussion" link in the other.

**Mistake 4: Feedback consolidation without re-check**

*Problem:* Using Template 8 ("feedback consolidated, ready to merge") when the latest commit actually introduced new test failures.

*Prevention:* Before posting Template 8, verify `gh pr checks <N>` shows all checks passing. Never post "ready to merge" if CI is red.

**Mistake 5: Overly technical synopsis in channel posts**

*Problem:* "*Refactor: Move PImpl from template specialization to virtual inheritance*" in a general engineering channel. Non-C++ team members don't know why they should care.

*Prevention:* For channel announcements, lead with impact, not technique. "*Perf: Eliminated overhead in hot loop; Editor startup 5% faster.*" Then link to PR for technical details.

**Mistake 6: Forgetting that large PRs need a roadmap**

*Problem:* Announcing a 50-file refactor without suggesting a review order. Reviewer opens it, drowns, closes without reading.

*Prevention:* Use Template 9 for PRs that touch >15 files or >500 LOC of non-generated code. Provide a review order and point out the decision points that shaped the size.

**Lesson: Async clarity saves review time**

The best PR announcement is one that a reviewer can understand **without opening the PR**. Use the synopsis, the "why", and the target audience to decide what detail to include. The GitHub unfurl will provide the rest.

---

## Worked example

User asks: *"Slack post for the rule-engine PR chain -- ready for review, friendly tone, channel post."*

Skill flow:

1. Audience: channel (specified).
2. Custom emojis: none mentioned, use standard set.
3. Gather data: `gh pr list --author "@me" --json ...` -- find the four PRs in the chain.
4. Template: Template 1 (PR stack / chain announcement).
5. Fill slots with verified PR numbers, titles stripped of `[EAD-2112]` prefix.
6. Quality checklist passes.
7. Deliver:

````text
Heya :pray: the EAD-2112 BootConfig rule-engine stack is ready for eyes whenever you have a moment.

Four PRs, each sized for a single sitting. Easiest in order, base → consumer:

1. *BootConfig groundwork* — API surface docs, `ParameterRegistry`, `Parsed()` accessor. <https://github.cds.internal.unity3d.com/unity/unity/pull/105207|#105207>
2. *Token-to-Value Mappings* — `MappedParameter<T>` replaces parallel `(tokens[], values[])` arrays with one type-safe table. <https://github.cds.internal.unity3d.com/unity/unity/pull/105387|#105387>
3. *Multi-Value MappedParameter* — `Cardinality::Multi` for repeating keys; migrates `-forceFullStacktrace`. <https://github.cds.internal.unity3d.com/unity/unity/pull/105562|#105562>
4. *Rules framework* — `Condition` library + four rule kinds + `RuleRegistry`. <https://github.cds.internal.unity3d.com/unity/unity/pull/105556|#105556>

Bite-sized by design, no rush.

Happy to walk through any of them on a call if it helps :coffee:
````

Optional tone toggles offered after the fence:
- Swap `:pray:` for `:eyes:` if you want a more direct "review please" beat.
- Drop the trailing call-offer line if the channel is across timezones.
- Add `<!here>` at the top if it's time-critical (default omitted).
