"""Shared fixtures and helpers for hook tests (migrated from test_helper.bash + adr_0022_helper.bash)."""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

# ── Project Paths ────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HOOKS_DIR = PROJECT_ROOT / "source" / "claude" / "hooks"
SHARED_HOOKS_DIR = PROJECT_ROOT / "source" / "shared" / "hooks"

# Shared library files that must be present alongside any hook that sources them.
# NOTE: pipeline-state-path.sh is intentionally omitted here. When it is present,
# session_state_dir() resolves to ~/.atelier/pipeline/{slug}/{hash}/ — an
# out-of-repo path that test fixtures do not populate. Hooks that source this
# library (post-compact-reinject.sh, session-boot.sh) have a built-in fallback:
#   session_state_dir() { echo "$PROJECT_DIR/docs/pipeline"; }
# which is what test fixtures rely on. Tests for pipeline-state-path.sh itself
# (test_pipeline_state_path.py) source the file directly and do not use prepare_hook.
HOOK_LIB_FILES = ["hook-lib.sh"]

# ADR-0022 directories
SOURCE_DIR = PROJECT_ROOT / "source"
SOURCE_AGENTS = SOURCE_DIR / "agents"
SOURCE_HOOKS = SOURCE_DIR / "hooks"
SOURCE_COMMANDS = SOURCE_DIR / "commands"
SOURCE_REFERENCES = SOURCE_DIR / "references"
SOURCE_PIPELINE = SOURCE_DIR / "pipeline"
SOURCE_RULES = SOURCE_DIR / "rules"
SOURCE_VARIANTS = SOURCE_DIR / "variants"
SOURCE_DASHBOARD = SOURCE_DIR / "dashboard"

SHARED_DIR = SOURCE_DIR / "shared"
CLAUDE_DIR = SOURCE_DIR / "claude"
CURSOR_DIR = SOURCE_DIR / "cursor"

# ── Agent Lists ──────────────────────────────────────────────────────────

AGENTS_12 = [
    "cal", "colby", "roz", "robert", "sable", "ellis",
    "agatha", "investigator", "distillator", "sentinel", "darwin", "deps",
]

HOOK_AGENTS = ["roz", "cal", "colby", "agatha"]
PRODUCER_AGENTS = ["robert-spec", "sable-ux"]
PERMISSION_MODE_AGENTS = ["colby", "cal", "agatha", "ellis"]
READ_ONLY_AGENTS = ["robert", "sable", "investigator", "distillator", "sentinel", "darwin", "deps"]

ALL_HOOK_SCRIPT_NAMES = [
    "enforce-roz-paths.sh",
    "enforce-cal-paths.sh",
    "enforce-colby-paths.sh",
    "enforce-agatha-paths.sh",
    "enforce-product-paths.sh",
    "enforce-ux-paths.sh",
    "enforce-eva-paths.sh",
]


# ── Default Config ───────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "pipeline_state_dir": "docs/pipeline",
    "architecture_dir": "docs/architecture",
    "product_specs_dir": "docs/product",
    "ux_docs_dir": "docs/ux",
    "colby_blocked_paths": [
        "docs/",
        ".github/",
        ".gitlab-ci",
        ".circleci/",
        "Jenkinsfile",
        "Dockerfile",
        "docker-compose",
        ".gitlab/",
        "deploy/",
        "infra/",
        "terraform/",
        "pulumi/",
        "k8s/",
        "kubernetes/",
    ],
    "test_command": "",
    "test_patterns": [
        ".test.",
        ".spec.",
        "/tests/",
        "/__tests__/",
        "/test_",
        "_test.",
        "conftest",
    ],
}

SIMPLIFIED_CONFIG = {
    "pipeline_state_dir": "docs/pipeline",
    "colby_blocked_paths": [
        "docs/",
        ".github/",
        ".gitlab-ci",
        ".circleci/",
        "Jenkinsfile",
        "Dockerfile",
        "docker-compose",
        ".gitlab/",
        "deploy/",
        "infra/",
        "terraform/",
        "pulumi/",
        "k8s/",
        "kubernetes/",
    ],
    "test_command": "",
    "test_patterns": [
        ".test.",
        ".spec.",
        "/tests/",
        "/__tests__/",
        "/test_",
        "_test.",
        "conftest",
    ],
}


