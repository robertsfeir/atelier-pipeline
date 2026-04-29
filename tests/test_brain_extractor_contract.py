"""Contract tests for Sarah's revision-mode token.

The original module also covered the brain-extractor consumer side of the
contract -- those tests were removed when the brain-extractor agent itself
was deleted in v4.1.0 (superseded by the ADR-0053 three-hook capture gate).
What remains is the producer-side assertion: Sarah must emit the
`Revision <N>` placeholder in her Revision Mode section so downstream
telemetry curation (now performed by Eva, not the extractor) has a stable
token to recognize.

This test runs against all three agent locations:
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
