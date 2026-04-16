"""ADR-0041 pre-build test assertions: frontmatter consistency.

Parameterized test over the 15 agents listed in ADR-0041 §Per-Agent
Assignment Table x 2 platforms (Claude + Cursor) = 30 assertions.

Covers test-spec IDs T-0041-025 through T-0041-039 (both platforms).

Pre-build: majority of assertions FAIL -- reasoning-tier agents still carry
`sonnet` or outdated effort values. That is the expected pre-build signal
per Roz-first TDD (retro lesson 002).
"""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLAUDE_AGENTS_DIR = PROJECT_ROOT / "source" / "claude" / "agents"
CURSOR_AGENTS_DIR = PROJECT_ROOT / "source" / "cursor" / "agents"

# ADR-0041 §Per-Agent Assignment Table (authoritative runtime lookup).
EXPECTED = {
    "cal":             {"model": "opus",  "effort": "xhigh"},
    "colby":           {"model": "opus",  "effort": "high"},
    "roz":             {"model": "opus",  "effort": "high"},
    "investigator":    {"model": "opus",  "effort": "high"},
    "robert":          {"model": "opus",  "effort": "medium"},
    "robert-spec":     {"model": "opus",  "effort": "medium"},
    "sable":           {"model": "opus",  "effort": "medium"},
    "sable-ux":        {"model": "opus",  "effort": "medium"},
    "sentinel":        {"model": "opus",  "effort": "medium"},
    "deps":            {"model": "opus",  "effort": "medium"},
    "darwin":          {"model": "opus",  "effort": "high"},
    "agatha":          {"model": "opus",  "effort": "medium"},
    "ellis":           {"model": "haiku", "effort": "low"},
    "distillator":     {"model": "haiku", "effort": "low"},
    "brain-extractor": {"model": "haiku", "effort": "low"},
}

PLATFORMS = [
    ("claude", CLAUDE_AGENTS_DIR),
    ("cursor", CURSOR_AGENTS_DIR),
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


_MODEL_RE = re.compile(r"^model:\s*(\S+)\s*$", re.MULTILINE)
_EFFORT_RE = re.compile(r"^effort:\s*(\S+)\s*$", re.MULTILINE)


def _parse_frontmatter(path: Path) -> dict:
    """Return a flat dict of top-level `model:` and `effort:` values from a
    YAML frontmatter file. Does not pull in PyYAML -- the schema is flat and
    a simple regex over the file text suffices."""
    if not path.exists():
        pytest.skip(f"Frontmatter file not found: {path}")
    text = path.read_text()
    out: dict = {}
    m = _MODEL_RE.search(text)
    if m:
        out["model"] = m.group(1).strip().strip("'\"")
    e = _EFFORT_RE.search(text)
    if e:
        out["effort"] = e.group(1).strip().strip("'\"")
    return out


def _model_matches(actual: str, expected_substring: str) -> bool:
    """Substring match so that fully-qualified model strings such as
    `claude-haiku-4-5-20250101` match the canonical family name `haiku`."""
    if actual is None:
        return False
    return expected_substring.lower() in actual.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Parameterized: 15 agents x 2 platforms = 30 assertions
# ─────────────────────────────────────────────────────────────────────────────


_PARAMS = [
    pytest.param(agent, platform, dir_, id=f"{platform}-{agent}")
    for agent, _ in EXPECTED.items()
    for platform, dir_ in PLATFORMS
]


@pytest.mark.parametrize("agent,platform,agents_dir", _PARAMS)
def test_frontmatter_model_and_effort(agent, platform, agents_dir):
    """For each (agent, platform): the frontmatter file carries the `model`
    and `effort` values from ADR-0041 §Per-Agent Assignment Table.

    Pre-build: FAILS for reasoning-tier agents still carrying `sonnet`, for
    Cal still carrying `high` effort, and for brain-extractor missing the
    `effort` field altogether.
    """
    path = agents_dir / f"{agent}.frontmatter.yml"
    fm = _parse_frontmatter(path)

    expected_model = EXPECTED[agent]["model"]
    expected_effort = EXPECTED[agent]["effort"]

    actual_model = fm.get("model")
    actual_effort = fm.get("effort")

    assert actual_model is not None, (
        f"{path} is missing a top-level `model:` key."
    )
    assert _model_matches(actual_model, expected_model), (
        f"{path}: expected model family '{expected_model}' but got "
        f"'{actual_model}'. ADR-0041 §Per-Agent Assignment Table requires "
        f"the {agent} agent to use {expected_model} base model."
    )

    assert actual_effort is not None, (
        f"{path} is missing a top-level `effort:` key. ADR-0041 §Decision "
        "requires every agent frontmatter to declare effort explicitly."
    )
    assert actual_effort == expected_effort, (
        f"{path}: expected effort '{expected_effort}' but got "
        f"'{actual_effort}'. ADR-0041 §Per-Agent Assignment Table assigns "
        f"{expected_effort} to the {agent} agent."
    )
