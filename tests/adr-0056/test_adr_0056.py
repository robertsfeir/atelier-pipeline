"""Behavioral / contract tests for ADR-0056: Brain Migration Wizard.

ADR-0056 inserts a one-time migration wizard (Step 0f) into the
pipeline-setup skill that hands existing bundled-brain installs over to
the standalone mybrain plugin without losing data. Phase 3 of ADR-0055
deletes brain/ from this repo, so the wizard's third detection signal
(`brain/server.mjs` readable in CLAUDE_PLUGIN_ROOT) is absent in the
source tree -- a project that has upgraded to Phase 3+ will exit the
wizard at S0 (silent no-op).

These are documentation-contract tests: the wizard runs in a SKILL.md
prose body interpreted by the skill agent, so the load-bearing guarantees
(idempotency gate, S5 rollback recovery command, multi-project warning,
no config key translation) are tested by parsing SKILL.md and asserting
the prose contains the required strings. Behavior at runtime is exercised
by Sarah's wizard-idempotency and S5-rollback contract tests when the
wizard actually runs against a real install.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PIPELINE_SETUP_SKILL = PROJECT_ROOT / "skills" / "pipeline-setup" / "SKILL.md"
CURSOR_PIPELINE_SETUP = PROJECT_ROOT / ".cursor-plugin" / "skills" / "pipeline-setup" / "SKILL.md"


# ─── 1. Idempotency: brain/server.mjs is gone, S0 must gate on it ─────────


def test_brain_server_mjs_absent_in_source_tree():
    """Phase 3 deletes brain/server.mjs. Step 0f signal 3 gates on this file
    being present in the user's CLAUDE_PLUGIN_ROOT. With it absent in the
    source tree, every fresh upgrade past Phase 3 has signal 3 false → wizard
    exits at S0 (silent no-op). This is the load-bearing idempotency
    guarantee for users who upgraded directly past Phase 3."""
    assert not (PROJECT_ROOT / "brain" / "server.mjs").exists(), (
        "brain/server.mjs is still present in the source tree; ADR-0055 Phase 3 "
        "deleted it and ADR-0056 detection signal 3 depends on its absence."
    )


def test_s0_detection_gates_on_brain_server_mjs():
    """The wizard's S0 must explicitly check brain/server.mjs presence.
    Without that gate, the wizard would re-trigger on every Phase-3+ install."""
    text = PIPELINE_SETUP_SKILL.read_text()
    assert "brain/server.mjs" in text, (
        "Step 0f must reference `brain/server.mjs` as the bundled-brain "
        "detection signal. Without it the wizard re-triggers on every run."
    )


def test_s0_uses_logical_and_for_three_signals():
    """ADR-0056 explicitly says all three signals must hold (AND, not OR).
    The skill text must reflect that — single-signal triggers cause false
    positives and cause the wizard to misfire."""
    text = PIPELINE_SETUP_SKILL.read_text()
    # The skill prose explicitly uses "all three" or "AND" language to make
    # the conjunction explicit.
    assert ("all three" in text.lower() or "logical and" in text.lower()), (
        "Step 0f must declare the three detection signals are AND-combined "
        "(not OR). Single-signal triggers misfire on long-lived projects."
    )


def test_wizard_idempotency_documented():
    """Idempotency contract: re-running pipeline-setup on a freshly migrated
    install must be a silent no-op. The skill text must state that contract
    so the skill agent does not re-trigger destructive actions."""
    text = PIPELINE_SETUP_SKILL.read_text()
    assert "idempot" in text.lower() and "Step 0f" in text, (
        "Step 0f must declare its idempotency contract (re-running on a "
        "migrated install is a silent no-op)."
    )


# ─── 2. S5 rollback contract — highest-risk state ────────────────────────


def test_s5_rollback_contract_includes_recovery_command():
    """The S5 HALT message must include the exact `psql ... < backup_path`
    command. This is the highest-risk state per ADR-0056 — old brain gone,
    mybrain installed, DB in partial migration. Silent failure here is
    unrecoverable; the skill MUST tell the user the recovery command."""
    text = PIPELINE_SETUP_SKILL.read_text()
    # Locate the S5 section text. The skill labels it #### S5 — Verify & Migrate.
    s5_idx = text.find("#### S5")
    assert s5_idx >= 0, "S5 section missing entirely from pipeline-setup SKILL.md."
    s5_section = text[s5_idx:s5_idx + 4000]  # ~4KB window covers the section

    assert "psql" in s5_section, (
        "S5 HALT message must include the `psql` recovery command per ADR-0056 rollback contract."
    )
    assert "backup_path" in s5_section or "<backup_path>" in s5_section, (
        "S5 HALT message must reference the backup path placeholder."
    )
    # The state name must be mentioned in the failure path so the user
    # knows where the migration stopped.
    assert "S5 HALT" in s5_section, (
        "S5 HALT label missing from the S5 section — rollback contract requires "
        "the state name be visible in the HALT message."
    )


# ─── 3. Wizard structural presence ───────────────────────────────────────


def test_step_0f_header_present():
    """Step 0f header must exist in the pipeline-setup skill."""
    text = PIPELINE_SETUP_SKILL.read_text()
    assert "### Step 0f" in text, (
        "pipeline-setup/SKILL.md is missing the `### Step 0f` header for the "
        "ADR-0056 brain migration wizard."
    )


def test_three_detection_signals_documented():
    """The skill must list all three S0 detection signals so the skill agent
    knows what to probe before triggering the wizard."""
    text = PIPELINE_SETUP_SKILL.read_text()
    # Signal 1: mybrain ToolSearch probe.
    assert "ToolSearch" in text and "mybrain" in text, (
        "Signal 1 (mybrain ToolSearch probe) must be documented in Step 0f."
    )
    # Signal 2: brain-config.json + reachability.
    assert ".claude/brain-config.json" in text and "SELECT 1" in text, (
        "Signal 2 (brain-config.json + Postgres reachability) must be documented."
    )
    # Signal 3: brain/server.mjs presence (already asserted above, but
    # repeated here for the three-signal contract completeness).
    assert "brain/server.mjs" in text, (
        "Signal 3 (brain/server.mjs presence) must be documented."
    )


def test_consent_screen_states_no_data_loss():
    """The S1 consent screen must contain the exact 'Your existing brain data
    will NOT be lost' phrase per ADR-0056 §Decision."""
    text = PIPELINE_SETUP_SKILL.read_text()
    assert "Your existing brain data will NOT be lost" in text, (
        "S1 consent screen must contain the exact phrase "
        "'Your existing brain data will NOT be lost' per the ADR-0056 contract."
    )