# ── JSON Input Builders ─────────────────────────────────────────────────


def build_tool_input(tool_name: str = "Write", file_path: str = "", agent_type: str | None = None) -> str:
    """Build a PreToolUse-style JSON input for Write/Edit/MultiEdit hooks."""
    d: dict = {"tool_name": tool_name, "tool_input": {"file_path": file_path}}
    if agent_type is not None:
        d["agent_type"] = agent_type
    return json.dumps(d, separators=(",", ":"))


def build_agent_input(subagent_type: str = "", agent_id: str | None = None) -> str:
    """Build a PreToolUse-style JSON input for Agent tool (enforce-sequencing)."""
    d: dict = {"tool_name": "Agent", "tool_input": {"subagent_type": subagent_type}}
    if agent_id is not None:
        d["agent_id"] = agent_id
    else:
        # Omit agent_id to match bats behavior (main thread)
        pass
    return json.dumps(d, separators=(",", ":"))


def build_bash_input(
    command: str = "",
    agent_id: str | None = None,
    agent_type: str | None = None,
) -> str:
    """Build a Bash tool input for enforce-git."""
    d: dict = {"tool_name": "Bash", "tool_input": {"command": command}}
    if agent_id is not None:
        d["agent_id"] = agent_id
    if agent_type is not None:
        d["agent_type"] = agent_type
    return json.dumps(d, separators=(",", ":"))


def build_subagent_start_input(agent_type: str = "", agent_id: str = "", session_id: str = "") -> str:
    """Build a SubagentStart-style JSON input."""
    return json.dumps({"agent_type": agent_type, "agent_id": agent_id, "session_id": session_id}, separators=(",", ":"))


def build_subagent_stop_input(
    agent_type: str = "",
    agent_id: str = "",
    session_id: str = "",
    last_message: str | None = "__UNSET__",
) -> str:
    """Build a SubagentStop-style JSON input.

    Pass None for null last_assistant_message.
    Pass "__UNSET__" (default) to omit the key entirely.
    Pass "" for empty string.
    """
    d: dict = {"agent_type": agent_type, "agent_id": agent_id, "session_id": session_id}
    if last_message == "__UNSET__":
        pass  # no key
    elif last_message is None:
        d["last_assistant_message"] = None
    else:
        d["last_assistant_message"] = last_message
    return json.dumps(d, separators=(",", ":"))


def build_stop_failure_input(agent_type: str = "", error_type: str = "", error_message: str = "") -> str:
    """Build a StopFailure-style JSON input."""
    return json.dumps({"agent_type": agent_type, "error_type": error_type, "error_message": error_message}, separators=(",", ":"))


def build_stop_failure_input_minimal() -> str:
    """Build a StopFailure-style JSON input with missing fields."""
    return json.dumps({}, separators=(",", ":"))


def build_per_agent_input(tool_name: str = "Write", file_path: str = "") -> str:
    """Build a per-agent hook JSON input (no agent_type -- implicit from hook)."""
    return json.dumps({"tool_name": tool_name, "tool_input": {"file_path": file_path}}, separators=(",", ":"))


# ── Hook Runners ─────────────────────────────────────────────────────────


