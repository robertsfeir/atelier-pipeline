"""ADR-0015: Predictive Dependency Management Agent (Deps) -- Structural Tests.

Tests: T-0015-001 through T-0015-064 (64 tests).
Migrated from deps-structural.test.bats.
"""

import json
import re

import pytest

from tests.conftest import (
    SOURCE_PIPELINE,
    ALL_AGENTS_12,
    CLAUDE_DIR,
    INSTALLED_AGENTS,
    INSTALLED_COMMANDS,
    INSTALLED_REFS,
    INSTALLED_RULES,
    PROJECT_ROOT,
    SKILL_FILE,
    SOURCE_COMMANDS,
    SOURCE_REFS,
    SOURCE_RULES,
    assert_has_closing_tag,
    assert_has_tag,
    extract_frontmatter,
    extract_tag_content,
    extract_template_section,
    extract_section,
    line_of,
)

# ═══════════════════════════════════════════════════════════════════════
# Step 1: Agent Persona
# ═══════════════════════════════════════════════════════════════════════

def test_T_0015_001_source_files_exist():
    shared = PROJECT_ROOT / "source" / "shared" / "agents" / "deps.md"
    frontmatter = CLAUDE_DIR / "agents" / "deps.frontmatter.yml"
    assert shared.is_file()
    assert frontmatter.is_file()
    assert "name: deps" in frontmatter.read_text()


def test_T_0015_002_installed_copy():
    f = INSTALLED_AGENTS / "deps.md"
    assert f.is_file()
    assert "name: deps" in f.read_text()


def test_T_0015_003_disallowed_tools():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    fm = extract_frontmatter(f)
    assert "Write" in fm
    assert "Edit" in fm
    assert "MultiEdit" in fm


def test_T_0015_004_required_xml_tags():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    for tag in ["identity", "required-actions", "workflow", "examples", "constraints", "output"]:
        assert_has_tag(f, tag)
        assert_has_closing_tag(f, tag)


def test_T_0015_005_examples_tag():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    assert_has_tag(f, "examples")
    assert_has_closing_tag(f, "examples")
    examples = extract_tag_content(f, "examples")
    count = len(re.findall(r"(?i)example|skip.*ecosystem|breakage.*predict|missing.*tool|cargo.*not found|go.*cve", examples))
    assert count >= 2


def test_T_0015_006_tools_section():
    """Tools are enforced via frontmatter disallowedTools, not a <tools> tag (ADR-0023)."""
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    fm = extract_frontmatter(f)
    assert "disallowedTools" in fm, "Missing disallowedTools in frontmatter"
    assert "Write" in fm, "Write should be disallowed"
    assert "Edit" in fm, "Edit should be disallowed"


def test_T_0015_007_workflow_phases():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    wf = extract_tag_content(f, "workflow").lower()
    assert re.search(r"detect|ecosystem|manifest", wf), "Missing detection phase"
    assert re.search(r"scan|outdated|cve|audit", wf), "Missing scan phase"
    assert re.search(r"report|risk|classification", wf), "Missing report phase"


def test_T_0015_008_hang_stop_rule():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    c = extract_tag_content(f, "constraints")
    assert re.search(r"hang.*stop|stop.*do not retry|hang.*do not retry", c, re.IGNORECASE)


def test_T_0015_009_never_modify():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    c = extract_tag_content(f, "constraints")
    assert re.search(r"never.*modify|never.*write|read.only|no.*file.*modif", c, re.IGNORECASE)


def test_T_0015_010_webfetch_degradation():
    """When changelog/WebFetch unavailable, deps uses conservative labeling."""
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    content = f.read_text()
    assert re.search(r"webfetch.*unavailable|webfetch.*degrad|changelog.*unavailable|conservative|uncertain.*needs review|private.*registry|missing.*tool|note.*gap", content, re.IGNORECASE)


