"""ADR-0045 pre-build test assertions: Sherlock subagent + Slice 4 cleanup.

All new tests in this file are PRE-BUILD: they MUST FAIL against the current
codebase and PASS only after Colby implements ADR-0045. A test that passes
before Colby builds is flagged with justification in its docstring (Retro
Lesson #002).

Scope (per ADR-0045 Test Specification, nine categories):

  Category A (T_0045_001..009)  -- Sherlock persona presence.
  Category B (T_0045_010..015)  -- Gate 4 rewrite + Eva's user-bug-flow
                                   intake protocol.
  Category C (T_0045_016..023)  -- Routing-matrix + roster updates.
  Category D (T_0045_024..026)  -- Per-Agent Assignment Table.
  Category E (T_0045_027..030)  -- pipeline-config.json schema.
  Category F (T_0045_031..032)  -- Enforce-scout-swarm Sherlock bypass
                                   (documentation, not code edit).
  Category G (T_0045_033..047)  -- Removed-feature absence guards.
  Category H                    -- Existing-test updates (applied verbatim
                                   to 10 existing test files per the ADR
                                   Test Specification Category H table;
                                   NOT duplicated here).
  Category I (T_0045_069..071)  -- Test-directory deletions.

Counts:
  71 T_0045 tests total (A: 9, B: 6, C: 8, D: 3, E: 4, F: 2, G: 15, H: 21
  applied as verbatim updates in other files, I: 3).
  Defined in this file: 50 tests (A..G + I; Category H lives in the files
  it updates).

Reference: ADR-0045 §Test Specification (T_0045_001 through T_0045_071).
"""

import json
import re
import subprocess
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Absolute paths (tests run from any working directory)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SHARED_DIR = PROJECT_ROOT / "source" / "shared"
CLAUDE_SOURCE_DIR = PROJECT_ROOT / "source" / "claude"
CURSOR_SOURCE_DIR = PROJECT_ROOT / "source" / "cursor"

SHARED_AGENTS = SHARED_DIR / "agents"
SHARED_COMMANDS = SHARED_DIR / "commands"
SHARED_REFS = SHARED_DIR / "references"
SHARED_RULES = SHARED_DIR / "rules"
SHARED_HOOKS = SHARED_DIR / "hooks"
SHARED_PIPELINE = SHARED_DIR / "pipeline"

CLAUDE_AGENTS = CLAUDE_SOURCE_DIR / "agents"
CURSOR_AGENTS = CURSOR_SOURCE_DIR / "agents"

INSTALLED_CLAUDE_AGENTS = PROJECT_ROOT / ".claude" / "agents"
INSTALLED_CURSOR_AGENTS = PROJECT_ROOT / ".cursor-plugin" / "agents"

SKILLS_DIR = PROJECT_ROOT / "skills"

SHERLOCK_SOURCE = SHARED_AGENTS / "sherlock.md"
SHERLOCK_CLAUDE_FM = CLAUDE_AGENTS / "sherlock.frontmatter.yml"
SHERLOCK_CURSOR_FM = CURSOR_AGENTS / "sherlock.frontmatter.yml"
SHERLOCK_CLAUDE_INSTALLED = INSTALLED_CLAUDE_AGENTS / "sherlock.md"
SHERLOCK_CURSOR_INSTALLED = INSTALLED_CURSOR_AGENTS / "sherlock.md"

PIPELINE_ORCH = SHARED_RULES / "pipeline-orchestration.md"
DEFAULT_PERSONA = SHARED_RULES / "default-persona.md"
AGENT_SYSTEM = SHARED_RULES / "agent-system.md"
PIPELINE_MODELS = SHARED_RULES / "pipeline-models.md"
ROUTING_DETAIL = SHARED_REFS / "routing-detail.md"
PIPELINE_CONFIG = SHARED_PIPELINE / "pipeline-config.json"

SCOUT_HOOK = CLAUDE_SOURCE_DIR / "hooks" / "enforce-scout-swarm.sh"
SESSION_BOOT_SH = SHARED_HOOKS / "session-boot.sh"

ROZ_SOURCE = SHARED_AGENTS / "roz.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    assert path.exists(), f"File not found: {path}"
    return path.read_text()


def _read_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text()


def _extract_tag_content(text: str, tag: str) -> str:
    """Extract content within <tag>...</tag> (non-greedy; first match)."""
    pattern = rf"<{tag}(?:\s[^>]*)?>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    return ""


