"""Contract tests for brain-extractor <-> producer persona files.

These are structural/contract tests that verify producer personas and the
brain-extractor consumer agree on the same textual tokens. They do NOT
exercise an LLM -- they check that the token a producer is instructed to
emit is the same token the extractor is instructed to search for. If these
drift apart, structured quality signals silently stop flowing, and no
behavioral test would catch it.

Each test runs against all three agent locations:
- `source/shared/agents/` (canonical source)
- `.claude/agents/` (installed Claude Code mirror)
- `.cursor-plugin/agents/` (installed Cursor mirror)

Installed mirrors are assembled from source/shared body + platform frontmatter
overlay, so body changes must stay in sync across all three locations.
"""

import pytest

from tests.conftest import CURSOR_AGENTS, INSTALLED_AGENTS, SHARED_AGENTS


AGENT_DIRS = [
    pytest.param(SHARED_AGENTS, id="shared"),
    pytest.param(INSTALLED_AGENTS, id="claude"),
    pytest.param(CURSOR_AGENTS, id="cursor"),
]


@pytest.mark.parametrize("agents_dir", AGENT_DIRS)
def test_brain_extractor_documents_adr_revision_signal(agents_dir):
    """brain-extractor.md must mention `adr_revision` in its sarah quality
    signals section. This is the field name persisted to metadata."""
    extractor = (agents_dir / "brain-extractor.md").read_text()
    assert "adr_revision" in extractor, (
        f"brain-extractor.md in {agents_dir} is missing the `adr_revision` "
        "quality signal. Sarah's revision telemetry depends on this field name."
    )


@pytest.mark.parametrize("agents_dir", AGENT_DIRS)
def test_brain_extractor_searches_for_revision_n_pattern(agents_dir):
    """brain-extractor.md must explicitly name the `Revision <integer>` pattern
    it searches for in Sarah's ADR output. If this token changes on the
    extractor side without coordination, revision cycles go invisible."""
    extractor = (agents_dir / "brain-extractor.md").read_text()
    assert "Revision <integer>" in extractor, (
        f"brain-extractor.md in {agents_dir} no longer mentions the "
        "`Revision <integer>` token. Either the pattern changed or the signal "
        "documentation drifted; coordinate with Sarah's Revision Mode section "
        "before landing."
    )


@pytest.mark.parametrize("agents_dir", AGENT_DIRS)
def test_sarah_revision_mode_emits_revision_n_token(agents_dir):
    """sarah.md must instruct Sarah to emit a `Revision <N>` placeholder in
    Revision Mode -- the template form of the `Revision N` token the
    brain-extractor searches for. This is the producer half of the contract
    verified above."""
    sarah = (agents_dir / "sarah.md").read_text()
    assert "### Revision Mode" in sarah, (
        f"sarah.md in {agents_dir} is missing the `### Revision Mode` section "
        "that defines the revision marker format."
    )
    # Locate the Revision Mode section and confirm the token appears inside it.
    revision_start = sarah.index("### Revision Mode")
    # End at the next top-level `## ` or `</workflow>` -- whichever comes first.
    tail = sarah[revision_start:]
    next_top_level = len(tail)
    for marker in ("\n## ", "\n</workflow>"):
        idx = tail.find(marker)
        if idx != -1 and idx < next_top_level:
            next_top_level = idx
    revision_section = tail[:next_top_level]
    assert "Revision <N>" in revision_section, (
        f"sarah.md in {agents_dir} Revision Mode section no longer instructs "
        "Sarah to emit `Revision <N>`. The brain-extractor searches for the "
        "`Revision N` pattern; producer and consumer must stay aligned."
    )
