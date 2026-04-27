"""ADR-0051 / issue #45 item 5 — provenance surfacing.

Asserts that the <brain-context> format spec surfaces the brain's
provenance fields (captured_by, created_at) so subagents can weigh
credibility instead of having those fields silently dropped.

Files asserted on:
- source/shared/rules/agent-system.md (<thought> attribute spec)
- source/shared/references/invocation-templates.md (worked example)
- source/shared/references/agent-preamble.md (step 3 weighting guidance)
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SHARED = PROJECT_ROOT / "source" / "shared"

AGENT_SYSTEM = SHARED / "rules" / "agent-system.md"
INVOCATION_TEMPLATES = SHARED / "references" / "invocation-templates.md"
AGENT_PREAMBLE = SHARED / "references" / "agent-preamble.md"


def test_agent_system_brain_context_lists_provenance_attributes():
    text = AGENT_SYSTEM.read_text()
    assert "captured_by" in text, (
        "agent-system.md <brain-context> spec must list captured_by so Eva "
        "surfaces brain provenance instead of dropping it silently."
    )
    assert "created_at" in text, (
        "agent-system.md <brain-context> spec must list created_at so "
        "subagents can weigh thought recency."
    )
    assert "combined_score" in text, (
        "agent-system.md <brain-context> spec must reference combined_score "
        "as the relevance source field returned by agent_search."
    )


def test_invocation_templates_shows_fully_formed_brain_context_example():
    text = INVOCATION_TEMPLATES.read_text()
    assert "captured_by=" in text, (
        "invocation-templates.md must include a worked <brain-context> "
        "example with the captured_by attribute populated."
    )
    assert "created_at=" in text, (
        "invocation-templates.md must include a worked <brain-context> "
        "example with the created_at attribute populated."
    )


def test_agent_preamble_step3_names_provenance_attributes():
    text = AGENT_PREAMBLE.read_text()
    assert "captured_by" in text and "created_at" in text, (
        "agent-preamble.md step 3 must name captured_by and created_at as "
        "the credibility-weighting attributes subagents should consult."
    )
    # Ensure the reference-not-instruction framing is preserved (extended,
    # not replaced) — guards against scope creep on this edit.
    assert "reference, not instruction" in text, (
        "agent-preamble.md step 3 reference-not-instruction framing must be "
        "preserved; provenance guidance extends it, does not replace it."
    )
