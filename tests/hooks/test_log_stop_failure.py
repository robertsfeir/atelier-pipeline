"""Tests for ADR-0020 Step 4: StopFailure error tracking hook. Covers T-0020-051 through T-0020-063."""

import json
import re
import subprocess

from conftest import (
    PROJECT_ROOT,
    build_stop_failure_input,
    build_stop_failure_input_minimal,
    hide_jq_env,
    prepare_hook,
    run_hook_with_project_dir,
    run_hook_without_project_dir,
)


def test_T_0020_051_appends_structured_entry(hook_env):
    (hook_env / "docs" / "pipeline" / "error-patterns.md").write_text("# Error Patterns\n")
    inp = build_stop_failure_input("colby", "rate_limit", "Rate limit exceeded for model claude-opus-4-20250514")
    r = run_hook_with_project_dir("log-stop-failure.sh", inp, hook_env)
    assert r.returncode == 0
    text = (hook_env / "docs" / "pipeline" / "error-patterns.md").read_text()
    assert "StopFailure" in text
    assert "colby" in text
    assert "rate_limit" in text
    assert "Rate limit exceeded" in text


def test_T_0020_052_entry_format(hook_env):
    (hook_env / "docs" / "pipeline" / "error-patterns.md").write_text("# Error Patterns\n")
    inp = build_stop_failure_input("roz", "api_error", "Internal server error")
    r = run_hook_with_project_dir("log-stop-failure.sh", inp, hook_env)
    assert r.returncode == 0
    text = (hook_env / "docs" / "pipeline" / "error-patterns.md").read_text()
    assert re.search(r"### StopFailure: roz at \d{4}-\d{2}-\d{2}", text)
    assert "- Error: api_error" in text
    assert "- Message:" in text


def test_T_0020_053_unwritable_file(hook_env):
    ep = hook_env / "docs" / "pipeline" / "error-patterns.md"
    ep.write_text("# Error Patterns\n")
    ep.chmod(0o444)
    inp = build_stop_failure_input("colby", "rate_limit", "Rate limit exceeded")
    r = run_hook_with_project_dir("log-stop-failure.sh", inp, hook_env)
    assert r.returncode == 0
    ep.chmod(0o644)


def test_T_0020_054_jq_missing_fallback(hook_env):
    (hook_env / "docs" / "pipeline" / "error-patterns.md").write_text("# Error Patterns\n")
    env = hide_jq_env(hook_env)
    env["CLAUDE_PROJECT_DIR"] = str(hook_env)
    inp = build_stop_failure_input("colby", "timeout", "Request timed out")
    hook_path = prepare_hook("log-stop-failure.sh", hook_env)
    r = subprocess.run(["bash", str(hook_path)], input=inp, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, timeout=30)
    assert r.returncode == 0
    assert "StopFailure" in (hook_env / "docs" / "pipeline" / "error-patterns.md").read_text()


def test_T_0020_055_unset_project_dir(hook_env):
    inp = build_stop_failure_input("colby", "rate_limit", "Rate limit exceeded")
    r = run_hook_without_project_dir("log-stop-failure.sh", inp, hook_env)
    assert r.returncode == 0


def test_T_0020_056_creates_file_when_missing(hook_env):
    ep = hook_env / "docs" / "pipeline" / "error-patterns.md"
    ep.unlink(missing_ok=True)
    inp = build_stop_failure_input("colby", "rate_limit", "Rate limit exceeded")
    r = run_hook_with_project_dir("log-stop-failure.sh", inp, hook_env)
    assert r.returncode == 0
    assert ep.exists()
    text = ep.read_text()
    assert "# Error Patterns" in text
    assert "### StopFailure:" in text


def test_T_0020_057_201_char_truncated(hook_env):
    (hook_env / "docs" / "pipeline" / "error-patterns.md").write_text("# Error Patterns\n")
    long_message = "A" * 200 + "B"
    assert len(long_message) == 201
    inp = build_stop_failure_input("colby", "rate_limit", long_message)
    r = run_hook_with_project_dir("log-stop-failure.sh", inp, hook_env)
    assert r.returncode == 0
    text = (hook_env / "docs" / "pipeline" / "error-patterns.md").read_text()
    message_line = [l for l in text.splitlines() if l.startswith("- Message:")][0]
    assert "B" not in message_line
    assert "A" * 100 in message_line


