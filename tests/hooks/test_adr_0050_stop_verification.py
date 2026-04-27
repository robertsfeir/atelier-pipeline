"""Tests for ADR-0050: Colby SubagentStop verification hook.

Falsifiability cases per ADR-0050 §Falsifiability:
  1. agent_type=colby + failing typecheck stub → exit 2 + non-empty stderr
  2. agent_type=sarah → exit 0, no command invoked
  3. verify_commands absent from pipeline-config.json → exit 0

Regression case (Poirot F1, the FAILURE-only counter rule):
  4. Three consecutive successful typecheck invocations for the same
     session_id, then a 4th failing invocation → 4th still exits 2
     (the counter must reset on each success, never accumulate on
     successes; only failures count toward verify_max_attempts).
"""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_SOURCE = PROJECT_ROOT / "source" / "claude" / "hooks" / "enforce-colby-stop-verify.sh"
SHARED_HOOKS_DIR = PROJECT_ROOT / "source" / "shared" / "hooks"
HOOK_LIB_FILES = ["hook-lib.sh"]


def _prepare_env(tmp_path: Path, pipeline_config: dict | None) -> Path:
    """Set up an isolated CLAUDE_PROJECT_DIR with the hook + pipeline-config.json."""
    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    dst = hooks_dir / "enforce-colby-stop-verify.sh"
    shutil.copy2(HOOK_SOURCE, dst)
    dst.chmod(dst.stat().st_mode | stat.S_IEXEC)

    # Copy shared library files so the hook's SCRIPT_DIR-relative source resolves
    # in the isolated tmp env (mirrors conftest.prepare_hook's HOOK_LIB_FILES loop).
    for lib_name in HOOK_LIB_FILES:
        lib_src = SHARED_HOOKS_DIR / lib_name
        if lib_src.exists():
            shutil.copy2(lib_src, hooks_dir / lib_name)

    (tmp_path / "docs" / "pipeline").mkdir(parents=True, exist_ok=True)

    if pipeline_config is not None:
        (tmp_path / ".claude" / "pipeline-config.json").write_text(
            json.dumps(pipeline_config, indent=2)
        )

    return dst


def _build_stdin(agent_type: str, session_id: str = "session-test-0050") -> str:
    return json.dumps(
        {
            "agent_type": agent_type,
            "agent_id": "agent-test",
            "session_id": session_id,
        },
        separators=(",", ":"),
    )


