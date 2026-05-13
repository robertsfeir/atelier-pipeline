<protocol id="scout-fanout">

## Phase 2a: Scout Fan-Out

After the user approves the scan inventory, Eva fans out scout subagents in parallel. Each scout reads one category of artifact files and returns raw content in a named inline block. This keeps all file reading off the main thread and off Opus.

**Invocation pattern:** `Agent(subagent_type: "scout")`. Eva must use the Scout Invocation Template below when building the prompt — copy it verbatim and fill `{FILES}` with the Phase 1 file paths for that category. Facts only -- no extraction, no opinions. Each scout returns raw file content with clear delimiters per file. Per ADR-0048, the scout model pinning is owned by the scout frontmatter (`claude-haiku-4-5-20251001`); the `model` parameter is omitted from the invocation.

**Dedup rule:** Each file is read by exactly one scout. No file appears in more than one scout's file set.

### Scout Categories

| Scout | Files | Block element |
|-------|-------|---------------|
| **ADR scout** | `docs/architecture/ADR-*.md` or `docs/adrs/ADR-*.md` | `<adrs>` |
| **Specs scout** | `docs/product/*.md` | `<specs>` |
| **UX scout** | `docs/ux/*.md` | `<ux-docs>` |
| **Pipeline scout** | `error-patterns.md` + `context-brief.md` | `<pipeline-artifacts>` |
| **Git scout** | `git log` output -- filter for significant commits only; if no significant commits found, returns empty | `<git-history>` |

### Scout Content Format

Each scout returns content using file delimiters:

```
=== FILE: docs/architecture/ADR-0002-team-collaboration.md ===
[full file content]
=== END FILE ===

=== FILE: docs/architecture/ADR-0005-xml-prompt-structure.md ===
[full file content]
=== END FILE ===
```

The Sonnet subagent parses these delimiters to process each file individually against the extraction rules.

### Scout Invocation Template

Eva copies this template verbatim into every scout Agent call. Fill `{FILES}` with the Phase 1 file paths for the category being read (one path per line). Do not paraphrase or abbreviate any part of this template — the `=== FILE:` delimiter format in `<output>` is what the downstream synthesis/extractor agent and the `enforce-scout-swarm.sh` hook both require.

```
<task>Read the files listed in <read> below. Return the full content of every file exactly as-is. Do not summarize, paraphrase, or omit any part of any file. Do not add commentary, headings, or analysis. Raw file dumps only.</task>
<read>
{FILES}
</read>
<constraints>
- No prose, no summaries, no opinions.
- Every file in <read> must appear in output exactly once.
- Reproduce each file completely — no truncation.
</constraints>
<output>
For each file, output using this exact delimiter format:

=== FILE: {path} ===
[full file content]
=== END FILE ===

Repeat for every file in <read>.
</output>
```

The `{FILES}` placeholder is the exact file paths from Phase 1 inventory for this scout's category — one absolute or repo-relative path per line. Eva determines the file list from Phase 1 counts before fan-out.

### Skip Conditions

- **User excluded source type:** If the user narrowed scope (e.g., "only ADRs"), only the ADR scout fires. All other scouts are skipped.
- **Zero files in category:** If the Phase 1 scan found zero files for a category (e.g., no UX docs), that scout is skipped entirely. The Sonnet subagent skips that source type gracefully.
- **Scope-based exclusion:** If the user explicitly says "skip git history", the Git scout does not fire.

### File-Count Gate

If a single scout would read **more than 20 files**, split into multiple sub-scouts with **disjoint** (non-overlapping) file sets. Each file is assigned to exactly one sub-scout.

Example: 25 ADRs → ADR scout A (13 files) + ADR scout B (12 files). Split as evenly as possible; if the count is odd, the first sub-scout gets the larger half. Eva determines the split at fan-out time using Phase 1 inventory counts. The Sonnet subagent receives all sub-scout outputs concatenated in the same `<adrs>` element.

### Dry-Run Mode (Phase 2a)

In dry-run mode, scouts still fire normally so the user can preview what content would be extracted. Scout results are collected but not passed to a capture subagent.

### Scout Failure Handling

If a scout fails (timeout or error), Eva reports which category failed to the user. **No automatic re-invocation.** The user decides whether to proceed with partial content or abort. Consistent with retro lesson #004: hang-and-timeout failures are diagnostic information, not a trigger for re-invocation.

### Completeness Check (Gate Before Extraction)

Before invoking the Sonnet subagent, Eva verifies scout output completeness: the file count returned by each scout must match the Phase 1 inventory count for that category. If a mismatch is found, Eva reports the gap to the user before proceeding. Skipped scouts (per skip conditions above -- zero-file categories, user-excluded sources, or scope-based exclusions) are excluded from this check and do not count as mismatches.

</protocol>
