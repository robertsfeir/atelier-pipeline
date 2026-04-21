"""Tests for ADR-0033 Wave 2: pipeline-setup SKILL.md surgical edits.

Covers T-0033-020, T-0033-021, T-0033-022, T-0033-023, T-0033-024.

SKILL.md contains:
  * a fenced ```json block with the settings.json template (around line 344)
  * a file-copy manifest markdown table (~lines 280-315)
  * numbered `### Step 0/0a/0b/0c/1/...` sections

These tests parse SKILL.md structurally and assert the post-Wave-2 state:
  * enforce-scout-swarm.sh appears in the Agent matcher command hooks
  * prompt-brain-prefetch.sh `if:` lists exactly cal/colby/roz (no agatha)
  * brain-extractor `if:` lists 9 agent types (cal/colby/roz/agatha +
    robert/robert-spec/sable/sable-ux/ellis, and explicitly NOT brain-extractor)
  * Step 0c section exists between Step 0b and Step 1
  * session-hydrate.sh manifest description updated to "no-op" language

These tests will fail until Wave 2 is implemented. Wave 2 runs after Wave 1
PASS per the ADR's wave discipline.

Colby MUST NOT modify these assertions.
"""

import json
import re

from conftest import PROJECT_ROOT

SKILL_MD = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"


# ── Helpers ───────────────────────────────────────────────────────────────


def read_skill_md() -> str:
    assert SKILL_MD.exists(), f"SKILL.md missing at {SKILL_MD}"
    return SKILL_MD.read_text()


def extract_json_block(text: str) -> str:
    """Extract the first ```json fenced block that contains a top-level
    `"hooks"` key — that's the settings.json template.

    Multiple ```json fences may exist; we pick the one with `"hooks"`.
    """
    # Match fenced ```json ... ``` blocks (greedy minimum via non-greedy DOTALL).
    pattern = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)
    candidates = pattern.findall(text)
    assert candidates, "No ```json fenced block found in SKILL.md"
    # Prefer the one containing `"hooks"` key.
    for block in candidates:
        if '"hooks"' in block:
            return block
    # Fallback: first block.
    return candidates[0]


def flatten_hook_commands(hooks_section: dict) -> list[dict]:
    """Walk the settings.json hooks tree and yield every individual hook dict
    (the inner `{"type": "...", "command": "..."}` or `{"type": "prompt", ...}`
    or `{"type": "agent", ...}` dicts).
    """
    out: list[dict] = []
    for _event, event_entries in hooks_section.items():
        if not isinstance(event_entries, list):
            continue
        for entry in event_entries:
            hook_list = entry.get("hooks", []) if isinstance(entry, dict) else []
            for h in hook_list:
                if isinstance(h, dict):
                    out.append(h)
    return out


# ═══════════════════════════════════════════════════════════════════════
# T-0033-020: fenced ```json block parses with json.loads()
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_020_skill_md_json_block_parses():
    """The fenced ```json settings.json template in SKILL.md must parse
    as valid JSON via json.loads().

    Wave 2 surgically edits this block. A trailing comma, unbalanced bracket,
    or unescaped quote would silently break every fresh /pipeline-setup install.
    This test is the canary.
    """
    text = read_skill_md()
    block = extract_json_block(text)
    try:
        parsed = json.loads(block)
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"SKILL.md ```json block is invalid JSON after Wave 2 edits: {e}\n"
            f"Block excerpt:\n{block[:500]}..."
        ) from e
    assert isinstance(parsed, dict), "Parsed JSON block must be an object"
    assert "hooks" in parsed, "Parsed JSON block missing top-level 'hooks' key"


# ═══════════════════════════════════════════════════════════════════════
# T-0033-021: hook registrations wired correctly
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_022_manifest_has_enforce_scout_swarm_row():
    """The markdown file-copy manifest in SKILL.md must include a row that
    references enforce-scout-swarm.sh (so /pipeline-setup copies it into
    .claude/hooks/ on fresh installs). ADR-0033 Step 8 (C2 part 1).
    """
    text = read_skill_md()
    # The manifest is a markdown table. Look for a line referencing
    # source/claude/hooks/enforce-scout-swarm.sh.
    pattern = re.compile(
        r"\|\s*`source/claude/hooks/enforce-scout-swarm\.sh`",
    )
    match = pattern.search(text)
    assert match is not None, (
        "SKILL.md file-copy manifest missing a row for "
        "`source/claude/hooks/enforce-scout-swarm.sh`. "
        "ADR-0033 Step 8 (C2 part 1) requires this row."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0033-023: Step 0c exists between Step 0b and Step 1
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_023_step_0c_cleanup_section_present():
    """SKILL.md must contain a `### Step 0c:` section that:
      (a) appears AFTER `### Step 0b:`, and
      (b) appears BEFORE `### Step 1:`, and
      (c) references session-hydrate.sh (the cleanup target).

    ADR-0033 Step 10 Edit B inserts this section.
    """
    text = read_skill_md()

    step_0b_match = re.search(r"^###\s+Step\s+0b:", text, re.MULTILINE)
    step_0c_match = re.search(r"^###\s+Step\s+0c:", text, re.MULTILINE)
    step_1_match = re.search(r"^###\s+Step\s+1:", text, re.MULTILINE)

    assert step_0b_match is not None, (
        "SKILL.md missing existing `### Step 0b:` anchor — cannot verify ordering."
    )
    assert step_0c_match is not None, (
        "SKILL.md missing `### Step 0c:` section. ADR-0033 Step 10 Edit B "
        "requires a new cleanup section for orphan session-hydrate.sh registrations."
    )
    assert step_1_match is not None, (
        "SKILL.md missing `### Step 1:` anchor — cannot verify ordering."
    )

    assert step_0b_match.start() < step_0c_match.start() < step_1_match.start(), (
        f"Step 0c must appear between Step 0b and Step 1. "
        f"Offsets: 0b={step_0b_match.start()}, 0c={step_0c_match.start()}, "
        f"1={step_1_match.start()}"
    )

    # The Step 0c section body must mention session-hydrate.sh.
    body = text[step_0c_match.start():step_1_match.start()]
    assert "session-hydrate.sh" in body, (
        "Step 0c section does not reference session-hydrate.sh. "
        "The cleanup target must be named in the section body."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0033-024: session-hydrate.sh manifest description updated
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_024_session_hydrate_manifest_description_updated():
    """The manifest row describing session-hydrate.sh must contain both
    "no-op" and "NOT registered" (ADR-0033 Step 10 Edit A).

    Rationale: the source file is an intentional no-op superseded by the
    atelier_hydrate MCP tool. The manifest description previously claimed
    it "runs telemetry hydration at SessionStart" — stale and misleading.
    """
    text = read_skill_md()
    # Find the manifest row referencing session-hydrate.sh.
    row_pattern = re.compile(
        r"\|\s*`source/claude/hooks/session-hydrate\.sh`[^\n]*",
    )
    match = row_pattern.search(text)
    assert match is not None, (
        "SKILL.md manifest missing session-hydrate.sh row"
    )
    row = match.group(0)
    assert "no-op" in row, (
        f"session-hydrate.sh manifest description missing 'no-op' language. "
        f"Current row: {row!r}. ADR-0033 Step 10 Edit A requires the description "
        f"to state this is an intentional no-op superseded by atelier_hydrate MCP."
    )
    assert "NOT registered" in row, (
        f"session-hydrate.sh manifest description missing 'NOT registered' language. "
        f"Current row: {row!r}."
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0034-062: SKILL.md SubagentStop template has 9-agent condition (ADR-0034)
# ═══════════════════════════════════════════════════════════════════════