def prepare_hook(hook_name: str, tmp_path: Path) -> Path:
    """Copy a hook script to tmp_path/.claude/hooks/ and set up config alongside it.

    Also copies hook-lib.sh and pipeline-state-path.sh so hooks that source
    them via SCRIPT_DIR resolve correctly in the isolated temp directory.

    Returns the path to the hook in tmp_path/.claude/hooks/.
    """
    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    src = HOOKS_DIR / hook_name
    dst = hooks_dir / hook_name
    shutil.copy2(src, dst)
    # Also copy directly to root for backward compat
    shutil.copy2(src, tmp_path / hook_name)
    # Copy shared library files so SCRIPT_DIR-relative sourcing works
    for lib_name in HOOK_LIB_FILES:
        lib_src = SHARED_HOOKS_DIR / lib_name
        if lib_src.exists():
            shutil.copy2(lib_src, hooks_dir / lib_name)
            shutil.copy2(lib_src, tmp_path / lib_name)
    # Copy enforcement-config.json if present
    config_src = tmp_path / "enforcement-config.json"
    if config_src.exists():
        shutil.copy2(config_src, hooks_dir / "enforcement-config.json")
    return dst


def run_hook(hook_name: str, input_json: str, tmp_path: Path, env_override: dict | None = None) -> subprocess.CompletedProcess:
    """Run a stdin-based hook with JSON piped in.

    Copies the hook to tmp_path/.claude/hooks/ and runs it.
    Returns CompletedProcess with returncode. stdout contains combined
    stdout+stderr (matching bats `run` behavior where $output has both).

    Strips CLAUDE_PROJECT_DIR and CURSOR_PROJECT_DIR from the base environment
    to prevent ambient env-var leakage from the developer's shell from causing
    session_state_dir() to resolve to an out-of-repo ~/.atelier path where
    test fixture files do not exist.  Tests that explicitly need one of those
    vars set must use run_hook_with_project_dir() or pass env_override directly.
    """
    hook_path = prepare_hook(hook_name, tmp_path)
    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("CURSOR_PROJECT_DIR", None)
    if env_override:
        env.update(env_override)
    r = subprocess.run(
        ["bash", str(hook_path)],
        input=input_json,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        timeout=30,
    )
    return r


def run_hook_with_project_dir(hook_name: str, input_json: str, tmp_path: Path) -> subprocess.CompletedProcess:
    """Run a hook with CLAUDE_PROJECT_DIR set to tmp_path."""
    return run_hook(hook_name, input_json, tmp_path, env_override={"CLAUDE_PROJECT_DIR": str(tmp_path)})


def run_hook_without_project_dir(hook_name: str, input_json: str, tmp_path: Path) -> subprocess.CompletedProcess:
    """Run a hook with CLAUDE_PROJECT_DIR and CURSOR_PROJECT_DIR unset."""
    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("CURSOR_PROJECT_DIR", None)
    hook_path = prepare_hook(hook_name, tmp_path)
    return subprocess.run(
        ["bash", str(hook_path)],
        input=input_json,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        timeout=30,
    )


# ── Per-Agent Hook Runners ──────────────────────────────────────────────


def prepare_per_agent_hook(hook_name: str, tmp_path: Path) -> Path:
    """Prepare a per-agent hook script from source/claude/hooks/.

    Also copies hook-lib.sh and pipeline-state-path.sh so hooks that source
    them via SCRIPT_DIR resolve correctly in the isolated temp directory.
    """
    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_source = CLAUDE_DIR / "hooks" / hook_name
    dst = hooks_dir / hook_name

    if hook_source.exists():
        shutil.copy2(hook_source, dst)
        dst.chmod(dst.stat().st_mode | stat.S_IEXEC)
    else:
        # Script does not exist yet (pre-implementation). Create placeholder.
        dst.write_text('#!/bin/bash\necho "ERROR: Hook script not yet implemented" >&2\nexit 99\n')
        dst.chmod(dst.stat().st_mode | stat.S_IEXEC)

    # Copy shared library files so SCRIPT_DIR-relative sourcing works
    for lib_name in HOOK_LIB_FILES:
        lib_src = SHARED_HOOKS_DIR / lib_name
        if lib_src.exists():
            shutil.copy2(lib_src, hooks_dir / lib_name)

    # Copy enforcement-config.json to the hook dir
    config_src = tmp_path / "enforcement-config.json"
    if config_src.exists():
        shutil.copy2(config_src, hooks_dir / "enforcement-config.json")
    return dst


