"""Behavioral tests for ADR-0060: Configurable Agent Roster.

Two behavioral contracts (per ADR):
1. Absent agent never blocks -- roster-aware skip must work for every gated agent.
2. Ellis-absent commit flow -- generic_commit_enabled flag is set correctly by roster.

These tests exercise enforce-sequencing.sh and enforce-brain-capture-pending.sh
against pipeline-config.json rosters that include and exclude each gated agent.
"""

import json
import shutil
from pathlib import Path

import pytest

from conftest import (
    HOOKS_DIR,
    SHARED_HOOKS_DIR,
    build_agent_input,
    write_pipeline_status,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def write_enforcement_config(tmp_path: Path) -> None:
    """Write the enforcement-config.json expected by enforce-sequencing.sh."""
    (tmp_path / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    config = {
        "pipeline_state_dir": "docs/pipeline",
        "colby_blocked_paths": ["docs/", ".claude/"],
    }
    (tmp_path / ".claude" / "hooks" / "enforcement-config.json").write_text(
        json.dumps(config)
    )


def write_pipeline_config(tmp_path: Path, roster: dict, generic_commit: bool = True) -> None:
    """Write .claude/pipeline-config.json with the given roster."""
    (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
    config = {
        "project_name": "test-project",
        "agent_roster": roster,
        "generic_commit_enabled": generic_commit,
    }
    (tmp_path / ".claude" / "pipeline-config.json").write_text(json.dumps(config))


def prepare_sequencing_hook(tmp_path: Path) -> Path:
    """Copy enforce-sequencing.sh and all dependencies to tmp_path."""
    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    src = HOOKS_DIR / "enforce-sequencing.sh"
    dst = hooks_dir / "enforce-sequencing.sh"
    shutil.copy2(src, dst)

    # Copy hook-lib.sh
    lib_src = SHARED_HOOKS_DIR / "hook-lib.sh"
    if lib_src.exists():
        shutil.copy2(lib_src, hooks_dir / "hook-lib.sh")

    write_enforcement_config(tmp_path)
    return dst


def run_sequencing(tmp_path: Path, subagent_type: str) -> int:
    """Run enforce-sequencing.sh for the given subagent_type. Returns exit code."""
    import os
    import subprocess

    hook_path = prepare_sequencing_hook(tmp_path)
    input_json = build_agent_input(subagent_type=subagent_type)
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
    env.pop("CURSOR_PROJECT_DIR", None)
    r = subprocess.run(
        ["bash", str(hook_path)],
        input=input_json,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        timeout=30,
    )
    return r.returncode


# ── Roster: minimal (Robert/Sarah/Colby only) ─────────────────────────────

MINIMAL_ROSTER = {
    "robert": {"enabled": True, "firing": "core"},
    "sarah": {"enabled": True, "firing": "core"},
    "colby": {"enabled": True, "firing": "core"},
}


# ── Contract 1: Absent agent never blocks ──────────────────────────────────


class TestAbsentAgentNeverBlocks:
    """All gated agents must exit 0 when absent from the roster during an active pipeline."""

    def _setup_active_pipeline(self, tmp_path: Path, roster: dict) -> None:
        """Write an active pipeline state and roster config."""
        write_pipeline_status(
            tmp_path,
            '{"phase":"build","sizing":"small","qa_status":"PENDING",'
            '"poirot_reviewed":"false","ci_watch_active":"false","feature":"feat"}',
        )
        write_pipeline_config(tmp_path, roster)

    def test_ellis_absent_exits_0(self, tmp_path):
        """Ellis absent from roster must not block during active pipeline."""
        self._setup_active_pipeline(tmp_path, MINIMAL_ROSTER)
        rc = run_sequencing(tmp_path, "ellis")
        assert rc == 0, "Ellis absent from roster must not block (exit 0)"

    def test_agatha_absent_exits_0_during_build(self, tmp_path):
        """Agatha absent from roster must not block during build phase."""
        self._setup_active_pipeline(tmp_path, MINIMAL_ROSTER)
        rc = run_sequencing(tmp_path, "agatha")
        assert rc == 0, "Agatha absent from roster must not block during build (exit 0)"

    def test_investigator_absent_exits_0_with_worktree(self, tmp_path):
        """Investigator absent from roster must not block even when worktree_path set."""
        (tmp_path / "docs" / "pipeline").mkdir(parents=True, exist_ok=True)
        write_pipeline_config(tmp_path, MINIMAL_ROSTER)
        (tmp_path / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
        # Pipeline state with a worktree path
        (tmp_path / "docs" / "pipeline" / "pipeline-state.md").write_text(
            "# Pipeline State\n"
            '<!-- PIPELINE_STATUS: {"phase":"build","worktree_path":"/some/worktree","feature":"f"} -->\n'
        )
        write_enforcement_config(tmp_path)
        rc = run_sequencing(tmp_path, "investigator")
        assert rc == 0, "Investigator absent from roster must not block (exit 0)"

    def test_ellis_disabled_false_exits_0(self, tmp_path):
        """Ellis explicitly disabled (enabled:false) must not block."""
        roster = dict(MINIMAL_ROSTER)
        roster["ellis"] = {"enabled": False, "firing": "on-demand"}
        self._setup_active_pipeline(tmp_path, roster)
        rc = run_sequencing(tmp_path, "ellis")
        assert rc == 0, "Ellis with enabled:false must exit 0"

    def test_agatha_disabled_false_exits_0(self, tmp_path):
        """Agatha explicitly disabled must not block during build phase."""
        roster = dict(MINIMAL_ROSTER)
        roster["agatha"] = {"enabled": False, "firing": "on-demand"}
        self._setup_active_pipeline(tmp_path, roster)
        rc = run_sequencing(tmp_path, "agatha")
        assert rc == 0, "Agatha with enabled:false must exit 0 during build"


class TestRosterFailOpen:
    """Upgrade path: missing agent_roster key must preserve v5 behavior (fail-open)."""

    def test_no_roster_key_ellis_still_gated(self, tmp_path):
        """When agent_roster is absent, Ellis is still gated by Gate 1 (v5 behavior)."""
        write_pipeline_status(
            tmp_path,
            '{"phase":"build","sizing":"small","qa_status":"PENDING",'
            '"poirot_reviewed":"false","ci_watch_active":"false","feature":"feat"}',
        )
        # Write config WITHOUT agent_roster key (old install)
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
        (tmp_path / ".claude" / "pipeline-config.json").write_text(
            json.dumps({"project_name": "old-install"})
        )
        write_enforcement_config(tmp_path)
        rc = run_sequencing(tmp_path, "ellis")
        # Gate 1 blocks Ellis when qa_status != PASS -- fail-open means "agent treated as enabled"
        assert rc == 2, "Old install without agent_roster must preserve Gate 1 block for Ellis"

    def test_no_roster_key_agatha_still_gated_in_build(self, tmp_path):
        """When agent_roster is absent, Agatha is still gated by Gate 2 (v5 behavior)."""
        write_pipeline_status(
            tmp_path,
            '{"phase":"build","sizing":"small","qa_status":"PASS",'
            '"poirot_reviewed":"true","ci_watch_active":"false","feature":"feat"}',
        )
        (tmp_path / ".claude").mkdir(parents=True, exist_ok=True)
        (tmp_path / ".claude" / "pipeline-config.json").write_text(
            json.dumps({"project_name": "old-install"})
        )
        write_enforcement_config(tmp_path)
        rc = run_sequencing(tmp_path, "agatha")
        assert rc == 2, "Old install without agent_roster must preserve Gate 2 block for Agatha"


class TestRosterEnabledAgentsStillGated:
    """Enabled agents in the roster must still be gated normally."""

    def test_ellis_enabled_blocked_no_qa_pass(self, tmp_path):
        """Ellis enabled in roster is still blocked by Gate 1 when qa_status != PASS."""
        write_pipeline_status(
            tmp_path,
            '{"phase":"build","sizing":"small","qa_status":"PENDING",'
            '"poirot_reviewed":"false","ci_watch_active":"false","feature":"feat"}',
        )
        roster = dict(MINIMAL_ROSTER)
        roster["ellis"] = {"enabled": True, "firing": "pipeline-end"}
        write_pipeline_config(tmp_path, roster, generic_commit=False)
        write_enforcement_config(tmp_path)
        rc = run_sequencing(tmp_path, "ellis")
        assert rc == 2, "Ellis enabled must still be blocked by Gate 1 when no QA PASS"

    def test_agatha_enabled_blocked_during_build(self, tmp_path):
        """Agatha enabled in roster is still blocked by Gate 2 during build."""
        write_pipeline_status(
            tmp_path,
            '{"phase":"build","sizing":"small","qa_status":"PASS",'
            '"poirot_reviewed":"true","ci_watch_active":"false","feature":"feat"}',
        )
        roster = dict(MINIMAL_ROSTER)
        roster["agatha"] = {"enabled": True, "firing": "pipeline-end"}
        write_pipeline_config(tmp_path, roster)
        write_enforcement_config(tmp_path)
        rc = run_sequencing(tmp_path, "agatha")
        assert rc == 2, "Agatha enabled must still be blocked by Gate 2 during build"


# ── Contract 2: Ellis-absent commit flow ──────────────────────────────────


class TestElliAbsentCommitFlow:
    """When Ellis is absent from the roster, generic_commit_enabled must be true.

    This test validates that pipeline-config.json templates and setup skill
    write the correct generic_commit_enabled value based on roster composition.
    We test the config schema contract rather than the Eva behavior (which lives
    in a persona, not a hook).
    """

    def test_minimal_roster_template_has_generic_commit_true(self):
        """Source template for pipeline-config.json must have generic_commit_enabled:true."""
        from conftest import PROJECT_ROOT

        template_path = (
            PROJECT_ROOT / "source" / "shared" / "pipeline" / "pipeline-config.json"
        )
        assert template_path.exists(), "Source template must exist"
        config = json.loads(template_path.read_text())
        assert config.get("generic_commit_enabled") is True, (
            "Minimal install template must have generic_commit_enabled:true "
            "(Ellis absent from default roster)"
        )

    def test_minimal_roster_template_excludes_ellis(self):
        """Source template roster must not include Ellis as enabled."""
        from conftest import PROJECT_ROOT

        template_path = (
            PROJECT_ROOT / "source" / "shared" / "pipeline" / "pipeline-config.json"
        )
        config = json.loads(template_path.read_text())
        roster = config.get("agent_roster", {})
        # Ellis either absent or explicitly disabled in the minimal default
        ellis = roster.get("ellis", {})
        assert ellis.get("enabled", False) is not True, (
            "Minimal install roster must not have Ellis enabled "
            "(generic commit is the default)"
        )

    def test_installed_config_has_generic_commit(self):
        """Installed pipeline-config.json must have a generic_commit_enabled key."""
        from conftest import PROJECT_ROOT

        installed_path = PROJECT_ROOT / ".claude" / "pipeline-config.json"
        assert installed_path.exists(), "Installed pipeline-config.json must exist"
        config = json.loads(installed_path.read_text())
        assert "generic_commit_enabled" in config, (
            "Installed pipeline-config.json must have generic_commit_enabled key "
            "(set by setup wizard based on roster)"
        )

    def test_installed_config_no_dashboard_mode(self):
        """Installed pipeline-config.json must not have dashboard_mode key (ADR-0060)."""
        from conftest import PROJECT_ROOT

        installed_path = PROJECT_ROOT / ".claude" / "pipeline-config.json"
        config = json.loads(installed_path.read_text())
        assert "dashboard_mode" not in config, (
            "dashboard_mode must be removed from pipeline-config.json (ADR-0060)"
        )

    def test_source_template_no_dashboard_mode(self):
        """Source template pipeline-config.json must not have dashboard_mode (ADR-0060)."""
        from conftest import PROJECT_ROOT

        template_path = (
            PROJECT_ROOT / "source" / "shared" / "pipeline" / "pipeline-config.json"
        )
        config = json.loads(template_path.read_text())
        assert "dashboard_mode" not in config, (
            "Source template must not have dashboard_mode key (ADR-0060)"
        )

    def test_installed_config_has_agent_roster(self):
        """Installed pipeline-config.json must have agent_roster key."""
        from conftest import PROJECT_ROOT

        installed_path = PROJECT_ROOT / ".claude" / "pipeline-config.json"
        config = json.loads(installed_path.read_text())
        assert "agent_roster" in config, "Installed config must have agent_roster key"
        roster = config["agent_roster"]
        # Core trio must always be enabled
        for agent in ("robert", "sarah", "colby"):
            assert roster.get(agent, {}).get("enabled") is True, (
                f"Core agent {agent} must be enabled in roster"
            )
            assert roster[agent].get("firing") == "core", (
                f"Core agent {agent} must have firing:core"
            )
