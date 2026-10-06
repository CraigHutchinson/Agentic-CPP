# Style Profile and Org Overlay Selection

Shared C++ reference. Loaded by `cpp-review` (before any review pass), `cpp-write` (before writing any code), and `cpp-project-init` / `cpp-simplify` (wherever they say "org overlay"). **This file is the only place that defines how a project selects a style profile and an org overlay.** Skills refer to it; they do not restate it.

Two kinds of extension exist, and they answer different questions:

| Kind | Directory | Holds | Answers |
|---|---|---|---|
| **Style profile** | `../sub0-references/sub0-profile.md` (`../<name>-references/<name>-profile.md`) | Values for choices between acceptable alternatives: naming case, file extension, include style, comment notation, brace layout. | "Which of the acceptable forms does this house use?" |
| **Org overlay** | `../unity-references/` (`../<org>-references/*-{codebase,commenting,idioms,modernisation,reinvention}.md`) | Local knowledge: in-house utilities, module boundaries, type preferences. | "What exists here that the generic guidance cannot know about?" |

A directory `../<name>-references/` may hold either or both. The generic references in `../references/` state substance (correctness, safety, design) and a default for each style choice.

## Selection rule

Run once, at the start of a review or authoring session, from the root of the project under review.

1. **Explicit declaration (wins).** Search the project's `AGENTS.md`, `CLAUDE.md` and `STYLE_GUIDE.md` (repo root first, then the module directory of the code being touched) for these lines, each on its own line:

   ```text
   style-profile: <name>
   overlay: <name>
   ```

   `rg -n '^\s*(style-profile|overlay):\s*(\S+)' AGENTS.md CLAUDE.md STYLE_GUIDE.md`

   `style-profile: none` and `overlay: none` select nothing. A module-level declaration overrides the repo-root one for files under that module.
2. **Marker detection (fallback, only when step 1 found no `style-profile:` line).** A profile declares its own markers in its `## Selection markers` section. First match wins. For `sub0`: a `project(Sub0...)` in the root `CMakeLists.txt`, or an `include/sub0*` directory.
3. **Nothing applies.** Behaviour is exactly as before this file existed: only the generic references, plus the `unity-references` overlay if that directory exists.

**Resolving the overlay.** If a `style-profile:` was selected (declared or detected) and the project has no `overlay:` line, **no overlay is loaded**; this stops an unrelated machine-local overlay such as `unity-references` from steering a project that declared a different house. If no profile was selected, an overlay loads only if declared or, as before, if `../unity-references/` exists.

**Load order and precedence.** Generic references first, then the overlay's `*-{codebase,commenting,idioms,modernisation,reinvention}.md`, then the profile. On a style choice the profile wins over the generic default and over the overlay; on a substance rule the generic reference wins unless the profile rule is marked `[OVERRIDE]` and names it.

**Say what was selected.** The first line of any report or authored summary states `Style profile: <name> (declared in <file> | detected via <marker> | none)` and `Overlay: <name | none>`.

**Wording in the generic references.** Where a generic reference or skill says "if `../unity-references/` exists, load ..." it means "load the overlay selected by this file". Until the generic text is neutralised, the profile's `[OVERRIDE]` entries and its "Superseded generic guidance" list are what correct the unchanged examples.

## Profile schema

A profile is one Markdown file with a fixed shape so a reviewer can read it and a script can tally against it.

```text
# <Name> style profile
## Selection markers        <- how step 2 detects this profile
## Superseded generic guidance   <- list of generic rules/examples this profile overrides
## Report configuration     <- library-name placeholders, exemption lists
## Rules                    <- one block per rule, in the block format below
## Open items               <- same block format, status: open
```

Every rule is one `###` block with exactly these fields, in this order:

```text
### <ID> <short-name>
- **value:**       the decided form, one line
- **status:**      decided | provisional | open
- **why:**         one line
- **correct:**     example in this house's style
- **incorrect:**   example
- **detect:**      a ripgrep command, or "judgement"; then what a false positive looks like
- **severity:**    STYLE/SHOULD | STYLE/NICE | STYLE/CANDIDATE | STYLE/QUESTION
- **overrides:**   `[OVERRIDE]` + the generic rule (file > section) it replaces, or "none"
```

Meaning of the fields that drive reporting:

| Field | Effect |
|---|---|
| `status: decided` | Findings carry the rule's stated severity (`STYLE/SHOULD` or `STYLE/NICE`). Never MUST: style never gates the design layers. |
| `status: provisional` | The rule is an audit judgement whose definition is still being refined. Report candidates as `STYLE/CANDIDATE`, each with a one-line justification; never as a raw count. |
| `status: open` | Not a rule. Produce a question carrying the profile's stated preference; never a finding, never counted as a violation. |
| `detect: judgement` | Cannot be run mechanically; sample (see the audit mode in `cpp-review`) and report what was not read. |
| `overrides` | The generic rule is superseded for this profile. Do not raise the generic finding; raise the profile's rule instead. |

A rule's `detect` command may use `<lib>` / `<LIB>` placeholders; the profile's `## Report configuration` says how to fill them from the project.