def _extract_mandatory_gates_section(text: str) -> str:
    """Return the Mandatory Gates section body of pipeline-orchestration.md."""
    match = re.search(
        r"## Mandatory Gates(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    return match.group(1) if match else ""


def _extract_gate4_body(text: str) -> str:
    """Return the body of Gate 4 in pipeline-orchestration.md.

    Gate 4 body is lines between the `4. **...` header and the next
    numbered gate (`5. **`) or the next `## ` heading.
    """
    match = re.search(
        r"^4\. \*\*[^\n]*\*\*(.*?)(?=^\d+\. \*\*|\n## )",
        text,
        re.DOTALL | re.MULTILINE,
    )
    return match.group(1) if match else ""


def _extract_user_bug_flow_protocol(text: str) -> str:
    """Return the body of `<protocol id="user-bug-flow">...</protocol>`."""
    match = re.search(
        r'<protocol id="user-bug-flow">(.*?)</protocol>',
        text,
        re.DOTALL,
    )
    return match.group(1) if match else ""


def _extract_section_between(text: str, start_heading: str, end_heading_re: str) -> str:
    """Extract text between a literal heading line and the next heading match."""
    # Find the start literal
    idx = text.find(start_heading)
    if idx == -1:
        return ""
    rest = text[idx + len(start_heading):]
    end_match = re.search(end_heading_re, rest)
    if end_match:
        return rest[: end_match.start()]
    return rest


def _count_table_data_rows(section: str) -> int:
    """Count markdown table data rows in a section (minus header)."""
    count = 0
    header_seen = False
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        inner = stripped[1:-1]
        # Divider row (|---|---|)
        if re.match(r"^[\s\-:|]+$", inner):
            continue
        if not header_seen:
            header_seen = True
            continue
        count += 1
    return count


def _extract_intent_detection_table(text: str) -> str:
    match = re.search(
        r"## Intent Detection(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    return match.group(1) if match else ""


def _extract_per_agent_table(text: str) -> str:
    """Extract `## Per-Agent Assignment Table` body of pipeline-models.md."""
    match = re.search(
        r"## Per-Agent Assignment Table(.*?)(?=\n## |\Z)", text, re.DOTALL
    )
    return match.group(1) if match else ""


def _run_session_boot_json(tmp_path: Path) -> dict:
    """Run session-boot.sh and parse its JSON emission."""
    import os
    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("CURSOR_PROJECT_DIR", None)
    state_dir = tmp_path / "docs" / "pipeline"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "pipeline-state.md").write_text(
        '# Pipeline State\n\n<!-- PIPELINE_STATUS: '
        '{"phase":"idle","feature":"","sizing":""} -->\n'
    )
    proc = subprocess.run(
        ["bash", str(SESSION_BOOT_SH)],
        input="",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(tmp_path),
        timeout=30,
    )
    return json.loads(proc.stdout)


# =============================================================================
# Category A: Sherlock persona presence (T_0045_001..009)
# =============================================================================


def test_T_0045_001_sherlock_source_persona_exists_and_readable():
    """T_0045_001 (happy): `source/shared/agents/sherlock.md` exists and is readable.

    Pre-build: FAILS -- Sherlock persona is a new file per ADR-0045.
    """
    assert SHERLOCK_SOURCE.exists(), (
        f"Sherlock persona not found at {SHERLOCK_SOURCE}. "
        "ADR-0045 Decision: Sherlock is a NEW subagent persona file."
    )
    text = SHERLOCK_SOURCE.read_text()
    assert len(text) > 0, "sherlock.md is empty"


def test_T_0045_002_sherlock_persona_contains_all_six_xml_tags_in_order():
    """T_0045_002 (happy): sherlock.md contains all six XML tags in order.

    Order: <identity>, <required-actions>, <workflow>, <examples>,
    <constraints>, <output>.

    Pre-build: FAILS -- persona file does not yet exist.
    """
    text = _read(SHERLOCK_SOURCE)
    tags_in_order = [
        "identity",
        "required-actions",
        "workflow",
        "examples",
        "constraints",
        "output",
    ]
    positions = []
    for tag in tags_in_order:
        idx = text.find(f"<{tag}>")
        assert idx != -1, (
            f"sherlock.md missing <{tag}> opening tag. "
            "ADR-0045 Test Spec T_0045_002 requires all six tags in order."
        )
        positions.append(idx)
    assert positions == sorted(positions), (
        f"sherlock.md XML tags appear out of order. "
        f"Expected order: {tags_in_order}. Got positions: {positions}."
    )


def test_T_0045_003_sherlock_workflow_contains_five_numbered_hunt_steps():
    """T_0045_003 (happy): sherlock.md <workflow> section contains all five
    numbered hunt-step literals.

    Required literals (all must appear inside <workflow>...</workflow>):
      `1. **Inventory`, `2. **Reproduce`, `3. **Trace the decision tree`,
      `4. **Bisect`, `5. **Root cause`.

    Pre-build: FAILS -- persona does not yet exist.
    """
    text = _read(SHERLOCK_SOURCE)
    workflow = _extract_tag_content(text, "workflow")
    assert workflow, "sherlock.md missing <workflow>...</workflow> block"
    required_literals = [
        "1. **Inventory",
        "2. **Reproduce",
        "3. **Trace the decision tree",
        "4. **Bisect",
        "5. **Root cause",
    ]
    missing = [lit for lit in required_literals if lit not in workflow]
    assert not missing, (
        f"sherlock.md <workflow> missing hunt-step literals: {missing}. "
        "ADR-0045 Test Spec T_0045_003 pins all five steps verbatim."
    )


def test_T_0045_004_sherlock_output_contains_case_file_header_and_eight_sections():
    """T_0045_004 (happy): sherlock.md <output> section contains the literal
    `# Case File:` and all eight return-format section headings.

    Required sections: `## Verdict`, `## Evidence`, `## Path walked`,
    `## Ruled out`, `## Reproduction confirmed`, `## Recommended fix`,
    `## Unknowns`, `## Correction to brief`.

    Pre-build: FAILS -- persona does not yet exist.
    """
    text = _read(SHERLOCK_SOURCE)
    output = _extract_tag_content(text, "output")
    assert output, "sherlock.md missing <output>...</output> block"
    assert "# Case File:" in output, (
        "sherlock.md <output> missing `# Case File:` header literal. "
        "ADR-0045 Test Spec T_0045_004."
    )
    required_sections = [
        "## Verdict",
        "## Evidence",
        "## Path walked",
        "## Ruled out",
        "## Reproduction confirmed",
        "## Recommended fix",
        "## Unknowns",
        "## Correction to brief",
    ]
    missing = [s for s in required_sections if s not in output]
    assert not missing, (
        f"sherlock.md <output> missing return-format sections: {missing}. "
        "ADR-0045 Test Spec T_0045_004 pins all 8 sections."
    )


def test_T_0045_005_sherlock_constraints_contains_required_literals():
    """T_0045_005 (happy): sherlock.md <constraints> section contains
    required literals.

    Required: `Diagnose only`, `two independent observations`,
    `30 tool calls`, `Read-only`, `Never read files inside`.

    Pre-build: FAILS -- persona does not yet exist.
    """
    text = _read(SHERLOCK_SOURCE)
    constraints = _extract_tag_content(text, "constraints")
    assert constraints, "sherlock.md missing <constraints>...</constraints> block"
    required_literals = [
        "Diagnose only",
        "two independent observations",
        "30 tool calls",
        "Read-only",
        "Never read files inside",
    ]
    missing = [lit for lit in required_literals if lit not in constraints]
    assert not missing, (
        f"sherlock.md <constraints> missing required literals: {missing}. "
        "ADR-0045 Test Spec T_0045_005."
    )


def test_T_0045_006_sherlock_claude_frontmatter_contains_required_fields():
    """T_0045_006 (happy): sherlock.frontmatter.yml (Claude) contains
    required fields.

    Required: `name: sherlock`, `model: opus`, `effort: high`,
    `maxTurns: 40`, `permissionMode: plan`,
    `disallowedTools: Agent, Write, Edit, MultiEdit, NotebookEdit`.

    Pre-build: FAILS -- frontmatter file does not yet exist.
    """
    assert SHERLOCK_CLAUDE_FM.exists(), (
        f"sherlock.frontmatter.yml (Claude) not found at {SHERLOCK_CLAUDE_FM}. "
        "ADR-0045 creates this file."
    )
    text = SHERLOCK_CLAUDE_FM.read_text()
    required = {
        "name: sherlock": "name",
        "model: opus": "model",
        "effort: high": "effort",
        "maxTurns: 40": "maxTurns",
        "permissionMode: plan": "permissionMode",
    }
    missing = [k for k in required if k not in text]
    assert not missing, (
        f"sherlock.frontmatter.yml (Claude) missing literals: {missing}."
    )
    # disallowedTools must contain all five values
    for tool in ["Agent", "Write", "Edit", "MultiEdit", "NotebookEdit"]:
        assert tool in text, (
            f"sherlock.frontmatter.yml (Claude) `disallowedTools` missing "
            f"entry `{tool}`. ADR-0045 Test Spec T_0045_006."
        )
    assert "disallowedTools:" in text, (
        "sherlock.frontmatter.yml (Claude) missing `disallowedTools:` key."
    )


def test_T_0045_007_sherlock_cursor_frontmatter_contains_required_fields():
    """T_0045_007 (happy): sherlock.frontmatter.yml (Cursor) contains
    required fields and does NOT contain `permissionMode`.

    Required: `name: sherlock`, `model: opus`, `effort: high`,
    `maxTurns: 40`, `disallowedTools: Agent, Write, Edit, MultiEdit,
    NotebookEdit`. Cursor overlay must NOT contain `permissionMode`.

    Pre-build: FAILS -- Cursor frontmatter does not yet exist.
    """
    assert SHERLOCK_CURSOR_FM.exists(), (
        f"sherlock.frontmatter.yml (Cursor) not found at {SHERLOCK_CURSOR_FM}. "
        "ADR-0045 creates this file."
    )
    text = SHERLOCK_CURSOR_FM.read_text()
    required = ["name: sherlock", "model: opus", "effort: high", "maxTurns: 40"]
    missing = [k for k in required if k not in text]
    assert not missing, (
        f"sherlock.frontmatter.yml (Cursor) missing literals: {missing}."
    )
    for tool in ["Agent", "Write", "Edit", "MultiEdit", "NotebookEdit"]:
        assert tool in text, (
            f"sherlock.frontmatter.yml (Cursor) `disallowedTools` missing "
            f"entry `{tool}`."
        )
    assert "permissionMode" not in text, (
        "sherlock.frontmatter.yml (Cursor) must NOT contain `permissionMode` "
        "(Cursor frontmatter omits this field per ADR-0045 Test Spec T_0045_007)."
    )


def test_T_0045_008_installed_sherlock_personas_exist_after_install():
    """T_0045_008 (happy): Installed `.claude/agents/sherlock.md` and
    `.cursor-plugin/agents/sherlock.md` exist after install.

    Pre-build: FAILS -- install step has not run for Sherlock.
    """
    assert SHERLOCK_CLAUDE_INSTALLED.exists(), (
        f"Installed Sherlock (Claude) not found at "
        f"{SHERLOCK_CLAUDE_INSTALLED}. ADR-0045 install step must assemble "
        "this file from source/shared/agents/sherlock.md + "
        "source/claude/agents/sherlock.frontmatter.yml."
    )
    assert SHERLOCK_CURSOR_INSTALLED.exists(), (
        f"Installed Sherlock (Cursor) not found at "
        f"{SHERLOCK_CURSOR_INSTALLED}. ADR-0045 install step must assemble "
        "this file from source/shared/agents/sherlock.md + "
        "source/cursor/agents/sherlock.frontmatter.yml."
    )


def test_T_0045_009_sherlock_identity_contains_relentless_detective_and_diagnose():
    """T_0045_009 (happy): sherlock.md <identity> contains literal
    `relentless detective` and `diagnose`.

    Pre-build: FAILS -- persona does not yet exist.
    """
    text = _read(SHERLOCK_SOURCE)
    identity = _extract_tag_content(text, "identity")
    assert identity, "sherlock.md missing <identity>...</identity> block"
    assert "relentless detective" in identity, (
        "sherlock.md <identity> missing literal `relentless detective`. "
        "ADR-0045 Test Spec T_0045_009 pins this domain-intent phrase."
    )
    assert "diagnose" in identity, (
        "sherlock.md <identity> missing literal `diagnose`. "
        "ADR-0045 Test Spec T_0045_009."
    )


# =============================================================================
# Category B: Gate 4 rewrite + Eva's user-bug-flow (T_0045_010..015)
# =============================================================================


def test_T_0045_010_gate_4_title_is_sherlock_investigates_verbatim():
    """T_0045_010 (happy): Mandatory Gate 4 title line is
    `4. **Sherlock investigates user-reported bugs. Eva does not.**` verbatim.

    Pre-build: FAILS -- current Gate 4 title says "Roz investigates...".
    """
    text = _read(PIPELINE_ORCH)
    expected = "4. **Sherlock investigates user-reported bugs. Eva does not.**"
    assert expected in text, (
        f"pipeline-orchestration.md missing Gate 4 title literal: {expected!r}. "
        "ADR-0045 Decision §Gate 4 rewrites the title verbatim."
    )


def test_T_0045_011_gate_4_body_contains_all_required_literals():
    """T_0045_011 (happy): Mandatory Gate 4 body contains all required literals.

    Required literals: `6-question intake`, `case brief`, `own context with
    no session inheritance`, `without scout fan-out`, `Case file below.`,
    `wait for approval`, `automated flow through Roz`.

    Pre-build: FAILS -- Gate 4 body has not been rewritten.
    """
    text = _read(PIPELINE_ORCH)
    body = _extract_gate4_body(text)
    assert body, (
        "pipeline-orchestration.md Gate 4 body extraction failed. "
        "Check that Gate 4 exists with `4. **...` header."
    )
    required_literals = [
        "6-question intake",
        "case brief",
        "own context with no session inheritance",
        "without scout fan-out",
        "Case file below.",
        "wait for approval",
        "automated flow through Roz",
    ]
    missing = [lit for lit in required_literals if lit not in body]
    assert not missing, (
        f"Gate 4 body missing required literals: {missing}. "
        "ADR-0045 Decision §Gate 4 rewrite."
    )


def test_T_0045_012_user_bug_flow_protocol_contains_all_six_intake_question_titles():
    """T_0045_012 (happy): default-persona.md <protocol id="user-bug-flow">
    contains all 6 intake question literals (Q1-Q6 titles).

    Required: `The symptom.`, `The reproduction.`, `The surface.`,
    `The environment and location.`, `The signals.`, `The prior.`

    Pre-build: FAILS -- user-bug-flow protocol has not yet been rewritten
    to include the 6-question intake.
    """
    text = _read(DEFAULT_PERSONA)
    protocol = _extract_user_bug_flow_protocol(text)
    assert protocol, (
        "default-persona.md missing <protocol id=\"user-bug-flow\"> block."
    )
    required_titles = [
        "The symptom.",
        "The reproduction.",
        "The surface.",
        "The environment and location.",
        "The signals.",
        "The prior.",
    ]
    missing = [t for t in required_titles if t not in protocol]
    assert not missing, (
        f"user-bug-flow protocol missing intake question titles: {missing}. "
        "ADR-0045 Decision pins all 6 question titles verbatim."
    )


def test_T_0045_013_user_bug_flow_protocol_contains_verbatim_quote_anchor():
    """T_0045_013 (happy): default-persona.md <protocol id="user-bug-flow">
    contains literal `Quote the user's Q1-Q6 answers verbatim`
    (intake-paraphrase-prohibition anchor).

    Pre-build: FAILS -- this anchor is new to ADR-0045.
    """
    text = _read(DEFAULT_PERSONA)
    protocol = _extract_user_bug_flow_protocol(text)
    assert protocol, (
        "default-persona.md missing <protocol id=\"user-bug-flow\"> block."
    )
    anchor = "Quote the user's Q1-Q6 answers verbatim"
    assert anchor in protocol, (
        f"user-bug-flow protocol missing anchor `{anchor}`. "
        "ADR-0045: Eva must not paraphrase user intake answers."
    )


def test_T_0045_014_gate_4_body_does_not_contain_old_roz_phrase():
    """T_0045_014 (failure): Mandatory Gate 4 body does NOT contain the
    literal `Roz in investigation mode` (old Gate 4 phrase removed).

    Pre-build: FAILS -- current Gate 4 body (line 160) contains this phrase.
    """
    text = _read(PIPELINE_ORCH)
    body = _extract_gate4_body(text)
    assert body, "Gate 4 body extraction failed."
    assert "Roz in investigation mode" not in body, (
        "pipeline-orchestration.md Gate 4 body still contains the literal "
        "`Roz in investigation mode`. ADR-0045 removes this phrase as the "
        "investigation role transfers from Roz to Sherlock."
    )


def test_T_0045_015_roz_persona_does_not_contain_investigation_mode_heading():
    """T_0045_015 (failure): source/shared/agents/roz.md does NOT contain
    the literal `## Investigation Mode`.

    Pre-build: FAILS -- roz.md currently contains `## Investigation Mode
    (Bug Diagnosis)` section.
    """
    text = _read(ROZ_SOURCE)
    assert "## Investigation Mode" not in text, (
        "roz.md still contains `## Investigation Mode` heading. "
        "ADR-0045 removes this section from Roz's persona -- investigation "
        "is handled by Sherlock."
    )


# =============================================================================
# Category C: Routing-matrix + roster updates (T_0045_016..023)
# =============================================================================


def test_T_0045_016_agent_system_subagent_roster_contains_sherlock_row():
    """T_0045_016 (happy): agent-system.md subagent roster table contains
    a row with `**Sherlock**` between Poirot and Distillator.

    Pre-build: FAILS -- Sherlock is new to the roster.
    """
    text = _read(AGENT_SYSTEM)
    assert "**Sherlock**" in text, (
        "agent-system.md missing `**Sherlock**` roster row. "
        "ADR-0045 Decision inserts Sherlock between Poirot and Distillator."
    )
    poirot_idx = text.find("**Poirot**")
    sherlock_idx = text.find("**Sherlock**")
    distillator_idx = text.find("**Distillator**")
    assert poirot_idx != -1, "agent-system.md missing `**Poirot**` reference"
    assert distillator_idx != -1, (
        "agent-system.md missing `**Distillator**` reference"
    )
    assert poirot_idx < sherlock_idx < distillator_idx, (
        f"`**Sherlock**` row must sit between Poirot (pos={poirot_idx}) "
        f"and Distillator (pos={distillator_idx}); got sherlock_idx={sherlock_idx}."
    )


def test_T_0045_017_agent_system_subagent_roster_does_not_contain_darwin_or_deps():
    """T_0045_017 (failure): agent-system.md subagent roster does NOT
    contain `**Darwin**` or `**Deps**` rows.

    Pre-build: FAILS -- roster currently contains Darwin and Deps entries.
    """
    text = _read(AGENT_SYSTEM)
    assert "**Darwin**" not in text, (
        "agent-system.md still contains `**Darwin**` roster row. "
        "ADR-0045 removes Darwin entirely (amputation)."
    )
    assert "**Deps**" not in text, (
        "agent-system.md still contains `**Deps**` roster row. "
        "ADR-0045 removes Deps entirely (amputation)."
    )


def test_T_0045_018_routing_auto_routing_summary_contains_sherlock_and_intake():
    """T_0045_018 (happy): agent-system.md <routing id="auto-routing">
    Summary section contains `Sherlock` and `intake`.

    Pre-build: FAILS -- Summary section not yet updated for Sherlock flow.
    """
    text = _read(AGENT_SYSTEM)
    match = re.search(
        r'<routing id="auto-routing">(.*?)</routing>', text, re.DOTALL
    )
    assert match, (
        "agent-system.md missing <routing id=\"auto-routing\"> block."
    )
    routing = match.group(1)
    # Locate the Summary subsection
    summary_match = re.search(
        r"### Summary(.*?)(?=\n### |\Z)", routing, re.DOTALL
    )
    assert summary_match, (
        "agent-system.md routing block missing `### Summary` subsection."
    )
    summary = summary_match.group(1)
    assert "Sherlock" in summary, (
        "Summary section missing `Sherlock`. ADR-0045 Decision adds "
        "Sherlock to the Summary routing bullets (bug intake entry)."
    )
    assert "intake" in summary, (
        "Summary section missing `intake`. ADR-0045 Decision pins the "
        "6-question intake keyword in the Summary."
    )


def test_T_0045_019_no_skill_tool_custom_commands_table_does_not_contain_debug_darwin_deps():
    """T_0045_019 (failure): agent-system.md <gate id="no-skill-tool">
    Custom Commands table does NOT contain rows for `/debug`, `/darwin`,
    `/deps`.

    Pre-build: FAILS -- table currently contains all three rows.
    """
    text = _read(AGENT_SYSTEM)
    match = re.search(
        r'<gate id="no-skill-tool">(.*?)</gate>', text, re.DOTALL
    )
    assert match, (
        "agent-system.md missing <gate id=\"no-skill-tool\"> block."
    )
    gate = match.group(1)
    for cmd in ["/debug", "/darwin", "/deps"]:
        # Match as a row literal with a pipe-separated cell (e.g. "| `/debug` |")
        assert f"`{cmd}`" not in gate, (
            f"no-skill-tool Custom Commands table still contains a row for "
            f"`{cmd}`. ADR-0045 amputates this command."
        )


def test_T_0045_020_no_skill_tool_subagent_table_contains_sherlock_bug_detective_row():
    """T_0045_020 (happy): agent-system.md <gate id="no-skill-tool">
    subagents-invoked-via-Agent-tool table contains a `Sherlock (bug detective)`
    row.

    Pre-build: FAILS -- Sherlock is new.
    """
    text = _read(AGENT_SYSTEM)
    match = re.search(
        r'<gate id="no-skill-tool">(.*?)</gate>', text, re.DOTALL
    )
    assert match, (
        "agent-system.md missing <gate id=\"no-skill-tool\"> block."
    )
    gate = match.group(1)
    assert "Sherlock (bug detective)" in gate, (
        "no-skill-tool subagents table missing `Sherlock (bug detective)` "
        "row. ADR-0045 Decision adds this entry."
    )


def test_T_0045_021_routing_detail_intent_detection_does_not_contain_deps_or_darwin_anchors():
    """T_0045_021 (failure): routing-detail.md Intent Detection table
    does NOT contain a row with literal `deps_agent_enabled` or
    `darwin_enabled`.

    Pre-build: FAILS -- routing-detail.md currently contains both anchors.
    """
    text = _read(ROUTING_DETAIL)
    intent_table = _extract_intent_detection_table(text)
    assert intent_table, (
        "routing-detail.md missing `## Intent Detection` section."
    )
    assert "deps_agent_enabled" not in intent_table, (
        "routing-detail.md Intent Detection still contains `deps_agent_enabled`. "
        "ADR-0045 removes the Deps routing row."
    )
    assert "darwin_enabled" not in intent_table, (
        "routing-detail.md Intent Detection still contains `darwin_enabled`. "
        "ADR-0045 removes the Darwin routing row."
    )


def test_T_0045_022_routing_detail_contains_sherlock_bug_row():
    """T_0045_022 (happy): routing-detail.md Intent Detection table contains
    a row matching regex `Reports a bug.*Sherlock`.

    Pre-build: FAILS -- current row routes bugs to Roz, not Sherlock.
    """
    text = _read(ROUTING_DETAIL)
    intent_table = _extract_intent_detection_table(text)
    assert intent_table, (
        "routing-detail.md missing `## Intent Detection` section."
    )
    matches = re.search(r"Reports a bug.*Sherlock", intent_table)
    assert matches, (
        "routing-detail.md Intent Detection missing row matching "
        "`Reports a bug.*Sherlock`. ADR-0045 Decision rewrites the "
        "bug-report row to route to Sherlock."
    )


def test_T_0045_023_routing_detail_intent_detection_has_exactly_17_data_rows():
    """T_0045_023 (happy): routing-detail.md Intent Detection table has
    exactly 17 data rows (19 existing - 2 removed for darwin/deps).

    Pre-build: FAILS -- current table has 19 data rows.
    """
    text = _read(ROUTING_DETAIL)
    intent_table = _extract_intent_detection_table(text)
    assert intent_table, (
        "routing-detail.md missing `## Intent Detection` section."
    )
    rows = _count_table_data_rows(intent_table)
    assert rows == 17, (
        f"Intent Detection table has {rows} data rows; expected 17. "
        "ADR-0045 removes Darwin and Deps rows (19 - 2 = 17)."
    )


# =============================================================================
# Category D: Per-Agent Assignment Table (T_0045_024..026)
# =============================================================================


def test_T_0045_024_per_agent_table_has_exactly_16_rows():
    """T_0045_024 (happy): pipeline-models.md Per-Agent Assignment Table has
    exactly 16 data rows (was 17 -- removed Darwin + Deps + added Sherlock
    = -2+1 = net -1 from 17, = 16).

    Pre-build: FAILS -- current table has 17 rows.
    """
    text = _read(PIPELINE_MODELS)
    section = _extract_per_agent_table(text)
    assert section, (
        "pipeline-models.md missing `## Per-Agent Assignment Table` section."
    )
    rows = _count_table_data_rows(section)
    assert rows == 16, (
        f"Per-Agent Assignment Table has {rows} data rows; expected 16 "
        "(ADR-0045: -Darwin, -Deps, +Sherlock = 17 - 2 + 1 = 16)."
    )


def test_T_0045_025_per_agent_table_contains_sherlock_opus_high_row():
    """T_0045_025 (happy): pipeline-models.md Per-Agent Assignment Table
    contains a row with `**Sherlock**` + `opus` + `high`.

    Pre-build: FAILS -- Sherlock is new.
    """
    text = _read(PIPELINE_MODELS)
    section = _extract_per_agent_table(text)
    assert section, (
        "pipeline-models.md missing Per-Agent Assignment Table section."
    )
    # Find the Sherlock row and verify it contains opus AND high.
    sherlock_rows = [
        line for line in section.splitlines()
        if "**Sherlock**" in line
    ]
    assert sherlock_rows, (
        "Per-Agent Assignment Table missing `**Sherlock**` row. "
        "ADR-0045 Decision §Per-Agent Assignment Table."
    )
    row = sherlock_rows[0]
    assert "opus" in row, (
        f"Sherlock row missing `opus`. Row: {row!r}. "
        "ADR-0045 assigns Sherlock model=opus."
    )
    assert "high" in row, (
        f"Sherlock row missing `high`. Row: {row!r}. "
        "ADR-0045 assigns Sherlock effort=high."
    )


def test_T_0045_026_per_agent_table_does_not_contain_darwin_or_deps_rows():
    """T_0045_026 (failure): pipeline-models.md Per-Agent Assignment Table
    does NOT contain a `**Darwin**` row or a `**Deps**` row.

    Pre-build: FAILS -- table currently contains both rows.
    """
    text = _read(PIPELINE_MODELS)
    section = _extract_per_agent_table(text)
    assert section, (
        "pipeline-models.md missing Per-Agent Assignment Table section."
    )
    assert "**Darwin**" not in section, (
        "Per-Agent Assignment Table still contains a `**Darwin**` row. "
        "ADR-0045 removes Darwin entirely."
    )
    assert "**Deps**" not in section, (
        "Per-Agent Assignment Table still contains a `**Deps**` row. "
        "ADR-0045 removes Deps entirely."
    )


# =============================================================================
# Category E: pipeline-config.json schema (T_0045_027..030)
# =============================================================================


def test_T_0045_027_pipeline_config_is_valid_json():
    """T_0045_027 (happy): pipeline-config.json is valid JSON.

    Pre-build: PASSES (currently valid); must remain valid post-build.
    """
    text = _read(PIPELINE_CONFIG)
    try:
        json.loads(text)
    except json.JSONDecodeError as e:
        pytest.fail(f"pipeline-config.json is not valid JSON: {e}")


def test_T_0045_028_pipeline_config_does_not_contain_darwin_enabled_key():
    """T_0045_028 (failure): pipeline-config.json does NOT contain a
    `darwin_enabled` key.

    Pre-build: FAILS -- key currently present at line 19.
    """
    data = json.loads(_read(PIPELINE_CONFIG))
    assert "darwin_enabled" not in data, (
        "pipeline-config.json still contains `darwin_enabled` key. "
        "ADR-0045 removes this key (Darwin amputated)."
    )


def test_T_0045_029_pipeline_config_does_not_contain_deps_agent_enabled_key():
    """T_0045_029 (failure): pipeline-config.json does NOT contain a
    `deps_agent_enabled` key.

    Pre-build: FAILS -- key currently present at line 18.
    """
    data = json.loads(_read(PIPELINE_CONFIG))
    assert "deps_agent_enabled" not in data, (
        "pipeline-config.json still contains `deps_agent_enabled` key. "
        "ADR-0045 removes this key (Deps amputated)."
    )


def test_T_0045_030_pipeline_config_regression_guard_preserves_other_keys():
    """T_0045_030 (happy): pipeline-config.json still contains
    `sentinel_enabled`, `agent_teams_enabled`, `ci_watch_enabled`,
    `dashboard_mode`, `design_system_path` (regression guard).

    Pre-build: PASSES (all five keys present today); must remain post-build.
    """
    data = json.loads(_read(PIPELINE_CONFIG))
    required_keys = [
        "sentinel_enabled",
        "agent_teams_enabled",
        "ci_watch_enabled",
        "dashboard_mode",
        "design_system_path",
    ]
    missing = [k for k in required_keys if k not in data]
    assert not missing, (
        f"pipeline-config.json missing regression-guard keys: {missing}. "
        "ADR-0045 ONLY removes darwin_enabled + deps_agent_enabled; "
        "all other keys must survive untouched."
    )


# =============================================================================
# Category F: Enforce-scout-swarm Sherlock bypass (T_0045_031..032)
# =============================================================================


def test_T_0045_031_enforce_scout_swarm_case_statement_covers_only_cal_roz_colby():
    """T_0045_031 (happy): source/claude/hooks/enforce-scout-swarm.sh case
    statement contains only `cal|roz|colby) ;;` and a `*) exit 0 ;;`
    fallthrough. Sherlock is NOT in the enforcement case -- the fallthrough
    bypass is the correct behavior.

    Pre-build: PASSES (case statement is currently `cal|roz|colby) ;;`
    with `*) exit 0 ;;` fallthrough; ADR-0045 Anti-goal 3 explicitly keeps
    this unchanged).
    """
    text = _read(SCOUT_HOOK)
    # Find the SUBAGENT_TYPE case statement
    case_block_match = re.search(
        r'case\s+"\$SUBAGENT_TYPE"\s+in(.*?)esac',
        text,
        re.DOTALL,
    )
    assert case_block_match, (
        "enforce-scout-swarm.sh missing `case \"$SUBAGENT_TYPE\" in ... esac` "
        "block."
    )
    case_body = case_block_match.group(1)
    assert "cal|roz|colby) ;;" in case_body, (
        "enforce-scout-swarm.sh case block must contain `cal|roz|colby) ;;` "
        "literal. ADR-0045 Anti-goal 3: leave the case statement untouched."
    )
    assert "*) exit 0 ;;" in case_body, (
        "enforce-scout-swarm.sh case block must contain `*) exit 0 ;;` "
        "fallthrough. This is the Sherlock bypass mechanism -- any "
        "subagent_type not in cal|roz|colby falls through to exit 0."
    )


def test_T_0045_032_enforce_scout_swarm_has_no_sherlock_mention():
    """T_0045_032 (happy): source/claude/hooks/enforce-scout-swarm.sh grep
    for `sherlock` returns zero matches (no explicit bypass case arm needed
    -- Anti-goal 3).

    Pre-build: PASSES (hook does not mention Sherlock today). Post-build:
    must still pass -- ADR-0045 Anti-goal 3 explicitly forbids adding a
    Sherlock arm. The fallthrough `*) exit 0 ;;` handles the bypass.
    """
    text = _read(SCOUT_HOOK)
    # Case-insensitive match on the literal name.
    occurrences = len(re.findall(r"sherlock", text, re.IGNORECASE))
    assert occurrences == 0, (
        f"enforce-scout-swarm.sh contains {occurrences} `sherlock` "
        "occurrence(s); expected 0. ADR-0045 Anti-goal 3: Sherlock bypass "
        "relies on the `*) exit 0 ;;` fallthrough; no explicit arm is "
        "permitted."
    )


# =============================================================================
# Category G: Removed-feature absence guards (T_0045_033..047)
# =============================================================================


def test_T_0045_033_debug_command_source_does_not_exist():
    """T_0045_033 (failure): File `source/shared/commands/debug.md` does NOT exist.

    Pre-build: FAILS -- debug.md currently present.
    """
    f = SHARED_COMMANDS / "debug.md"
    assert not f.exists(), (
        f"{f} still exists. ADR-0045 amputates /debug."
    )


def test_T_0045_034_darwin_command_source_does_not_exist():
    """T_0045_034 (failure): File `source/shared/commands/darwin.md` does NOT exist."""
    f = SHARED_COMMANDS / "darwin.md"
    assert not f.exists(), (
        f"{f} still exists. ADR-0045 amputates /darwin."
    )


def test_T_0045_035_deps_command_source_does_not_exist():
    """T_0045_035 (failure): File `source/shared/commands/deps.md` does NOT exist."""
    f = SHARED_COMMANDS / "deps.md"
    assert not f.exists(), (
        f"{f} still exists. ADR-0045 amputates /deps."
    )


def test_T_0045_036_create_agent_command_source_does_not_exist():
    """T_0045_036 (failure): File `source/shared/commands/create-agent.md` does NOT exist."""
    f = SHARED_COMMANDS / "create-agent.md"
    assert not f.exists(), (
        f"{f} still exists. ADR-0045 amputates /create-agent."
    )


def test_T_0045_037_telemetry_hydrate_command_source_does_not_exist():
    """T_0045_037 (failure): File `source/shared/commands/telemetry-hydrate.md` does NOT exist."""
    f = SHARED_COMMANDS / "telemetry-hydrate.md"
    assert not f.exists(), (
        f"{f} still exists. ADR-0045 amputates /telemetry-hydrate."
    )


def test_T_0045_038_darwin_agent_source_does_not_exist():
    """T_0045_038 (failure): File `source/shared/agents/darwin.md` does NOT exist."""
    f = SHARED_AGENTS / "darwin.md"
    assert not f.exists(), (
        f"{f} still exists. ADR-0045 amputates the Darwin agent persona."
    )


def test_T_0045_039_deps_agent_source_does_not_exist():
    """T_0045_039 (failure): File `source/shared/agents/deps.md` does NOT exist."""
    f = SHARED_AGENTS / "deps.md"
    assert not f.exists(), (
        f"{f} still exists. ADR-0045 amputates the Deps agent persona."
    )


def test_T_0045_040_skills_dashboard_directory_does_not_exist():
    """T_0045_040 (failure): Directory `skills/dashboard/` does NOT exist."""
    d = SKILLS_DIR / "dashboard"
    assert not d.exists(), (
        f"{d} still exists. ADR-0045 amputates the dashboard skill."
    )


def test_T_0045_041_skills_pipeline_overview_directory_does_not_exist():
    """T_0045_041 (failure): Directory `skills/pipeline-overview/` does NOT exist."""
    d = SKILLS_DIR / "pipeline-overview"
    assert not d.exists(), (
        f"{d} still exists. ADR-0045 amputates the pipeline-overview skill."
    )


def test_T_0045_042_skills_load_design_directory_does_not_exist():
    """T_0045_042 (failure): Directory `skills/load-design/` does NOT exist."""
    d = SKILLS_DIR / "load-design"
    assert not d.exists(), (
        f"{d} still exists. ADR-0045 amputates the load-design skill "
        "(Step 1a fold into pipeline-setup absorbs the content)."
    )


def test_T_0045_043_pipeline_setup_skill_does_not_contain_step_6d_or_6e():
    """T_0045_043 (failure): skills/pipeline-setup/SKILL.md does NOT contain
    `### Step 6d: Deps Agent Opt-In` or `### Step 6e: Darwin`.

    Pre-build: FAILS -- both sections currently present.
    """
    f = SKILLS_DIR / "pipeline-setup" / "SKILL.md"
    text = _read(f)
    assert "### Step 6d: Deps Agent Opt-In" not in text, (
        "pipeline-setup/SKILL.md still contains `### Step 6d: Deps Agent "
        "Opt-In`. ADR-0045 removes it (Deps amputated)."
    )
    assert "### Step 6e: Darwin" not in text, (
        "pipeline-setup/SKILL.md still contains `### Step 6e: Darwin`. "
        "ADR-0045 removes it (Darwin amputated)."
    )


def test_T_0045_044_pipeline_setup_skill_contains_step_1a_design_system_path():
    """T_0045_044 (happy): skills/pipeline-setup/SKILL.md contains
    `### Step 1a: Design System Path` (fold success from load-design skill).

    Pre-build: FAILS -- Step 1a has not been folded in yet.
    """
    f = SKILLS_DIR / "pipeline-setup" / "SKILL.md"
    text = _read(f)
    assert "### Step 1a: Design System Path" in text, (
        "pipeline-setup/SKILL.md missing `### Step 1a: Design System Path`. "
        "ADR-0045 folds the load-design skill into pipeline-setup as Step 1a."
    )


def test_T_0045_045_session_boot_sh_does_not_set_darwin_enabled_or_deps_agent_enabled():
    """T_0045_045 (failure): source/shared/hooks/session-boot.sh does NOT
    contain `DARWIN_ENABLED=` or `DEPS_AGENT_ENABLED=` variable assignments.

    Pre-build: FAILS -- session-boot.sh currently has both assignments.
    """
    text = _read(SESSION_BOOT_SH)
    assert "DARWIN_ENABLED=" not in text, (
        "session-boot.sh still contains `DARWIN_ENABLED=` assignment. "
        "ADR-0045 removes this variable (Darwin amputated)."
    )
    assert "DEPS_AGENT_ENABLED=" not in text, (
        "session-boot.sh still contains `DEPS_AGENT_ENABLED=` assignment. "
        "ADR-0045 removes this variable (Deps amputated)."
    )


def test_T_0045_046_session_boot_sh_core_agents_contains_sherlock_and_drops_darwin_deps_with_14_tokens():
    """T_0045_046 (happy): source/shared/hooks/session-boot.sh CORE_AGENTS
    string contains `sherlock`, does NOT contain `darwin` or `deps`.
    Token count of CORE_AGENTS = 14.

    Pre-build: FAILS -- current CORE_AGENTS line has 15 tokens (with darwin
    + deps, without sherlock).
    """
    text = _read(SESSION_BOOT_SH)
    core_line = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("CORE_AGENTS="):
            core_line = stripped
            break
    assert core_line is not None, (
        "session-boot.sh missing `CORE_AGENTS=` assignment."
    )
    value = core_line.split("=", 1)[1].strip().strip('"').strip("'")
    tokens = value.split()
    assert "sherlock" in tokens, (
        f"CORE_AGENTS missing `sherlock`. Current tokens: {tokens}. "
        "ADR-0045 adds Sherlock to the CORE_AGENTS whitelist."
    )
    assert "darwin" not in tokens, (
        f"CORE_AGENTS still contains `darwin`. Current tokens: {tokens}. "
        "ADR-0045 removes Darwin."
    )
    assert "deps" not in tokens, (
        f"CORE_AGENTS still contains `deps`. Current tokens: {tokens}. "
        "ADR-0045 removes Deps."
    )
    assert len(tokens) == 14, (
        f"CORE_AGENTS has {len(tokens)} tokens; expected 14. "
        f"Tokens: {tokens}. ADR-0045: 15 - 2 (darwin, deps) + 1 (sherlock) = 14."
    )


def test_T_0045_047_session_boot_sh_json_output_does_not_contain_darwin_or_deps_keys(tmp_path):
    """T_0045_047 (failure): source/shared/hooks/session-boot.sh JSON output
    does NOT contain `"darwin_enabled":` or `"deps_agent_enabled":` literal.

    Pre-build: FAILS -- hook currently emits both keys.
    """
    data = _run_session_boot_json(tmp_path)
    assert "darwin_enabled" not in data, (
        "session-boot.sh JSON output still contains `darwin_enabled` key. "
        "ADR-0045 removes this from the JSON emission."
    )
    assert "deps_agent_enabled" not in data, (
        "session-boot.sh JSON output still contains `deps_agent_enabled` key. "
        "ADR-0045 removes this from the JSON emission."
    )


# =============================================================================
# Category H marker (assertions live in the files being updated)
# =============================================================================
#
# Category H (T_0045_048..068) is applied as verbatim body replacements to
# existing test files per the ADR-0045 §Test Specification Category H table.
# Updated files:
#   - tests/conftest.py                              (T_0045_048)
#   - tests/hooks/test_adr_0022_phase1_overlay.py    (T_0045_049)
#   - tests/adr-0023-reduction/test_reduction_structural.py (T_0045_050..052)
#   - tests/hooks/test_session_boot.py               (T_0045_053..056)
#   - tests/adr-0042/test_adr_0042.py                (T_0045_057..059)
#   - tests/test_adr0044_instruction_budget_trim.py  (T_0045_060..063)
#   - tests/dashboard/test_dashboard_integration.py  (T_0045_064..067)
#   - tests/cursor-port/test_cursor_port.py          (T_0045_068)
#
# These updates rename functions, substitute constants, and delete two
# functions (T_0042_012, T_0044_042 original body -> inverted guard). The
# assertions live in their home files so Pytest discovers them under their
# original ADR test suites; duplicating them here would create name collisions.
# The ADR Test Specification §Category H table remains the authoritative
# inventory for traceability.


# =============================================================================
# Category I: Test-directory deletions (T_0045_069..071)
# =============================================================================


def test_T_0045_069_adr_0015_deps_test_directory_does_not_exist():
    """T_0045_069 (failure): Delete `tests/adr-0015-deps/` directory
    (recursive, including test_deps_structural.py and any __init__.py,
    conftests, etc.). Target: 62 tests removed.

    Pre-build: FAILS -- directory currently exists.
    """
    d = PROJECT_ROOT / "tests" / "adr-0015-deps"
    assert not d.exists(), (
        f"{d} still exists. ADR-0045 deletes this test directory "
        "(Deps amputated, 62 tests removed)."
    )


def test_T_0045_070_adr_0016_darwin_test_directory_does_not_exist():
    """T_0045_070 (failure): Delete `tests/adr-0016-darwin/` directory
    (recursive). Target: 96 tests removed.

    Pre-build: FAILS -- directory currently exists.
    """
    d = PROJECT_ROOT / "tests" / "adr-0016-darwin"
    assert not d.exists(), (
        f"{d} still exists. ADR-0045 deletes this test directory "
        "(Darwin amputated, 96 tests removed)."
    )


def test_T_0045_071_adr_0045_test_file_structure_exists_as_delta_proxy():
    """T_0045_071 (happy): After deletion, the new tests/adr-0045/
    structure exists as a proxy for the net test count delta
    (-158 - 2 + 71 = -89 net, asserted structurally here).

    This test exists as a structural anchor for the count-delta claim.
    The actual numeric delta (--collect-only) is a pipeline-level
    invariant Roz verifies post-build by running pytest and comparing
    the collected count to the pre-ADR baseline.

    Pre-build: PASSES once this file + __init__.py exist (both are
    authored pre-build as part of this test spec). Post-build: must
    still pass -- the file survives as the home for T_0045_NNN tests.
    """
    adr_0045_dir = PROJECT_ROOT / "tests" / "adr-0045"
    assert adr_0045_dir.exists(), (
        f"{adr_0045_dir} must exist as the home for T_0045_NNN tests."
    )
    this_file = adr_0045_dir / "test_adr_0045.py"
    init_file = adr_0045_dir / "__init__.py"
    assert this_file.exists(), (
        f"{this_file} must exist to host the T_0045 test suite."
    )
    assert init_file.exists(), (
        f"{init_file} must exist as a pytest package marker."
    )