def test_multi_project_shared_db_warning_present():
    """The S1 consent screen must surface the multi-project shared-DB warning
    per ADR-0056. Migrating one project migrates the schema for every project
    pointing at the same DB."""
    text = PIPELINE_SETUP_SKILL.read_text()
    assert ("shared with other" in text.lower() or "multi-project" in text.lower() or
            "other atelier-pipeline projects" in text), (
        "S1 must include a multi-project shared-DB warning per ADR-0056."
    )
    # The migration-is-additive promise must be visible too.
    assert "additive" in text.lower(), (
        "S1 multi-project warning must note the migration is additive "
        "(new columns, nothing dropped)."
    )


def test_pg_dump_advisory_blocking():
    """ADR-0056 pg_dump policy: advisory-blocking. If pg_dump unavailable,
    the wizard surfaces the manual command and requires explicit
    acknowledgement. The skill text must reflect this — neither hard-block
    nor silent skip."""
    text = PIPELINE_SETUP_SKILL.read_text()
    assert "pg_dump" in text, "Step 0f must reference pg_dump for the backup gate."
    # The acknowledgement / 'I have my own backup' path must be present.
    assert ("acknowledge" in text.lower() or "have your own backup" in text.lower() or
            "have my own backup" in text.lower()), (
        "ADR-0056 pg_dump policy is advisory-blocking; the skill must offer an "
        "explicit acknowledgement path when pg_dump is unavailable."
    )