def test_T_0015_011_output_risk_sections():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    out = extract_tag_content(f, "output")
    for s in ["CVE", "Needs Review", "Safe to Upgrade", "No Action"]:
        assert re.search(s, out, re.IGNORECASE), f"Missing output section: {s}"


def test_T_0015_012_workflow_edge_cases():
    """Workflow + constraints cover edge cases: no manifest, missing tools, monorepo, private registry."""
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    content = f.read_text()  # Check full file, not just workflow
    assert re.search(r"no manifest|manifest.*not found|no.*dependency|no.*manifests", content, re.IGNORECASE)
    assert re.search(r"missing.*tool|tool.*not found|not.*installed|[Mm]issing tool", content, re.IGNORECASE)
    assert re.search(r"monorepo|multiple.*manifest|workspace|monorepos", content, re.IGNORECASE)
    assert re.search(r"private.*registry|private.*repo|auth", content, re.IGNORECASE)


def test_T_0015_013_bash_whitelist_blocklist():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    c = extract_tag_content(f, "constraints")
    for cmd in ["npm outdated", "npm audit", "pip-audit", "cargo audit", "cargo outdated", "go list"]:
        assert re.search(cmd, c, re.IGNORECASE), f"Missing whitelisted: {cmd}"
    for cmd in ["npm install", "pip install", "cargo update", "go get"]:
        assert re.search(cmd, c, re.IGNORECASE), f"Missing blocklisted: {cmd}"


def test_T_0015_014_go_no_audit():
    """Go has no standard audit tool -- noted in workflow or constraints."""
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    content = f.read_text()
    assert re.search(r"go.*no.*audit|go.*cve.*unavailable|no.*go.*audit|go.*cve.*omit|Go.*no standard tool|note gap", content, re.IGNORECASE)


def test_T_0015_015_no_write_in_tools():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    tools = extract_tag_content(f, "tools")
    assert not re.search(r"^\s*[-*].*\bWrite\b", tools, re.MULTILINE)


def test_T_0015_016_no_edit_in_tools():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    tools = extract_tag_content(f, "tools")
    assert not re.search(r"^\s*[-*].*\bEdit\b", tools, re.MULTILINE)


def test_T_0015_017_disallowed_write():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    fm = extract_frontmatter(f)
    assert "disallowedTools" in fm
    assert "Write" in fm


def test_T_0015_018_disallowed_edit():
    f = INSTALLED_AGENTS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md not yet created")
    fm = extract_frontmatter(f)
    assert "disallowedTools" in fm
    assert "Edit" in fm


def test_T_0015_019_not_in_core_constant():
    content = (INSTALLED_RULES / "agent-system.md").read_text()
    core = re.search(r"cal, colby.*distillator", content)
    if core:
        assert "deps" not in core.group(0)


def test_T_0015_020_core_code_block_no_deps():
    content = (INSTALLED_RULES / "agent-system.md").read_text()
    blocks = re.findall(r"```.*?```", content, re.DOTALL)
    for block in blocks:
        if "cal" in block and "colby" in block and "roz" in block:
            assert "deps" not in block


# ═══════════════════════════════════════════════════════════════════════
# Step 2: Slash Command
# ═══════════════════════════════════════════════════════════════════════

def test_T_0015_021_source_command():
    f = SOURCE_COMMANDS / "deps.md"
    assert f.is_file()
    # Frontmatter is in the overlay, not the shared body (post ADR-0022 split)
    overlay = CLAUDE_DIR / "commands" / "deps.frontmatter.yml"
    assert overlay.is_file()
    assert "name: deps" in overlay.read_text()


def test_T_0015_022_installed_command_identical():
    # Installed is assembled from overlay + shared body; verify key content is present
    inst = INSTALLED_COMMANDS / "deps.md"
    src_body = SOURCE_COMMANDS / "deps.md"
    assert inst.is_file() and src_body.is_file()
    inst_text = inst.read_text()
    # The installed version should have YAML frontmatter and contain key content from shared body
    assert inst_text.startswith("---")
    assert "deps" in inst_text
    # Verify a key section from shared body appears in the installed version
    assert "<identity>" in src_body.read_text()
    assert "<identity>" in inst_text


