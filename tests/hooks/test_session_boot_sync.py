"""Tests for ADR-0033 Step 2: session-boot.sh byte-identical duplicate enforcement.

Covers T-0033-002.

source/shared/hooks/session-boot.sh is the install source (per SKILL.md line 313).
source/claude/hooks/session-boot.sh is a legacy byte-identical duplicate. The ADR
commits to keeping both files in sync so a future edit cannot silently diverge
the install source from the Claude-overlay copy.

Colby MUST NOT modify this assertion.
"""

import hashlib

from conftest import PROJECT_ROOT

SHARED_COPY = PROJECT_ROOT / "source" / "shared" / "hooks" / "session-boot.sh"
CLAUDE_COPY = PROJECT_ROOT / "source" / "claude" / "hooks" / "session-boot.sh"


def _sha256(path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def test_T_0033_002_session_boot_files_identical():
    """Both session-boot.sh files must be byte-identical (SHA-256).

    Rationale: SKILL.md line 313 manifest copies
    source/shared/hooks/session-boot.sh into .claude/hooks/session-boot.sh at
    install time. source/claude/hooks/session-boot.sh is a legacy duplicate in
    the repo. If the two drift, contributors reading one might miss a fix in
    the other, re-introducing C1 (PIPELINE_STATUS grep mismatch) or M2
    (CORE_AGENTS list drift).

    The fix: lock them together via SHA-256. Any future edit must touch both.
    """
    assert SHARED_COPY.exists(), f"Missing shared copy: {SHARED_COPY}"
    assert CLAUDE_COPY.exists(), f"Missing claude copy: {CLAUDE_COPY}"
    shared_digest = _sha256(SHARED_COPY)
    claude_digest = _sha256(CLAUDE_COPY)
    assert shared_digest == claude_digest, (
        f"session-boot.sh copies have drifted.\n"
        f"  {SHARED_COPY} SHA-256: {shared_digest}\n"
        f"  {CLAUDE_COPY} SHA-256: {claude_digest}\n"
        f"Both must remain byte-identical — any edit to session-boot.sh must be "
        f"applied to both files in the same commit."
    )