def run_per_agent_hook(hook_name: str, input_json: str, tmp_path: Path) -> subprocess.CompletedProcess:
    """Run a per-agent hook with JSON input. Combines stdout+stderr."""
    hook_path = prepare_per_agent_hook(hook_name, tmp_path)
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
    return subprocess.run(
        ["bash", str(hook_path)],
        input=input_json,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        timeout=30,
    )


# ── Compact Advisory Hook Runners ───────────────────────────────────────


def prepare_compact_advisory_hook(tmp_path: Path) -> Path:
    """Prepare the prompt-compact-advisory.sh hook for testing.

    Copies hook-lib.sh and pipeline-state-path.sh so SCRIPT_DIR-relative
    sourcing works. pipeline-state-path.sh provides session_state_dir() which
    the hook uses to locate the pipeline state file (ADR-0034 Wave 2).

    When run without CLAUDE_PROJECT_DIR/CURSOR_PROJECT_DIR set and with
    cwd=tmp_path, session_state_dir() returns the relative path "docs/pipeline",
    which resolves to tmp_path/docs/pipeline/ -- exactly where write_pipeline_status
    places the state file.
    """
    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_source = CLAUDE_DIR / "hooks" / "prompt-compact-advisory.sh"
    dst = hooks_dir / "prompt-compact-advisory.sh"

    if hook_source.exists():
        shutil.copy2(hook_source, dst)
        dst.chmod(dst.stat().st_mode | stat.S_IEXEC)
    else:
        dst.write_text('#!/bin/bash\necho "ERROR: Hook script not yet implemented" >&2\nexit 99\n')
        dst.chmod(dst.stat().st_mode | stat.S_IEXEC)

    # Copy hook-lib.sh so hook_lib_pipeline_status_field and hook_lib_get_agent_type
    # are available (ADR-0034 Wave 2 Step 2.1)
    lib_src = SHARED_HOOKS_DIR / "hook-lib.sh"
    if lib_src.exists():
        shutil.copy2(lib_src, hooks_dir / "hook-lib.sh")

    # Copy pipeline-state-path.sh so session_state_dir() resolves correctly
    # (ADR-0034 Wave 2 Fix 4: hook migrated from CLAUDE_PROJECT_DIR to session_state_dir)
    path_src = SHARED_HOOKS_DIR / "pipeline-state-path.sh"
    if path_src.exists():
        shutil.copy2(path_src, hooks_dir / "pipeline-state-path.sh")

    return dst


def run_compact_advisory(input_json: str, tmp_path: Path) -> subprocess.CompletedProcess:
    """Run the compact advisory hook. Combines stdout+stderr.

    Strips CLAUDE_PROJECT_DIR and CURSOR_PROJECT_DIR so session_state_dir()
    falls back to the relative path "docs/pipeline". With cwd=tmp_path, that
    resolves to tmp_path/docs/pipeline/ -- where write_pipeline_status writes
    the state file.
    """
    hook_path = prepare_compact_advisory_hook(tmp_path)
    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("CURSOR_PROJECT_DIR", None)
    return subprocess.run(
        ["bash", str(hook_path)],
        input=input_json,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        cwd=str(tmp_path),
        timeout=30,
    )


# ── Pipeline State Helpers ──────────────────────────────────────────────


def write_pipeline_status(tmp_path: Path, json_str: str) -> None:
    """Write a pipeline-state.md with a PIPELINE_STATUS marker."""
    state_dir = tmp_path / "docs" / "pipeline"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "pipeline-state.md").write_text(
        f"# Pipeline State\n\nSome content here.\n\n<!-- PIPELINE_STATUS: {json_str} -->\n"
    )


def write_pipeline_freeform(tmp_path: Path, text: str) -> None:
    """Write pipeline-state.md with free-form text (no structured marker)."""
    state_dir = tmp_path / "docs" / "pipeline"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "pipeline-state.md").write_text(f"# Pipeline State\n\n{text}\n")