def test_T_0015_023_scan_and_report():
    f = INSTALLED_COMMANDS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md command not yet created")
    c = f.read_text()
    assert re.search(r"deps_agent_enabled|scan|report", c, re.IGNORECASE)


def test_T_0015_024_migration_brief():
    f = INSTALLED_COMMANDS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md command not yet created")
    assert re.search(r"migration.*adr|migration.*brief|cal", f.read_text(), re.IGNORECASE)


def test_T_0015_025_enabled_gate():
    f = INSTALLED_COMMANDS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md command not yet created")
    assert re.search(r"deps_agent_enabled.*false|not enabled|not.*enabled", f.read_text(), re.IGNORECASE)


def test_T_0015_026_structured_format():
    f = INSTALLED_COMMANDS / "deps.md"
    if not f.is_file(): pytest.skip("deps.md command not yet created")
    assert f.read_text().splitlines()[0].startswith("---")


# ═══════════════════════════════════════════════════════════════════════
# Step 3: Config Flag
# ═══════════════════════════════════════════════════════════════════════

def test_T_0015_027_source_config():
    f = SOURCE_PIPELINE / "pipeline-config.json"
    data = json.loads(f.read_text())
    assert data["deps_agent_enabled"] is False


def test_T_0015_028_installed_config():
    f = PROJECT_ROOT / ".claude" / "pipeline-config.json"
    data = json.loads(f.read_text())
    assert data["deps_agent_enabled"] is False


def test_T_0015_029_valid_json():
    json.loads((SOURCE_PIPELINE / "pipeline-config.json").read_text())
    json.loads((PROJECT_ROOT / ".claude" / "pipeline-config.json").read_text())


def test_T_0015_030_no_fields_removed():
    data = json.loads((SOURCE_PIPELINE / "pipeline-config.json").read_text())
    for field in ["branching_strategy", "platform", "sentinel_enabled", "agent_teams_enabled",
                   "ci_watch_enabled", "ci_watch_max_retries", "ci_watch_poll_command", "ci_watch_log_command"]:
        assert field in data, f"Missing existing field: {field}"


def test_T_0015_031_boolean_fields_unchanged():
    data = json.loads((SOURCE_PIPELINE / "pipeline-config.json").read_text())
    assert data["sentinel_enabled"] is False
    assert data["agent_teams_enabled"] is False
    assert data["ci_watch_enabled"] is False


# ═══════════════════════════════════════════════════════════════════════
# Step 4: Auto-Routing
# ═══════════════════════════════════════════════════════════════════════

def test_T_0015_032_source_subagent_table():
    assert "**Deps**" in (SOURCE_RULES / "agent-system.md").read_text()


def test_T_0015_033_installed_subagent_table():
    assert "**Deps**" in (INSTALLED_RULES / "agent-system.md").read_text()


def test_T_0015_034_auto_routing_deps():
    for f in [SOURCE_RULES / "agent-system.md", INSTALLED_RULES / "agent-system.md"]:
        c = f.read_text()
        assert re.search(r"Deps", c) and re.search(r"dependenc|outdated|upgrade|cve|vulnerability", c, re.IGNORECASE)
        assert re.search(r"\|.*[Dd]eps.*\|", c)


def test_T_0015_035_deps_agent_enabled_gate():
    assert "deps_agent_enabled" in (INSTALLED_RULES / "agent-system.md").read_text()


def test_T_0015_036_no_skill_tool_gate():
    for f in [SOURCE_RULES / "agent-system.md", INSTALLED_RULES / "agent-system.md"]:
        assert re.search(r"deps.*\.claude/agents/deps\.md|deps\.md", f.read_text(), re.IGNORECASE)