def test_s4_wizard_cannot_install_plugins():
    """ADR-0056 S4: the wizard CANNOT install plugins on the user's behalf.
    It must print the install command and wait for user confirmation."""
    text = PIPELINE_SETUP_SKILL.read_text()
    s4_idx = text.find("#### S4")
    assert s4_idx >= 0, "S4 section missing."
    s4_section = text[s4_idx:s4_idx + 3000]
    assert ("cannot install" in s4_section.lower() or
            "wait for user" in s4_section.lower() or
            "user confirmation" in s4_section.lower()), (
        "S4 must declare that the wizard waits for user confirmation that "
        "mybrain is installed (the skill cannot install plugins itself)."
    )
    assert "ToolSearch" in s4_section, (
        "S4 must probe ToolSearch to verify mybrain registration after the user installs it."
    )


def test_two_parallel_tracks_migrate_and_fresh():
    """ADR-0056 specifies two parallel tracks: migrate (preserve data) and
    fresh (drop schema). The skill must document both with separately named
    states (S2/S2-fresh, S3/S3-fresh, etc.) for an auditable rollback contract."""
    text = PIPELINE_SETUP_SKILL.read_text()
    for state in ["S2", "S2-fresh", "S3", "S3-fresh", "S4", "S4-fresh", "S5", "S5-fresh"]:
        assert state in text, (
            f"State {state} missing from Step 0f wizard. Both migrate and "
            f"fresh tracks must be documented with separate state names."
        )


# ─── 4. Config key preservation — no translation ─────────────────────────


def test_no_config_key_rename_or_translate_instructions():
    """ADR-0056 §Config Key Migration Map: the wizard rewrites no config keys.
    The migration is a hand-off, not a translation. The skill text must NOT
    contain instructions to rename/translate any config keys in the wizard
    section."""
    text = PIPELINE_SETUP_SKILL.read_text()

    # Locate the wizard section bounded by Step 0f start and the next Step
    # heading at the same level.
    start = text.find("### Step 0f")
    assert start >= 0, "Step 0f section missing entirely."
    end = text.find("### Step 1:", start)
    assert end > start, "Could not locate end of Step 0f section."
    wizard = text[start:end]

    forbidden = [
        "rename the config",
        "rename config",
        "translate the config",
        "translate config",
        "rewrite the config",
        "rewrite config keys",
    ]
    for phrase in forbidden:
        assert phrase.lower() not in wizard.lower(), (
            f"Step 0f contains forbidden phrase {phrase!r}. ADR-0056 specifies "
            "the wizard preserves config keys verbatim — no translation."
        )

    # Conversely, the preservation contract should be explicitly stated.
    assert ("hand-off" in wizard.lower() or
            "preservation" in wizard.lower() or
            "preserve" in wizard.lower() or
            "not a translation" in wizard.lower()), (
        "Step 0f must explicitly state that the migration is a hand-off / "
        "preservation, not a config translation."
    )


# ─── 5. Cursor mirror in sync ────────────────────────────────────────────


def test_cursor_mirror_contains_step_0f():
    """The cursor mirror of pipeline-setup must contain Step 0f identical to
    the source skill — both targets must ship the wizard."""
    src = PIPELINE_SETUP_SKILL.read_text()
    cursor = CURSOR_PIPELINE_SETUP.read_text()
    assert "### Step 0f" in cursor, (
        ".cursor-plugin/skills/pipeline-setup/SKILL.md is missing Step 0f."
    )
    assert src == cursor, (
        "skills/pipeline-setup/SKILL.md and the cursor mirror are out of sync. "
        "Step 0f content must be identical across both targets."
    )
