"""Tests for ADR-0020 Step 5: Documentation and file sync. Covers T-0020-064 through T-0020-069."""

import re
import subprocess

from conftest import PROJECT_ROOT


# ADR-0025 supersedes: warn-dor-dod.sh deleted and replaced by session-hydrate.sh in technical-reference.md (ADR-0025 R11, R9)
def test_T_0020_064_technical_reference_all_hooks():
    doc = (PROJECT_ROOT / "docs" / "guide" / "technical-reference.md").read_text()
    for hook in [
        "enforce-eva-paths.sh", "enforce-roz-paths.sh", "enforce-cal-paths.sh",
        "enforce-colby-paths.sh", "enforce-agatha-paths.sh", "enforce-product-paths.sh",
        "enforce-ux-paths.sh", "enforce-sequencing.sh", "enforce-pipeline-activation.sh",
        "enforce-git.sh", "session-hydrate.sh", "pre-compact.sh",
        "log-agent-start.sh", "log-agent-stop.sh", "post-compact-reinject.sh", "log-stop-failure.sh",
    ]:
        assert hook in doc, f"Expected hook '{hook}' in technical-reference.md"
    # warn-dor-dod.sh must not appear in technical-reference.md after ADR-0025 deleted it
    assert "warn-dor-dod.sh" not in doc, (
        "warn-dor-dod.sh must not appear in technical-reference.md after ADR-0025 R11 deleted it."
    )
    for event in ["PreToolUse", "SubagentStart", "SubagentStop", "PostCompact", "StopFailure"]:
        assert event in doc


def test_T_0020_065_user_guide():
    doc = (PROJECT_ROOT / "docs" / "guide" / "user-guide.md").read_text()
    assert re.search(r"if.*conditional|conditional.*if|\"if\".*field|if.*filter", doc, re.IGNORECASE)
    for event in ["SubagentStart", "PostCompact", "StopFailure"]:
        assert event in doc


def test_T_0020_066_source_hooks_installed():
    source_dir = PROJECT_ROOT / "source" / "claude" / "hooks"
    installed_dir = PROJECT_ROOT / ".claude" / "hooks"
    assert source_dir.is_dir()
    assert installed_dir.is_dir()
    missing = [f.name for f in source_dir.glob("*.sh") if not (installed_dir / f.name).exists()]
    assert missing == [], f"Missing installed copies: {missing}"


def test_T_0020_067_cursor_skill_md_hooks():
    # ADR-0022: Claude Code uses per-agent enforcement hooks; Cursor uses the
    # enforce-paths.sh monolith.  The two platforms intentionally diverge on
    # their enforcement strategy, so a simple subset check would always fail.
    # Instead we verify the known architecture contract:
    #   - Cursor carries enforce-paths.sh (monolith); CC does not.
    #   - CC carries per-agent enforce-*.sh hooks; Cursor does not.
    cc_skill = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"
    cursor_skill = PROJECT_ROOT / ".cursor-plugin" / "skills" / "pipeline-setup" / "SKILL.md"
    assert cc_skill.exists()
    assert cursor_skill.exists()
    cursor_hooks = set(re.findall(r"[a-z]+-[a-z-]+\.sh", cursor_skill.read_text()))
    cc_hooks = set(re.findall(r"[a-z]+-[a-z-]+\.sh", cc_skill.read_text()))

    # Cursor must carry the monolith enforcement hook
    assert "enforce-paths.sh" in cursor_hooks, "Cursor SKILL.md missing enforce-paths.sh"
    # Claude Code must NOT carry the Cursor monolith
    assert "enforce-paths.sh" not in cc_hooks, "CC SKILL.md should not reference enforce-paths.sh"
    # Claude Code must carry per-agent enforcement hooks
    per_agent_hooks = {
        "enforce-eva-paths.sh", "enforce-roz-paths.sh", "enforce-cal-paths.sh",
        "enforce-colby-paths.sh", "enforce-agatha-paths.sh",
        "enforce-product-paths.sh", "enforce-ux-paths.sh",
    }
    missing_per_agent = per_agent_hooks - cc_hooks
    assert missing_per_agent == set(), f"CC SKILL.md missing per-agent hooks: {missing_per_agent}"
    # Cursor must NOT carry per-agent enforcement hooks
    unexpected_in_cursor = per_agent_hooks & cursor_hooks
    assert unexpected_in_cursor == set(), (
        f"Cursor SKILL.md should not reference per-agent hooks: {unexpected_in_cursor}"
    )


def test_T_0020_068_byte_identical():
    source_dir = PROJECT_ROOT / "source" / "claude" / "hooks"
    installed_dir = PROJECT_ROOT / ".claude" / "hooks"
    mismatches = []
    for src in source_dir.glob("*.sh"):
        dst = installed_dir / src.name
        if dst.exists() and src.read_bytes() != dst.read_bytes():
            mismatches.append(src.name)
    # Also check enforcement-config.json
    src_cfg = source_dir / "enforcement-config.json"
    dst_cfg = installed_dir / "enforcement-config.json"
    if src_cfg.exists() and dst_cfg.exists() and src_cfg.read_bytes() != dst_cfg.read_bytes():
        mismatches.append("enforcement-config.json")
    assert mismatches == [], f"Mismatched files: {mismatches}"


def test_T_0020_069_cursor_skill_matches():
    # ADR-0022: The two platforms share a common set of non-enforcement hooks
    # (sequencing, git, lifecycle, quality, telemetry, etc.).  Exact set equality
    # no longer holds because enforcement is platform-specific (per-agent for CC,
    # monolith for Cursor).  We verify that every shared hook appears on both
    # platforms and that the platform-specific sets are non-empty on their
    # respective sides.
    cc_skill = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"
    cursor_skill = PROJECT_ROOT / ".cursor-plugin" / "skills" / "pipeline-setup" / "SKILL.md"
    cc_hooks = set(re.findall(r"[a-z]+-[a-z-]+\.sh", cc_skill.read_text()))
    cursor_hooks = set(re.findall(r"[a-z]+-[a-z-]+\.sh", cursor_skill.read_text()))

    # These hooks are platform-agnostic and must appear in both SKILL.md files
    shared_hooks = {
        "enforce-git.sh",
        "enforce-pipeline-activation.sh",
        "enforce-sequencing.sh",
        "log-agent-start.sh",
        "log-agent-stop.sh",
        "log-stop-failure.sh",
        "post-compact-reinject.sh",
        "pre-compact.sh",
        "session-hydrate.sh",
    }
    missing_from_cc = shared_hooks - cc_hooks
    missing_from_cursor = shared_hooks - cursor_hooks
    assert missing_from_cc == set(), f"Shared hooks missing from CC SKILL.md: {missing_from_cc}"
    assert missing_from_cursor == set(), (
        f"Shared hooks missing from Cursor SKILL.md: {missing_from_cursor}"
    )

    # Platform-specific enforcement sets must be non-empty (guards against
    # accidental deletion of the whole enforcement strategy on either side)
    cc_enforcement = {h for h in cc_hooks if h.startswith("enforce-") and h != "enforce-git.sh"
                      and h != "enforce-pipeline-activation.sh" and h != "enforce-sequencing.sh"}
    cursor_enforcement = {h for h in cursor_hooks if h.startswith("enforce-") and h != "enforce-git.sh"
                          and h != "enforce-pipeline-activation.sh" and h != "enforce-sequencing.sh"}
    assert cc_enforcement, "CC SKILL.md has no platform-specific enforcement hooks"
    assert cursor_enforcement, "Cursor SKILL.md has no platform-specific enforcement hooks"