def test_T_0015_037_routing_documents_gate():
    assert "deps_agent_enabled" in (INSTALLED_RULES / "agent-system.md").read_text()


def test_T_0015_038_subagent_tools_list():
    content = (INSTALLED_RULES / "agent-system.md").read_text()
    row = [l for l in content.splitlines() if re.search(r"\*\*Deps\*\*", l)]
    assert row, "Deps subagent row not found"
    r = row[0]
    for tool in ["Read", "Glob", "Grep", "Bash", "WebSearch", "WebFetch"]:
        assert tool in r, f"Missing {tool} in Deps row"


def test_T_0015_039_sentinel_unchanged():
    c = (INSTALLED_RULES / "agent-system.md").read_text()
    assert "**Sentinel**" in c
    assert re.search(r"Sentinel.*security.*audit|Sentinel.*Semgrep", c, re.IGNORECASE)


def test_T_0015_040_core_constant_no_deps():
    c = (INSTALLED_RULES / "agent-system.md").read_text()
    line = [l for l in c.splitlines() if "cal, colby, roz" in l]
    if line:
        assert "deps" not in line[0]


# ═══════════════════════════════════════════════════════════════════════
# Step 5: Invocation Templates
# ═══════════════════════════════════════════════════════════════════════

def test_T_0015_041_source_deps_scan():
    assert '<template id="deps-scan">' in (SOURCE_REFS / "invocation-templates.md").read_text()


def test_T_0015_042_installed_deps_scan():
    assert '<template id="deps-scan">' in (INSTALLED_REFS / "invocation-templates.md").read_text()


def test_T_0015_043_deps_scan_tags():
    t = extract_template_section(INSTALLED_REFS / "invocation-templates.md", "deps-scan")
    assert t, "deps-scan template not found"
    assert "<task>" in t
    assert "<constraints>" in t
    assert "<output>" in t


def test_T_0015_044_deps_scan_constraints():
    t = extract_template_section(INSTALLED_REFS / "invocation-templates.md", "deps-scan")
    assert t
    assert re.search(r"skip.*missing|missing.*ecosystem", t, re.IGNORECASE)
    assert re.search(r"conservative|changelog|breaking", t, re.IGNORECASE)
    assert re.search(r"hang|stop", t, re.IGNORECASE)
    assert re.search(r"no.*modif|never.*modif|read.only", t, re.IGNORECASE)


def test_T_0015_045_deps_scan_output():
    t = extract_template_section(INSTALLED_REFS / "invocation-templates.md", "deps-scan")
    assert t
    assert re.search(r"CVE|risk|section", t, re.IGNORECASE)
    assert re.search(r"DoR|DoD", t, re.IGNORECASE)


def test_T_0015_046_migration_brief_template():
    for f in [SOURCE_REFS / "invocation-templates.md", INSTALLED_REFS / "invocation-templates.md"]:
        assert '<template id="deps-migration-brief">' in f.read_text()


def test_T_0015_047_migration_brief_single_package():
    t = extract_template_section(INSTALLED_REFS / "invocation-templates.md", "deps-migration-brief")
    assert t
    assert re.search(r"single.*package|named.*package|specific.*package|package.*name", t, re.IGNORECASE)


def test_T_0015_048_migration_brief_output():
    t = extract_template_section(INSTALLED_REFS / "invocation-templates.md", "deps-migration-brief")
    assert t
    assert re.search(r"breaking.*change", t, re.IGNORECASE)
    assert re.search(r"usage.*inventory|file.*line", t, re.IGNORECASE)
    assert re.search(r"migration.*approach", t, re.IGNORECASE)
    assert re.search(r"effort|estimate", t, re.IGNORECASE)


def test_T_0015_049_existing_templates_unchanged():
    for f in [SOURCE_REFS / "invocation-templates.md", INSTALLED_REFS / "invocation-templates.md"]:
        assert "sentinel-audit" in f.read_text()


