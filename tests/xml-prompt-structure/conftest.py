"""Local conftest for xml-prompt-structure tests -- re-exports project-level fixtures."""

# Re-export PROJECT_ROOT so that tests doing `from conftest import PROJECT_ROOT`
# resolve correctly even when this local conftest shadows the root conftest during
# subprocess pytest collection (e.g. from meta-tests that run `pytest tests/`).
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