def _run(hook_path: Path, stdin: str, project_dir: Path, extra_path: str | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env.pop("CURSOR_PROJECT_DIR", None)
    if extra_path:
        env["PATH"] = f"{extra_path}:{env.get('PATH', '')}"
    return subprocess.run(
        ["bash", str(hook_path)],
        input=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        timeout=30,
    )


# ── Test 1: Colby + failing typecheck → exit 2 with stderr ────────────


def test_adr_0050_colby_typecheck_failure_exits_2(tmp_path):
    """Colby stop with a typechecker that exits 1 → hook exits 2 with non-empty stderr."""
    # Stub typecheck command: a script that prints and exits 1.
    stub_dir = tmp_path / "stubs"
    stub_dir.mkdir()
    typecheck_stub = stub_dir / "fake-typecheck"
    typecheck_stub.write_text("#!/bin/bash\necho 'error: type mismatch on line 42' >&2\nexit 1\n")
    typecheck_stub.chmod(0o755)

    hook = _prepare_env(
        tmp_path,
        {
            "verify_commands": {
                "typecheck": str(typecheck_stub),
            }
        },
    )
    r = _run(hook, _build_stdin("colby"), tmp_path)

    assert r.returncode == 2, f"Expected exit 2, got {r.returncode}. stdout={r.stdout!r} stderr={r.stderr!r}"
    assert r.stderr.strip() != "", "Expected non-empty stderr on typecheck failure"
    assert "type mismatch" in r.stderr or "BLOCKED" in r.stderr


# ── Test 2: agent_type=sarah → exit 0, no command invoked ─────────────


def test_adr_0050_non_colby_agent_skips_verification(tmp_path):
    """Sarah stop → hook exits 0 immediately; verify commands are NOT invoked."""
    # Sentinel file: if the typecheck command runs, it creates this file.
    # If the file exists after the hook runs, the gate failed.
    sentinel = tmp_path / "typecheck-was-invoked"
    stub_dir = tmp_path / "stubs"
    stub_dir.mkdir()
    typecheck_stub = stub_dir / "fake-typecheck"
    typecheck_stub.write_text(f"#!/bin/bash\ntouch '{sentinel}'\nexit 1\n")
    typecheck_stub.chmod(0o755)

    hook = _prepare_env(
        tmp_path,
        {
            "verify_commands": {
                "typecheck": str(typecheck_stub),
            }
        },
    )
    r = _run(hook, _build_stdin("sarah"), tmp_path)

    assert r.returncode == 0, f"Expected exit 0 for non-Colby agent, got {r.returncode}. stderr={r.stderr!r}"
    assert not sentinel.exists(), "Typecheck stub should NOT have been invoked for agent_type=sarah"


# ── Test 3: verify_commands absent → exit 0 ───────────────────────────


def test_adr_0050_missing_verify_commands_exits_0(tmp_path):
    """pipeline-config.json without verify_commands key → hook exits 0 silently."""
    hook = _prepare_env(
        tmp_path,
        {
            "project_name": "test-project",
            # No verify_commands key at all -- not opted in.
        },
    )
    r = _run(hook, _build_stdin("colby"), tmp_path)

    assert r.returncode == 0, (
        f"Expected exit 0 when verify_commands is absent, got {r.returncode}. "
        f"stdout={r.stdout!r} stderr={r.stderr!r}"
    )


# ── Test 4 (Poirot F1 regression): successes must reset the counter ───


def test_adr_0050_successful_typechecks_do_not_accumulate(tmp_path):
    """Three clean Colby stops then a failing one in the same session → 4th still exits 2.

    Regression for Poirot finding F1: the per-session counter previously
    incremented on every Colby stop, including successful ones. With
    verify_max_attempts=3 that meant the 4th invocation in any long-running
    session was silently skipped regardless of whether typecheck passed or
    failed. The fix increments only on failure and deletes the counter on
    success; this test pins that contract.
    """
    # Unique session_id so we can't possibly inherit state from other tests.
    session_id = "session-test-0050-f1-regression"

    stub_dir = tmp_path / "stubs"
    stub_dir.mkdir()

    pass_stub = stub_dir / "fake-typecheck-pass"
    pass_stub.write_text("#!/bin/bash\nexit 0\n")
    pass_stub.chmod(0o755)

    fail_stub = stub_dir / "fake-typecheck-fail"
    fail_stub.write_text("#!/bin/bash\necho 'error: simulated type error' >&2\nexit 1\n")
    fail_stub.chmod(0o755)

    config_path = tmp_path / ".claude" / "pipeline-config.json"
    counter_file = tmp_path / "docs" / "pipeline" / f".colby-verify-attempts-{session_id}"

    # Install the hook with the passing typecheck stub configured.
    hook = _prepare_env(
        tmp_path,
        {"verify_commands": {"typecheck": str(pass_stub)}},
    )

    # Three consecutive successful invocations -- each must exit 0 and leave
    # no counter file behind (the success branch deletes it).
    for attempt in range(1, 4):
        r = _run(hook, _build_stdin("colby", session_id=session_id), tmp_path)
        assert r.returncode == 0, (
            f"Attempt {attempt}: expected clean exit 0, got {r.returncode}. "
            f"stderr={r.stderr!r}"
        )
        assert not counter_file.exists(), (
            f"Attempt {attempt}: counter file should not exist after a successful "
            f"typecheck (success must delete it), but found {counter_file}"
        )

    # Swap the config to point at the failing stub and invoke a 4th time.
    # If successes had been incrementing the counter, CURRENT would already be
    # 3 == verify_max_attempts on entry and the hook would skip with exit 0.
    # With the F1 fix, CURRENT is 0 (no file), so the typecheck still runs
    # and fails → exit 2.
    config_path.write_text(
        json.dumps({"verify_commands": {"typecheck": str(fail_stub)}}, indent=2)
    )
    r = _run(hook, _build_stdin("colby", session_id=session_id), tmp_path)
    assert r.returncode == 2, (
        f"4th invocation (now failing) must still run typecheck and exit 2, "
        f"got {r.returncode}. If this returned 0 with a 'verify_max_attempts "
        f"reached' warning on stderr, F1 has regressed -- successes are "
        f"incrementing the counter again. stderr={r.stderr!r}"
    )
    assert counter_file.exists(), (
        "After a failing typecheck the counter file must exist (failure increments)."
    )
    assert counter_file.read_text().strip() == "1", (
        "First failure after three successes must record CURRENT=0 → NEXT=1, "
        f"but counter file contains {counter_file.read_text()!r}"
    )