# ═══════════════════════════════════════════════════════════════════════
# Step 6: Setup Step 6d
# ═══════════════════════════════════════════════════════════════════════

def _step6d():
    c = SKILL_FILE.read_text()
    return extract_section(c, r"[Ss]tep 6d", r"[Ss]tep 6e|[Ss]tep 7|[Bb]rain")


def test_T_0015_050_step_6d_exists():
    assert re.search(r"step 6d|### 6d|## Step 6d", SKILL_FILE.read_text(), re.IGNORECASE)


def test_T_0015_051_step_6d_position():
    c = SKILL_FILE.read_text()
    l6c = line_of(SKILL_FILE, r"(?i)step 6c|### 6c|## Step 6c")
    l6d = line_of(SKILL_FILE, r"(?i)step 6d|### 6d|## Step 6d")
    l_brain = line_of(SKILL_FILE, r"(?i)brain.*setup|brain.*offer|connect.*brain")
    assert l6c and l6d and l_brain
    assert l6c < l6d < l_brain


def test_T_0015_052_step_6d_offer_text():
    s = _step6d()
    assert s
    assert re.search(r"CVE|vulnerabilit", s, re.IGNORECASE)
    assert re.search(r"outdated|upgrade", s, re.IGNORECASE)
    assert re.search(r"breakage|breaking|risk", s, re.IGNORECASE)


def test_T_0015_053_step_6d_yes_path():
    s = _step6d()
    assert s
    assert re.search(r"deps_agent_enabled.*true|set.*deps.*true", s, re.IGNORECASE)


def test_T_0015_054_step_6d_copies_agent():
    s = _step6d()
    assert s
    assert re.search(r"deps\.md|agents/deps", s, re.IGNORECASE)


def test_T_0015_055_step_6d_copies_command():
    s = _step6d()
    assert s
    assert re.search(r"commands/deps|command.*deps", s, re.IGNORECASE)


def test_T_0015_056_step_6d_no_path():
    s = _step6d()
    assert s
    assert re.search(r"not enabled|skip|decline", s, re.IGNORECASE)


def test_T_0015_057_summary_line():
    assert re.search(r"deps.*agent.*enabled|deps.*agent.*not.*enabled|deps.*enabled|deps.*not enabled",
                     SKILL_FILE.read_text(), re.IGNORECASE)


def test_T_0015_058_absent_key_false():
    s = _step6d()
    assert s
    assert re.search(r"absent.*false|missing.*false|not.*present.*false|default.*false", s, re.IGNORECASE)


def test_T_0015_059_idempotency_enabled():
    s = _step6d()
    assert s
    assert re.search(r"already.*enabled|idempoten|skip.*mutation", s, re.IGNORECASE)


def test_T_0015_060_idempotency_disabled():
    s = _step6d()
    assert s
    assert re.search(r"ask|offer|enable|want|would you like", s, re.IGNORECASE)


def test_T_0015_061_sentinel_unchanged():
    c = SKILL_FILE.read_text()
    assert re.search(r"step 6a|sentinel", c, re.IGNORECASE)
    assert "sentinel_enabled" in c


def test_T_0015_062_agent_teams_unchanged():
    c = SKILL_FILE.read_text()
    assert re.search(r"step 6b|agent.teams", c, re.IGNORECASE)
    assert "agent_teams_enabled" in c


def test_T_0015_063_ci_watch_unchanged():
    c = SKILL_FILE.read_text()
    assert re.search(r"step 6c|ci.watch", c, re.IGNORECASE)
    assert "ci_watch_enabled" in c


def test_T_0015_064_brain_after_6d():
    l6d = line_of(SKILL_FILE, r"(?i)step 6d|### 6d")
    l_brain = line_of(SKILL_FILE, r"(?i)brain.*setup|brain.*offer|connect.*brain")
    assert l6d and l_brain
    assert l6d < l_brain
