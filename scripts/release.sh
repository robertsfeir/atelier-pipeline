#!/usr/bin/env bash
# Bump the atelier-pipeline version across all 5 version files in a single
# invocation. Not atomic: the script performs 4 independent `sed` calls
# followed by one file overwrite; a failure on any step leaves earlier files
# already mutated. `set -e` aborts on the first failure, and the operator
# must re-run (or manually revert) to restore consistency. Acceptable for a
# hand-run release utility.
#
# Usage: scripts/release.sh <version>
#   e.g. scripts/release.sh 3.38.0
#
# Updates:
#   .claude-plugin/plugin.json        (top-level "version")
#   .claude-plugin/marketplace.json   (plugins[0].version)
#   .cursor-plugin/plugin.json        (top-level "version")
#   .cursor-plugin/marketplace.json   (plugins[0].version)
#   .claude/.atelier-version          (plain text)
#
# Does NOT: edit CHANGELOG, stage, commit, tag, or push. Prints a checklist
# reminding the operator to do those steps manually. Safety boundary.
#
# ---------------------------------------------------------------------------
# SINGLE-VERSION-KEY ASSUMPTION (load-bearing)
# ---------------------------------------------------------------------------
# Each of the 4 target JSON files MUST contain exactly ONE `"version": "X.Y.Z"`
# occurrence -- the intended top-level (or plugins[0]) version string. The sed
# pattern below is anchored on the literal key name and a semver value, but it
# is NOT scoped to a specific JSON path. If a target file ever gains a NESTED
# `"version"` key (for example, an embedded dependency manifest such as
# `"dependencies": { "foo": { "version": "1.2.3" } }`), sed will happily
# rewrite the wrong occurrence -- silently, with no error.
#
# The test suite locks this assumption via `test_release_rejects_nested_version_keys`
# in tests/scripts/test_release.py, which pins a nested-key file as UNCHANGED
# after a run. If you change the sed strategy here, keep that test in sync
# (or replace it with something stricter, such as jq path-scoped edits).
# ---------------------------------------------------------------------------

set -euo pipefail

VERSION="${1:?Usage: scripts/release.sh <version> (e.g. 3.38.0)}"

# Validate canonical semver: MAJOR.MINOR.PATCH with no leading zeros, no
# pre-release suffix, no build metadata, no `v` prefix. Each component is
# either `0` or a non-zero digit followed by more digits. Rejects inputs
# such as `01.00.00`, `1.2.3-rc1`, `1.2.3+build.1`, `v3.37.0`, `3.37`.
if ! [[ "$VERSION" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
  echo "error: version '$VERSION' is not valid semver (expected canonical MAJOR.MINOR.PATCH with no leading zeros, no pre-release/build metadata, no 'v' prefix -- e.g. 3.38.0)" >&2
  echo "Usage: scripts/release.sh <version>" >&2
  exit 1
fi

# Resolve repo root from this script's own location so it works from any CWD.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# JSON files: replace the sole `"version": "X.Y.Z"` line. Pattern is
# semver-anchored so non-version strings containing the word "version"
# cannot be matched. sed is idempotent for literal replacements.
JSON_FILES=(
  ".claude-plugin/plugin.json"
  ".claude-plugin/marketplace.json"
  ".cursor-plugin/plugin.json"
  ".cursor-plugin/marketplace.json"
)

updated=0
for rel in "${JSON_FILES[@]}"; do
  path="$REPO_ROOT/$rel"
  if [ ! -f "$path" ]; then
    echo "error: expected file not found: $rel" >&2
    exit 1
  fi
  # -i.bak is portable across BSD (macOS) and GNU sed.
  sed -i.bak -E "s/\"version\"[[:space:]]*:[[:space:]]*\"[0-9]+\.[0-9]+\.[0-9]+\"/\"version\": \"${VERSION}\"/" "$path"
  rm -f "$path.bak"
  updated=$((updated + 1))
done

# Plain-text version file: overwrite with VERSION + newline.
VERSION_FILE="$REPO_ROOT/.claude/.atelier-version"
if [ ! -f "$VERSION_FILE" ]; then
  echo "error: expected file not found: .claude/.atelier-version" >&2
  exit 1
fi
printf '%s\n' "$VERSION" > "$VERSION_FILE"
updated=$((updated + 1))

cat <<EOF
Updated ${updated} files to v${VERSION}.

Next steps (manual -- release.sh deliberately does not perform these):
  1. Edit CHANGELOG.md: promote [Unreleased] -> [${VERSION}] - $(date +%Y-%m-%d)
  2. git commit -m 'chore(release): bump version to ${VERSION}'
  3. Push when ready.
EOF