def write_brain_state(tmp_path: Path, available: str) -> None:
    """Write pipeline-state.md with brain availability info."""
    state_dir = tmp_path / "docs" / "pipeline"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "pipeline-state.md").write_text(
        f'# Pipeline State\n\nbrain_available: {available}\n\n<!-- PIPELINE_STATUS: {{"phase":"review","roz_qa":"PASS"}} -->\n'
    )


# ── jq Manipulation ─────────────────────────────────────────────────────


def hide_jq_env(tmp_path: Path) -> dict:
    """Create a modified PATH that excludes jq. Returns an env dict."""
    env = os.environ.copy()
    jq_path = shutil.which("jq")
    if not jq_path:
        return env

    jq_dir = str(Path(jq_path).parent)

    # Create shadow directory
    shadow = tmp_path / "shadow_bin"
    shadow.mkdir(parents=True, exist_ok=True)
    for item in Path(jq_dir).iterdir():
        if item.name == "jq":
            continue
        link = shadow / item.name
        if not link.exists():
            try:
                link.symlink_to(item)
            except OSError:
                pass

    # Replace jq's directory with shadow in PATH
    new_path_parts = []
    for d in env.get("PATH", "").split(":"):
        if d == jq_dir:
            new_path_parts.append(str(shadow))
        else:
            new_path_parts.append(d)
    env["PATH"] = ":".join(new_path_parts)
    return env


# ── Overlay Assembly ────────────────────────────────────────────────────


def assemble_agent(platform: str, agent_name: str, output_path: Path) -> bool:
    """Assemble a complete agent .md file from frontmatter overlay + shared content.

    Returns True on success, False if source files are missing.
    """
    frontmatter = SOURCE_DIR / platform / "agents" / f"{agent_name}.frontmatter.yml"
    content = SHARED_DIR / "agents" / f"{agent_name}.md"

    if not frontmatter.exists() or not content.exists():
        return False

    with open(output_path, "w") as out:
        out.write("---\n")
        out.write(frontmatter.read_text())
        out.write("---\n")
        out.write(content.read_text())
    return True


# ── File Comparison with Placeholder Resolution ─────────────────────────


def compare_with_placeholder_resolution(claude_file: Path, source_file: Path) -> bool:
    """Compare files resolving placeholders in source_file."""
    source_text = source_file.read_text()
    resolved = source_text.replace("{config_dir}", ".claude")
    resolved = resolved.replace("{pipeline_state_dir}", "docs/pipeline")
    resolved = resolved.replace("{architecture_dir}", "docs/architecture")
    resolved = resolved.replace("{product_specs_dir}", "docs/product")
    resolved = resolved.replace("{ux_docs_dir}", "docs/ux")
    resolved = resolved.replace("{features_dir}", "source")
    resolved = resolved.replace("{source_dir}", "source")
    resolved = resolved.replace("{conventions_file}", "docs/CONVENTIONS.md")
    resolved = resolved.replace("{changelog_file}", "CHANGELOG.md")

    return claude_file.read_text() == resolved


# ── Frontmatter Extraction ──────────────────────────────────────────────


def extract_frontmatter(file_path: Path) -> str:
    """Extract YAML frontmatter from a markdown file (between first pair of ---)."""
    lines = file_path.read_text().splitlines()
    in_frontmatter = False
    result = []
    for line in lines:
        if line.strip() == "---":
            if in_frontmatter:
                break  # closing delimiter
            in_frontmatter = True
            continue
        if in_frontmatter:
            result.append(line)
    return "\n".join(result)


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def hook_env(tmp_path):
    """Standard hook test environment: tmp dir with docs/pipeline/ and default config."""
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config_path = tmp_path / "enforcement-config.json"
    config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
    return tmp_path


@pytest.fixture
def simplified_env(tmp_path):
    """Phase 2 simplified environment: no architecture_dir, product_specs_dir, ux_docs_dir."""
    (tmp_path / "docs" / "pipeline").mkdir(parents=True)
    config_path = tmp_path / "enforcement-config.json"
    config_path.write_text(json.dumps(SIMPLIFIED_CONFIG, indent=2))
    return tmp_path
