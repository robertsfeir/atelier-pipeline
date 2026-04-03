"""Tests for ADR-0020 Step 5: Documentation and file sync. Covers T-0020-064 through T-0020-069."""

import re
import subprocess

from conftest import PROJECT_ROOT


def test_T_0020_064_technical_reference_all_hooks():
    doc = (PROJECT_ROOT / "docs" / "guide" / "technical-reference.md").read_text()
    for hook in [
        "enforce-paths.sh", "enforce-sequencing.sh", "enforce-pipeline-activation.sh",
        "enforce-git.sh", "warn-dor-dod.sh", "pre-compact.sh",
        "log-agent-start.sh", "log-agent-stop.sh", "post-compact-reinject.sh", "log-stop-failure.sh",
    ]:
        assert hook in doc
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
    cc_skill = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"
    cursor_skill = PROJECT_ROOT / ".cursor-plugin" / "skills" / "pipeline-setup" / "SKILL.md"
    assert cc_skill.exists()
    assert cursor_skill.exists()
    cursor_hooks = set(re.findall(r"[a-z]+-[a-z-]+\.sh", cursor_skill.read_text()))
    cc_hooks = set(re.findall(r"[a-z]+-[a-z-]+\.sh", cc_skill.read_text()))
    divergent = cursor_hooks - cc_hooks
    assert divergent == set(), f"Cursor hooks not in CC: {divergent}"


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
    cc_skill = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"
    cursor_skill = PROJECT_ROOT / ".cursor-plugin" / "skills" / "pipeline-setup" / "SKILL.md"
    cc_hooks = sorted(set(re.findall(r"[a-z]+-[a-z-]+\.sh", cc_skill.read_text())))
    cursor_hooks = sorted(set(re.findall(r"[a-z]+-[a-z-]+\.sh", cursor_skill.read_text())))
    assert cc_hooks == cursor_hooks
