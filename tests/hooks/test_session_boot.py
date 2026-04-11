"""Tests for session-boot.sh (SessionStart hook) — ADR-0033 Wave 1 Steps 1 & 2.

Covers T-0033-001, T-0033-003, T-0033-004, T-0033-005, T-0033-006, T-0033-007, T-0033-008.

The hook emits a JSON blob describing pipeline activation state, core-agent
count, and other session-boot fields. These tests assert the FIXED behavior
after the ADR-0033 Step 1 (grep pattern) and Step 2 (CORE_AGENTS list) fixes
have been applied. Tests will fail against the current (broken) source.

Colby MUST NOT modify these assertions.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import PROJECT_ROOT

HOOK_SOURCE = PROJECT_ROOT / "source" / "shared" / "hooks" / "session-boot.sh"


def run_session_boot(tmp_path: Path, input_json: str = "") -> subprocess.CompletedProcess:
    """Run session-boot.sh from tmp_path with no CLAUDE_PROJECT_DIR.

    The hook reads docs/pipeline/pipeline-state.md relative to cwd, so we cd
    into tmp_path via cwd= and lay out the fixture there.
    """
    assert HOOK_SOURCE.exists(), f"session-boot.sh missing at {HOOK_SOURCE}"
    env = os.environ.copy()
    # Ensure no existing project env confuses the hook.
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("CURSOR_PROJECT_DIR", None)
    return subprocess.run(
        ["bash", str(HOOK_SOURCE)],
        input=input_json,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(tmp_path),
        timeout=30,
    )


def write_state(tmp_path: Path, status_json: str) -> None:
    """Write docs/pipeline/pipeline-state.md with a PIPELINE_STATUS line."""
    state_dir = tmp_path / "docs" / "pipeline"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "pipeline-state.md").write_text(
        f"# Pipeline State\n\nSome preamble.\n\n<!-- PIPELINE_STATUS: {status_json} -->\n"
    )


def write_raw_state(tmp_path: Path, body: str) -> None:
    state_dir = tmp_path / "docs" / "pipeline"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "pipeline-state.md").write_text(body)


def make_agents_dir(tmp_path: Path, agent_names: list[str]) -> None:
    """Create .claude/agents/<name>.md files with YAML `name:` frontmatter."""
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for name in agent_names:
        # session-boot.sh greps for ^name: in each file and counts it as an agent.
        # Give it a minimal markdown stub with the right header.
        (agents_dir / f"{name}.md").write_text(f"---\nname: {name}\n---\n\nStub.\n")


def parse_boot_output(proc: subprocess.CompletedProcess) -> dict:
    """Parse the JSON blob from the hook's stdout.

    The hook emits a single JSON object — parse it directly.
    """
    assert proc.returncode == 0, (
        f"session-boot.sh exited {proc.returncode}. stderr={proc.stderr!r}"
    )
    return json.loads(proc.stdout)


# ═══════════════════════════════════════════════════════════════════════
# T-0033-001: canonical PIPELINE_STATUS line parses → pipeline_active=true
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_001_canonical_pipeline_status_parses(tmp_path):
    """A canonical `PIPELINE_STATUS: {...}` line with phase+feature must set
    pipeline_active=true and propagate phase and feature to the JSON output.

    Canonical format verified by source/claude/hooks/enforce-scout-swarm.sh
    line 74: `grep -o 'PIPELINE_STATUS: {[^}]*}'`. The literal space after the
    colon is load-bearing.
    """
    write_state(tmp_path, '{"phase":"build","feature":"hook-audit","sizing":"medium"}')
    proc = run_session_boot(tmp_path)
    data = parse_boot_output(proc)
    assert data["pipeline_active"] is True, (
        f"Expected pipeline_active=true for phase=build feature=hook-audit. "
        f"Got {data['pipeline_active']!r}. Full output: {data!r}"
    )
    assert data["phase"] == "build", f"phase should be 'build', got {data['phase']!r}"
    assert data["feature"] == "hook-audit", (
        f"feature should be 'hook-audit', got {data['feature']!r}"
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0033-003: phase=idle → pipeline_active=false
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_003_phase_idle_reports_inactive(tmp_path):
    """When PHASE is `idle`, pipeline_active must be false regardless of other fields."""
    write_state(tmp_path, '{"phase":"idle","feature":"","sizing":""}')
    proc = run_session_boot(tmp_path)
    data = parse_boot_output(proc)
    assert data["pipeline_active"] is False, (
        f"phase=idle must yield pipeline_active=false, got {data['pipeline_active']!r}"
    )
    assert data["phase"] == "idle"


# ═══════════════════════════════════════════════════════════════════════
# T-0033-004: phase=complete → pipeline_active=false
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_004_phase_complete_reports_inactive(tmp_path):
    """When PHASE is `complete`, pipeline_active must be false."""
    write_state(tmp_path, '{"phase":"complete","feature":"finished-feature","sizing":"small"}')
    proc = run_session_boot(tmp_path)
    data = parse_boot_output(proc)
    assert data["pipeline_active"] is False, (
        f"phase=complete must yield pipeline_active=false, got {data['pipeline_active']!r}"
    )
    assert data["phase"] == "complete"


# ═══════════════════════════════════════════════════════════════════════
# T-0033-005: legacy no-space `PIPELINE_STATUS:{...}` must NOT match
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_005_legacy_no_space_pattern_not_matched(tmp_path):
    """The fixed grep pattern requires a space after the colon. A legacy
    no-space `PIPELINE_STATUS:{...}` line must NOT be matched — the hook
    falls through to defaults and reports pipeline_active=false.

    Rationale: canonical format across the codebase (pipeline-state.md line 6,
    enforce-scout-swarm.sh line 74) uses the space. The old broken pattern
    matched either style; the fixed pattern matches only the canonical one.
    """
    # Legacy no-space marker — fixed pattern should NOT match this.
    write_raw_state(
        tmp_path,
        "# Pipeline State\n\n"
        '<!-- PIPELINE_STATUS:{"phase":"build","feature":"legacy-feature"} -->\n',
    )
    proc = run_session_boot(tmp_path)
    data = parse_boot_output(proc)
    # Because the canonical pattern did not match, defaults apply: phase=idle, active=false.
    assert data["pipeline_active"] is False, (
        f"Legacy no-space marker must not match the fixed pattern. "
        f"Expected pipeline_active=false (defaults), got {data['pipeline_active']!r}"
    )
    assert data["phase"] == "idle", (
        f"Legacy marker should leave phase at default 'idle', got {data['phase']!r}"
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0033-006: CORE_AGENTS string in the hook contains all 15 agent names
# ═══════════════════════════════════════════════════════════════════════


EXPECTED_CORE_AGENTS_15 = [
    "cal", "colby", "roz", "ellis", "agatha", "robert", "sable",
    "investigator", "distillator", "sentinel", "darwin", "deps",
    "brain-extractor", "robert-spec", "sable-ux",
]


def test_T_0033_006_core_agents_list_contains_all_15(tmp_path):
    """The CORE_AGENTS variable in session-boot.sh must list all 15 pipeline-native agents.

    Verified structurally: read the source file, grep for the CORE_AGENTS= line,
    tokenize, assert every expected name is present.
    """
    text = HOOK_SOURCE.read_text()
    # Locate the CORE_AGENTS="..." assignment line.
    core_line = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("CORE_AGENTS="):
            core_line = stripped
            break
    assert core_line is not None, (
        "session-boot.sh missing CORE_AGENTS=... assignment"
    )
    # Extract the quoted value.
    # Format: CORE_AGENTS="cal colby roz ..."
    value = core_line.split("=", 1)[1].strip().strip('"').strip("'")
    tokens = value.split()
    for agent in EXPECTED_CORE_AGENTS_15:
        assert agent in tokens, (
            f"CORE_AGENTS missing '{agent}'. Current list: {tokens}. "
            f"Expected all 15: {EXPECTED_CORE_AGENTS_15}"
        )
    assert len(tokens) == 15, (
        f"CORE_AGENTS should have exactly 15 entries, has {len(tokens)}: {tokens}"
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0033-007: pipeline-default agents dir → CUSTOM_AGENT_COUNT=0
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_007_default_agent_set_reports_zero_custom(tmp_path):
    """A .claude/agents/ directory populated with exactly the 15 pipeline-native
    agents must yield custom_agent_count=0.
    """
    make_agents_dir(tmp_path, EXPECTED_CORE_AGENTS_15)
    # Need a pipeline-state file so hook runs cleanly; idle state.
    write_state(tmp_path, '{"phase":"idle","feature":""}')
    proc = run_session_boot(tmp_path)
    data = parse_boot_output(proc)
    assert data["custom_agent_count"] == 0, (
        f"15 pipeline-native agents should produce custom_agent_count=0, "
        f"got {data['custom_agent_count']}. Full output: {data!r}"
    )


# ═══════════════════════════════════════════════════════════════════════
# T-0033-008: one extra non-core agent → CUSTOM_AGENT_COUNT=1
# ═══════════════════════════════════════════════════════════════════════


def test_T_0033_008_one_custom_agent_reports_one(tmp_path):
    """Adding a single non-core agent file must bump custom_agent_count to 1.

    This verifies both the positive case (the extra agent is counted) and
    regression protection: previously the broken CORE_AGENTS over-reported
    by 6 (because 6 pipeline-native agents weren't in the list), so a bare
    fixture could report a non-zero count even with no real custom agents.
    """
    agents = list(EXPECTED_CORE_AGENTS_15) + ["zod-custom"]
    make_agents_dir(tmp_path, agents)
    write_state(tmp_path, '{"phase":"idle","feature":""}')
    proc = run_session_boot(tmp_path)
    data = parse_boot_output(proc)
    assert data["custom_agent_count"] == 1, (
        f"15 core + 1 custom should produce custom_agent_count=1, "
        f"got {data['custom_agent_count']}. Full output: {data!r}"
    )