def test_T_0020_058_unknown_defaults(hook_env):
    (hook_env / "docs" / "pipeline" / "error-patterns.md").write_text("# Error Patterns\n")
    inp = build_stop_failure_input_minimal()
    r = run_hook_with_project_dir("log-stop-failure.sh", inp, hook_env)
    assert r.returncode == 0
    text = (hook_env / "docs" / "pipeline" / "error-patterns.md").read_text()
    assert re.search(r"### StopFailure: unknown at", text)
    assert "- Error: unknown" in text
    assert "- Message: unknown" in text


def test_T_0020_059_markdown_special_chars(hook_env):
    (hook_env / "docs" / "pipeline" / "error-patterns.md").write_text("# Error Patterns\n")
    inp = build_stop_failure_input("colby", "parse_error", "Failed to parse `config` at [line 5] | column 3")
    r = run_hook_with_project_dir("log-stop-failure.sh", inp, hook_env)
    assert r.returncode == 0
    text = (hook_env / "docs" / "pipeline" / "error-patterns.md").read_text()
    assert "### StopFailure:" in text
    assert "- Error:" in text
    assert "- Message:" in text
    assert text.count("### StopFailure:") == 1


def test_T_0020_060_two_sections(hook_env):
    (hook_env / "docs" / "pipeline" / "error-patterns.md").write_text("# Error Patterns\n")
    for agent, etype, msg in [("colby", "rate_limit", "First error"), ("roz", "timeout", "Second error")]:
        inp = build_stop_failure_input(agent, etype, msg)
        r = run_hook_with_project_dir("log-stop-failure.sh", inp, hook_env)
        assert r.returncode == 0
    text = (hook_env / "docs" / "pipeline" / "error-patterns.md").read_text()
    assert text.count("### StopFailure:") == 2
    assert "colby" in text
    assert "roz" in text


def test_T_0020_061_settings_json_stop_failure():
    settings = json.loads((PROJECT_ROOT / ".claude" / "settings.json").read_text())
    sf_matchers = settings["hooks"].get("StopFailure", [])
    commands = [h.get("command", "") for m in sf_matchers for h in m.get("hooks", [])]
    assert any("log-stop-failure.sh" in c for c in commands)


def test_T_0020_062_stack_trace_truncated(hook_env):
    (hook_env / "docs" / "pipeline" / "error-patterns.md").write_text("# Error Patterns\n")
    stack_trace = (
        "Error: rate_limit at Object.send (/app/node_modules/anthropic/core.mjs:291:15) "
        "at process.processTicksAndRejections (node:internal/process/task_queues:95:5) "
        "at async AgentRunner.run (/app/src/agent.ts:142:22) "
        "at async Pipeline.executePhase (/app/src/pipeline.ts:88:11) "
        "at async main (/app/src/index.ts:15:3) "
        "internal details: token_count=450000 model=claude-opus-4-20250514 retry_count=3 "
        "last_error_code=429 request_id=req_abc123def456ghi789"
    )
    inp = build_stop_failure_input("colby", "rate_limit", stack_trace)
    r = run_hook_with_project_dir("log-stop-failure.sh", inp, hook_env)
    assert r.returncode == 0
    text = (hook_env / "docs" / "pipeline" / "error-patterns.md").read_text()
    message_line = [l for l in text.splitlines() if l.startswith("- Message:")][0]
    content = message_line.removeprefix("- Message: ")
    assert len(content) <= 200
    assert "request_id" not in message_line
    assert "req_abc123def456" not in message_line


def test_T_0020_063_existing_content_preserved(hook_env):
    ep = hook_env / "docs" / "pipeline" / "error-patterns.md"
    ep.write_text(
        "# Error Patterns\n\n"
        "Existing line one about a previous error.\n"
        "Existing line two about another incident.\n"
        "Existing line three with resolution notes.\n"
    )
    inp = build_stop_failure_input("colby", "rate_limit", "New error occurred")
    r = run_hook_with_project_dir("log-stop-failure.sh", inp, hook_env)
    assert r.returncode == 0
    text = ep.read_text()
    assert "Existing line one about a previous error" in text
    assert "Existing line two about another incident" in text
    assert "Existing line three with resolution notes" in text
    assert "### StopFailure:" in text
    assert "New error occurred" in text
