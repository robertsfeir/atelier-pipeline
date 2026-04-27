"""Structural test: agent frontmatter must pin explicit Anthropic model IDs.

Ensures every `*.frontmatter.yml` file under both `source/claude/agents/`
and `source/cursor/agents/` declares a `model:` value that starts with
`claude-` (i.e., an explicit versioned ID such as `claude-opus-4-7`),
never a generic alias (`opus`, `sonnet`, `haiku`).

Justification: ADR-0047 Phase 4. Generic aliases can be silently
re-resolved by Anthropic to non-4.7 models, invalidating the call-
efficiency assumption that Phase 2's tightened `maxTurns` budgets rest on.
This test catches alias drift the moment a new agent is added.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml  # type: ignore

    _HAS_YAML = True
except ImportError:  # pragma: no cover - fallback path
    _HAS_YAML = False


REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTMATTER_DIRS = (
    REPO_ROOT / "source" / "claude" / "agents",
    REPO_ROOT / "source" / "cursor" / "agents",
)
REQUIRED_PREFIX = "claude-"
GENERIC_ALIASES = {"opus", "sonnet", "haiku"}


def _discover_frontmatter_files() -> list[Path]:
    files: list[Path] = []
    for directory in FRONTMATTER_DIRS:
        files.extend(sorted(directory.glob("*.frontmatter.yml")))
    return files


def _extract_model_field(path: Path) -> str | None:
    """Return the `model` field value, or None if missing.

    Uses PyYAML when available; otherwise falls back to a line-by-line
    scan that matches the project's flat frontmatter format.
    """
    text = path.read_text(encoding="utf-8")
    if _HAS_YAML:
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            return None
        value = data.get("model")
        return str(value) if value is not None else None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("model:"):
            return stripped.split(":", 1)[1].strip()
    return None


FRONTMATTER_FILES = _discover_frontmatter_files()


def test_frontmatter_files_discovered() -> None:
    """Sanity: at least one frontmatter file exists in each tree."""
    assert FRONTMATTER_FILES, (
        f"No *.frontmatter.yml files found under {FRONTMATTER_DIRS!r}; "
        "the test would otherwise pass vacuously."
    )
    for directory in FRONTMATTER_DIRS:
        present = list(directory.glob("*.frontmatter.yml"))
        assert present, f"No frontmatter files under {directory}"


@pytest.mark.parametrize(
    "frontmatter_path",
    FRONTMATTER_FILES,
    ids=[str(p.relative_to(REPO_ROOT)) for p in FRONTMATTER_FILES],
)
def test_model_field_is_explicit_id(frontmatter_path: Path) -> None:
    """`model:` must be an explicit `claude-*` ID, not a generic alias."""
    model = _extract_model_field(frontmatter_path)
    rel = frontmatter_path.relative_to(REPO_ROOT)
    assert model is not None, f"{rel}: missing `model:` field"
    assert model not in GENERIC_ALIASES, (
        f"{rel}: model field is generic alias {model!r}; "
        f"pin an explicit ID starting with {REQUIRED_PREFIX!r} "
        "(see ADR-0047 Phase 4)."
    )
    assert model.startswith(REQUIRED_PREFIX), (
        f"{rel}: model field {model!r} does not start with "
        f"{REQUIRED_PREFIX!r}; pin an explicit Anthropic model ID such as "
        "`claude-opus-4-7`, `claude-sonnet-4-6`, or "
        "`claude-haiku-4-5-20251001` (see ADR-0047 Phase 4)."
    )
