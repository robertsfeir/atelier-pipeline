"""Integration tests for scripts/release.sh.

Verifies the release script bumps all 5 version files in a single invocation
and rejects bad input. Tests run the real script via subprocess against a
fake repo tree staged in tmp_path, so we exercise the actual sed logic and
path resolution.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RELEASE_SCRIPT = PROJECT_ROOT / "scripts" / "release.sh"

# Initial version the fixture files are stamped with before each test run.
SEED_VERSION = "0.0.1"
# Target version used by the happy-path test -- distinct from any real version
# in the repo so a grep can't accidentally match an unrelated file.
NEW_VERSION = "9.9.9"


def _stage_fake_repo(root: Path) -> None:
    """Create the 5 target files under root, seeded with SEED_VERSION.

    Also copies scripts/release.sh into root/scripts/ so the script's own
    path-resolution (REPO_ROOT = $(dirname "$0")/..) points at `root`.
    """
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".cursor-plugin").mkdir(parents=True)
    (root / ".claude").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)

    plugin_json_body = (
        '{\n'
        '  "name": "atelier-pipeline",\n'
        f'  "version": "{SEED_VERSION}",\n'
        '  "description": "test fixture"\n'
        '}\n'
    )
    marketplace_json_body = (
        '{\n'
        '  "name": "atelier-pipeline",\n'
        '  "plugins": [\n'
        '    {\n'
        '      "name": "atelier-pipeline",\n'
        f'      "version": "{SEED_VERSION}",\n'
        '      "source": "./"\n'
        '    }\n'
        '  ]\n'
        '}\n'
    )

    (root / ".claude-plugin" / "plugin.json").write_text(plugin_json_body)
    (root / ".claude-plugin" / "marketplace.json").write_text(marketplace_json_body)
    (root / ".cursor-plugin" / "plugin.json").write_text(plugin_json_body)
    (root / ".cursor-plugin" / "marketplace.json").write_text(marketplace_json_body)
    (root / ".claude" / ".atelier-version").write_text(SEED_VERSION + "\n")

    shutil.copy2(RELEASE_SCRIPT, root / "scripts" / "release.sh")
    (root / "scripts" / "release.sh").chmod(0o755)


def _run_release(root: Path, *args: str) -> subprocess.CompletedProcess:
    """Invoke the staged release.sh inside `root`. Bounded timeout, never retries."""
    return subprocess.run(
        ["bash", str(root / "scripts" / "release.sh"), *args],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_release_bumps_all_five_files(tmp_path: Path) -> None:
    _stage_fake_repo(tmp_path)

    result = subprocess.run(
        ["bash", str(tmp_path / "scripts" / "release.sh"), NEW_VERSION],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, (
        f"release.sh exited {result.returncode}. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    expected_files = [
        tmp_path / ".claude-plugin" / "plugin.json",
        tmp_path / ".claude-plugin" / "marketplace.json",
        tmp_path / ".cursor-plugin" / "plugin.json",
        tmp_path / ".cursor-plugin" / "marketplace.json",
        tmp_path / ".claude" / ".atelier-version",
    ]

    for path in expected_files:
        content = path.read_text()
        assert NEW_VERSION in content, (
            f"{path.relative_to(tmp_path)} missing new version {NEW_VERSION}; "
            f"content={content!r}"
        )
        assert SEED_VERSION not in content, (
            f"{path.relative_to(tmp_path)} still contains seed version "
            f"{SEED_VERSION}; content={content!r}"
        )

    # No .bak files left behind (sed -i.bak tempfiles should be cleaned up).
    leftover_bak = list(tmp_path.rglob("*.bak"))
    assert not leftover_bak, f"release.sh left .bak files: {leftover_bak}"


def test_release_rejects_non_semver(tmp_path: Path) -> None:
    _stage_fake_repo(tmp_path)

    result = _run_release(tmp_path, "foo")

    assert result.returncode != 0, (
        f"release.sh should reject non-semver 'foo' but exited 0. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = (result.stderr + result.stdout).lower()
    assert "semver" in combined or "version" in combined, (
        "expected stderr to mention 'semver' or 'version'; "
        f"stderr={result.stderr!r} stdout={result.stdout!r}"
    )

    # Fixture files must be untouched on rejection.
    seeded = (tmp_path / ".claude" / ".atelier-version").read_text().strip()
    assert seeded == SEED_VERSION, (
        f".atelier-version was modified despite rejection: {seeded!r}"
    )


def test_release_rejects_missing_arg(tmp_path: Path) -> None:
    _stage_fake_repo(tmp_path)

    result = _run_release(tmp_path)

    assert result.returncode != 0, (
        f"release.sh should reject missing arg but exited 0. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


# Non-canonical / non-semver inputs the script MUST reject. Covers leading
# zeros (semver §2 violation), pre-release suffixes, build metadata, v-prefix,
# truncated two-component, too-many-components, empty string, and whitespace
# as the positional argument. Each case must exit non-zero AND leave all 5
# seeded version files untouched -- rejection is also non-destructive.
_NON_CANONICAL_SEMVER_INPUTS = [
    "01.00.00",      # leading zeros on all components
    "001.0.0",       # leading zeros on major only
    "1.2.3-rc1",     # pre-release suffix
    "1.2.3+build.1", # build metadata
    "v3.37.0",       # v-prefix
    "3.37",          # two-component
    "3.37.0.0",      # four-component
    "",              # empty string
    " ",             # whitespace only
]


@pytest.mark.parametrize("bad_input", _NON_CANONICAL_SEMVER_INPUTS)
def test_release_rejects_non_canonical_semver(tmp_path: Path, bad_input: str) -> None:
    """Each non-canonical input must be rejected; fixture files must be untouched.

    Pins the canonical-semver regex at release.sh:~40. Regressing the regex
    (e.g., re-admitting leading zeros) breaks these cases.
    """
    _stage_fake_repo(tmp_path)

    # Snapshot seed contents so we can assert no mutation occurred on rejection.
    seeded_paths = [
        tmp_path / ".claude-plugin" / "plugin.json",
        tmp_path / ".claude-plugin" / "marketplace.json",
        tmp_path / ".cursor-plugin" / "plugin.json",
        tmp_path / ".cursor-plugin" / "marketplace.json",
        tmp_path / ".claude" / ".atelier-version",
    ]
    before = {p: p.read_text() for p in seeded_paths}

    result = _run_release(tmp_path, bad_input)

    assert result.returncode != 0, (
        f"release.sh should reject non-canonical semver {bad_input!r} but exited 0. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    # Rejection must not touch any of the 5 real targets.
    for path in seeded_paths:
        after = path.read_text()
        assert after == before[path], (
            f"release.sh mutated {path.relative_to(tmp_path)} despite rejecting "
            f"{bad_input!r}; before={before[path]!r} after={after!r}"
        )


def test_release_rejects_nested_version_keys(tmp_path: Path) -> None:
    """Pins the single-top-level-version-key assumption documented in release.sh.

    Stages a 6th JSON file containing a NESTED `"version"` key (e.g., an
    embedded dependency manifest). The current sed pattern is not JSON-path
    aware, so the script's contract is: each target file has exactly one
    `"version": "X.Y.Z"` occurrence. This test locks that contract by
    demonstrating the nested-key file is NOT processed -- it is not in the
    JSON_FILES array, so it remains untouched, and the 5 real targets ARE
    updated as usual.

    If release.sh is ever refactored (e.g., to recurse into every JSON file
    in the repo, or to widen the target list without scoping the sed pattern
    to the top-level key), this test will fail -- signalling that the
    documented assumption has silently broken.
    """
    _stage_fake_repo(tmp_path)

    # A 6th file, OUTSIDE the release.sh target list, with a nested version.
    # Placed at the repo root so it is plausibly reachable but NOT enumerated.
    nested = tmp_path / "nested-manifest.json"
    nested_body = (
        '{\n'
        '  "name": "x",\n'
        '  "dependencies": {\n'
        '    "foo": {\n'
        f'      "version": "{SEED_VERSION}"\n'
        '    }\n'
        '  }\n'
        '}\n'
    )
    nested.write_text(nested_body)

    result = _run_release(tmp_path, NEW_VERSION)

    assert result.returncode == 0, (
        f"release.sh should succeed on valid semver. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    # The 6th file (not in JSON_FILES) must be byte-for-byte unchanged.
    assert nested.read_text() == nested_body, (
        f"release.sh touched a file OUTSIDE its target list "
        f"(nested-manifest.json). This breaks the documented "
        f"single-top-level-version-key assumption. "
        f"content={nested.read_text()!r}"
    )

    # And the 5 real targets must be bumped as usual.
    expected_files = [
        tmp_path / ".claude-plugin" / "plugin.json",
        tmp_path / ".claude-plugin" / "marketplace.json",
        tmp_path / ".cursor-plugin" / "plugin.json",
        tmp_path / ".cursor-plugin" / "marketplace.json",
        tmp_path / ".claude" / ".atelier-version",
    ]
    for path in expected_files:
        content = path.read_text()
        assert NEW_VERSION in content, (
            f"{path.relative_to(tmp_path)} missing new version {NEW_VERSION}; "
            f"content={content!r}"
        )
        assert SEED_VERSION not in content, (
            f"{path.relative_to(tmp_path)} still contains seed version "
            f"{SEED_VERSION}; content={content!r}"
        )
