"""ADR-0022 Phase 2: Legacy test deletion/migration + final verification.
Step 2g. Tests T-0022-160 through T-0022-166."""

import subprocess

from conftest import PROJECT_ROOT


def test_T_0022_160_enforce_paths_bats_deleted():
    assert not (PROJECT_ROOT / "tests" / "hooks" / "enforce-paths.bats").exists()


def test_T_0022_162_doc_sync_updated():
    doc_sync = PROJECT_ROOT / "tests" / "hooks" / "doc-sync.bats"
    if doc_sync.exists():
        text = doc_sync.read_text()
        stale = [
            l for l in text.splitlines()
            if "source/hooks/" in l
            and "source/claude/hooks" not in l
            and "source/cursor/hooks" not in l
            and "source/shared" not in l
        ]
        assert stale == []


def test_T_0022_163_if_conditionals_updated():
    if_cond = PROJECT_ROOT / "tests" / "hooks" / "if-conditionals.bats"
    if if_cond.exists():
        text = if_cond.read_text()
        claude_refs = [
            l for l in text.splitlines()
            if "enforce-paths.sh" in l and "cursor" not in l.lower()
        ]
        assert claude_refs == []


def test_T_0022_164_no_flat_source_hooks():
    result = subprocess.run(
        ["grep", "-rl", "source/hooks/", str(PROJECT_ROOT / "tests" / "hooks")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    stale = [
        l for l in result.stdout.strip().splitlines()
        if "source/claude/hooks" not in l and "source/cursor/hooks" not in l
    ] if result.stdout.strip() else []
    assert stale == []


def test_T_0022_165_no_source_agents():
    result = subprocess.run(
        ["grep", "-rl", "source/agents/",
         str(PROJECT_ROOT / "source"),
         str(PROJECT_ROOT / "tests"),
         str(PROJECT_ROOT / "skills"),
         str(PROJECT_ROOT / "CLAUDE.md"),
         str(PROJECT_ROOT / "README.md"),
         str(PROJECT_ROOT / "docs")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    stale = [
        l for l in result.stdout.strip().splitlines()
        if "ADR-0022" not in l and ".git" not in l
        and "source/shared/agents" not in l and "source/claude/agents" not in l
        and "source/cursor/agents" not in l and "adr-0022-distillate" not in l
    ] if result.stdout.strip() else []
    assert stale == []


def test_T_0022_166_no_source_hooks():
    result = subprocess.run(
        ["grep", "-rl", "source/hooks/",
         str(PROJECT_ROOT / "source"),
         str(PROJECT_ROOT / "tests"),
         str(PROJECT_ROOT / "skills"),
         str(PROJECT_ROOT / "CLAUDE.md"),
         str(PROJECT_ROOT / "README.md"),
         str(PROJECT_ROOT / "docs")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    stale = [
        l for l in result.stdout.strip().splitlines()
        if "ADR-0022" not in l and ".git" not in l
        and "source/cursor/hooks" not in l and "adr-0022-distillate" not in l
    ] if result.stdout.strip() else []
    assert stale == []
