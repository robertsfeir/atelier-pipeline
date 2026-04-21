#!/bin/bash
# pipeline-state-path.sh -- Per-worktree session state path resolver
# Implements ADR-0032 Decision: session state files live out-of-repo,
# in a per-worktree directory under ~/.atelier/pipeline/.
#
# Exports two distinct functions:
#   session_state_dir()     -- per-worktree, out-of-repo
#   error_patterns_path()   -- in-repo, unchanged (ADR-0032 Decision)
#
# Non-blocking: exits 0 on every error path. Falls back to docs/pipeline/
# if resolution fails. Retro lesson #003 compliant.
#
# Usage (from another script):
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "$SCRIPT_DIR/pipeline-state-path.sh"
#   STATE_DIR=$(session_state_dir)
#   ERR_PATH=$(error_patterns_path)

# ─── session_state_dir ────────────────────────────────────────────────────────
#
# Returns an absolute path of the form:
#   ~/.atelier/pipeline/{project-slug}/{8-char-hash}/
#
# Resolution order:
#   (a) CLAUDE_PROJECT_DIR env var  -- set by Claude Code
#   (b) CURSOR_PROJECT_DIR env var  -- set by Cursor
#   (c) pwd                         -- fallback to current directory
#
# On any failure (missing sha256sum, unresolvable path, mkdir error) the
# function prints the legacy path docs/pipeline and exits 0 -- the caller
# gets a valid (relative) path it can still use.

session_state_dir() {
  local project_root=""

  # Resolve project root — only use the out-of-repo path when an explicit
  # project directory env var is set. Without one, we cannot distinguish a
  # transient subprocess (e.g. a test runner with cwd=/tmp/xxx) from a real
  # worktree, so we fall back to the legacy in-repo path.
  if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    project_root="$CLAUDE_PROJECT_DIR"
  elif [ -n "${CURSOR_PROJECT_DIR:-}" ]; then
    project_root="$CURSOR_PROJECT_DIR"
  else
    # No explicit project env var — use the legacy relative path so callers
    # reading docs/pipeline/ relative to cwd continue to work correctly.
    echo "docs/pipeline"
    return 0
  fi

  # Resolve absolute path
  project_root="$(cd "$project_root" 2>/dev/null && pwd)" || {
    echo "docs/pipeline"
    return 0
  }

  # Compute project slug from the last path component
  local project_slug
  project_slug="$(basename "$project_root" 2>/dev/null)" || {
    echo "docs/pipeline"
    return 0
  }

  # Compute 8-char hash of the absolute worktree root
  local worktree_hash
  if command -v sha256sum &>/dev/null; then
    # The || guard fires on a non-zero subshell exit (pipeline failure, e.g. sha256sum
    # itself exits non-zero). It does NOT protect against sha256sum silently producing
    # empty output while head exits 0 — that case is caught by the
    # [ "${#worktree_hash}" -ne 8 ] length check immediately below.
    worktree_hash="$(printf '%s' "$project_root" | sha256sum 2>/dev/null | head -c 8)" || {
      echo "docs/pipeline"
      return 0
    }
  elif command -v shasum &>/dev/null; then
    # macOS fallback
    # Same || semantics as above: guards subshell non-zero exits only.
    # The primary guard for empty/partial hash output is the length check below.
    worktree_hash="$(printf '%s' "$project_root" | shasum -a 256 2>/dev/null | head -c 8)" || {
      echo "docs/pipeline"
      return 0
    }
  else
    # No sha utility available -- fall back
    echo "docs/pipeline"
    return 0
  fi

  # Validate hash produced 8 chars (primary guard for empty/partial hash output)
  if [ "${#worktree_hash}" -ne 8 ]; then
    echo "docs/pipeline"
    return 0
  fi

  local state_dir="${HOME}/.atelier/pipeline/${project_slug}/${worktree_hash}"

  # Ensure directory exists (mkdir -p is idempotent)
  mkdir -p "$state_dir" 2>/dev/null || {
    echo "docs/pipeline"
    return 0
  }

  echo "$state_dir"
  return 0
}

# ─── error_patterns_path ──────────────────────────────────────────────────────
#
# Returns the in-repo path for error-patterns.md.
# Per ADR-0032 Decision: error-patterns.md stays in-repo so it can be committed
# and shared with the team. It is NOT per-worktree.
#
# Returns a relative path (docs/pipeline/error-patterns.md) so callers work
# correctly regardless of current working directory, consistent with the
# legacy behaviour session-boot.sh had before this helper was introduced.

error_patterns_path() {
  echo "docs/pipeline/error-patterns.md"
  return 0
}
