#!/bin/bash
# Session boot data collector -- SessionStart hook (Cursor platform mirror)
# Reads pipeline state, config, and environment to produce structured JSON
# for Eva's boot sequence (steps 1-3d). Brain interactions (steps 4-6) remain
# in Eva's boot sequence since they require MCP tool calls.
#
# Cursor platform mirror of source/claude/hooks/session-boot.sh (ADR-0037 Step C1).
# The shared pipeline-state-path.sh helper resolves CURSOR_PROJECT_DIR (and
# CLAUDE_PROJECT_DIR) so this script requires no platform-specific branching.
#
# Non-blocking: exits 0 always. No network calls, no brain calls.
# Retro lesson #003 compliant.

# Do NOT use set -e -- graceful degradation (retro lesson #003)
set -uo pipefail

INPUT=$(cat 2>/dev/null) || true

# Source the pipeline-state-path helper (ADR-0032 implementation)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/pipeline-state-path.sh" ]; then
  # shellcheck source=pipeline-state-path.sh
  source "$SCRIPT_DIR/pipeline-state-path.sh" 2>/dev/null || true
fi

# Source shared hook library (ADR-0034 Wave 2 Step 2.1)
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/hook-lib.sh" ]; then
  source "$SCRIPT_DIR/hook-lib.sh" 2>/dev/null || true
fi

# Define fallback if helper did not load
if ! command -v session_state_dir &>/dev/null; then
  session_state_dir() { echo "docs/pipeline"; }
fi
if ! command -v error_patterns_path &>/dev/null; then
  error_patterns_path() { echo "docs/pipeline/error-patterns.md"; }
fi

# Defaults
PIPELINE_ACTIVE=false
PHASE="idle"
FEATURE=""
STALE_CONTEXT=false
BRANCHING_STRATEGY="trunk-based"
AGENT_TEAMS_ENABLED=false
AGENT_TEAMS_ENV=false
CUSTOM_AGENT_COUNT=0
CI_WATCH_ENABLED=false
DARWIN_ENABLED=false
DASHBOARD_MODE="none"
PROJECT_NAME=""
SENTINEL_ENABLED=false
DEPS_AGENT_ENABLED=false
WARN_AGENTS="[]"

# Resolve config_dir: try .claude first, fall back to .cursor
CONFIG_DIR=""
if [ -d ".claude" ]; then
  CONFIG_DIR=".claude"
elif [ -d ".cursor" ]; then
  CONFIG_DIR=".cursor"
fi

# --- Resolve per-worktree state directory (ADR-0032) ---
STATE_DIR=$(session_state_dir)

# --- Read pipeline-state.md ---
PIPELINE_STATE_FILE="$STATE_DIR/pipeline-state.md"
if [ -f "$PIPELINE_STATE_FILE" ]; then
  if command -v jq &>/dev/null; then
    PHASE=$(cat "$PIPELINE_STATE_FILE" | hook_lib_pipeline_status_field phase 2>/dev/null || echo "idle")
    [ -z "$PHASE" ] && PHASE="idle"
    FEATURE=$(cat "$PIPELINE_STATE_FILE" | hook_lib_pipeline_status_field feature 2>/dev/null || echo "")
    if [ "$PHASE" != "idle" ] && [ "$PHASE" != "complete" ] && [ -n "$FEATURE" ]; then
      PIPELINE_ACTIVE=true
    fi
  fi
fi

# --- Read context-brief.md (check for stale context) ---
CONTEXT_BRIEF="$STATE_DIR/context-brief.md"
if [ -f "$CONTEXT_BRIEF" ] && [ -n "$FEATURE" ]; then
  BRIEF_FEATURE=$(grep -i "feature" "$CONTEXT_BRIEF" 2>/dev/null | head -1 || true)
  if [ -n "$BRIEF_FEATURE" ] && [ -n "$FEATURE" ]; then
    if ! echo "$BRIEF_FEATURE" | grep -qi "$FEATURE" 2>/dev/null; then
      STALE_CONTEXT=true
    fi
  fi
fi

# --- Read error-patterns.md (warn agents with Recurrence >= 3) ---
# error-patterns.md stays in-repo per ADR-0032 (shared with team via git)
ERROR_PATTERNS=$(error_patterns_path)
if [ -f "$ERROR_PATTERNS" ] && command -v grep &>/dev/null; then
  WARN_LIST=$(grep -i "recurrence.*[3-9]\|recurrence.*[1-9][0-9]" "$ERROR_PATTERNS" 2>/dev/null | \
    grep -oi "agent[s]*[: ]*[a-z,]*" 2>/dev/null | \
    sed 's/agent[s]*[: ]*//' | tr ',' '\n' | tr -d ' ' | sort -u | \
    awk 'NF{printf "\"%s\",",$0}' | sed 's/,$//' || true)
  if [ -n "$WARN_LIST" ]; then
    WARN_AGENTS="[$WARN_LIST]"
  fi
fi

# --- Read pipeline-config.json ---
CONFIG_FILE=""
if [ -n "$CONFIG_DIR" ]; then
  CONFIG_FILE="$CONFIG_DIR/pipeline-config.json"
fi
if [ -n "$CONFIG_FILE" ] && [ -f "$CONFIG_FILE" ] && command -v jq &>/dev/null; then
  BRANCHING_STRATEGY=$(jq -r '.branching_strategy // "trunk-based"' "$CONFIG_FILE" 2>/dev/null || echo "trunk-based")
  AGENT_TEAMS_ENABLED=$(jq -r '.agent_teams_enabled // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
  CI_WATCH_ENABLED=$(jq -r '.ci_watch_enabled // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
  DARWIN_ENABLED=$(jq -r '.darwin_enabled // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
  DASHBOARD_MODE=$(jq -r '.dashboard_mode // "none"' "$CONFIG_FILE" 2>/dev/null || echo "none")
  SENTINEL_ENABLED=$(jq -r '.sentinel_enabled // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
  DEPS_AGENT_ENABLED=$(jq -r '.deps_agent_enabled // false' "$CONFIG_FILE" 2>/dev/null || echo "false")
  CFG_PROJECT_NAME=$(jq -r '.project_name // ""' "$CONFIG_FILE" 2>/dev/null || echo "")
  if [ -n "$CFG_PROJECT_NAME" ]; then
    PROJECT_NAME="$CFG_PROJECT_NAME"
  fi
fi

# --- Derive project_name if not set ---
if [ -z "$PROJECT_NAME" ]; then
  REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)
  if [ -n "$REMOTE_URL" ]; then
    PROJECT_NAME=$(basename "$REMOTE_URL" .git)
  else
    PROJECT_NAME=$(basename "$PWD")
  fi
fi

# --- Count custom agents ---
if [ -n "$CONFIG_DIR" ] && [ -d "$CONFIG_DIR/agents" ]; then
  CORE_AGENTS="cal colby roz ellis agatha robert sable investigator distillator sentinel darwin deps brain-extractor robert-spec sable-ux"
  for agent_file in "$CONFIG_DIR/agents/"*.md; do
    [ -f "$agent_file" ] || continue
    AGENT_NAME=$(grep -m1 "^name:" "$agent_file" 2>/dev/null | sed 's/name:[[:space:]]*//' | tr -d '"' | tr -d "'" || true)
    if [ -z "$AGENT_NAME" ]; then
      continue
    fi
    IS_CORE=false
    for core in $CORE_AGENTS; do
      if [ "$AGENT_NAME" = "$core" ]; then
        IS_CORE=true
        break
      fi
    done
    if [ "$IS_CORE" = "false" ]; then
      CUSTOM_AGENT_COUNT=$((CUSTOM_AGENT_COUNT + 1))
    fi
  done
fi

# --- Check CLAUDE_AGENT_TEAMS env var ---
if [ -n "${CLAUDE_AGENT_TEAMS:-}" ]; then
  AGENT_TEAMS_ENV=true
fi

# --- Output JSON ---
# Escape string values to prevent JSON injection from double quotes/backslashes
# Delegates to hook_lib_json_escape (jq -Rs based, fixes S22 regression)
# Falls back to sed-based escaping if hook-lib was not loaded
json_escape() {
  if command -v hook_lib_json_escape &>/dev/null 2>&1; then
    # hook_lib_json_escape reads stdin and returns a full JSON string literal (with quotes)
    # Strip the surrounding quotes so the output matches the original interface
    local escaped
    escaped=$(printf '%s' "$1" | hook_lib_json_escape 2>/dev/null) || true
    # Remove surrounding double-quotes added by jq -Rs
    escaped="${escaped#\"}"
    escaped="${escaped%\"}"
    printf '%s' "$escaped"
  else
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/	/\\t/g'
  fi
}

cat <<EOF
{
  "pipeline_active": $PIPELINE_ACTIVE,
  "phase": "$(json_escape "$PHASE")",
  "feature": "$(json_escape "$FEATURE")",
  "stale_context": $STALE_CONTEXT,
  "warn_agents": $WARN_AGENTS,
  "branching_strategy": "$(json_escape "$BRANCHING_STRATEGY")",
  "agent_teams_enabled": $AGENT_TEAMS_ENABLED,
  "agent_teams_env": $AGENT_TEAMS_ENV,
  "custom_agent_count": $CUSTOM_AGENT_COUNT,
  "ci_watch_enabled": $CI_WATCH_ENABLED,
  "darwin_enabled": $DARWIN_ENABLED,
  "dashboard_mode": "$(json_escape "$DASHBOARD_MODE")",
  "project_name": "$(json_escape "$PROJECT_NAME")",
  "sentinel_enabled": $SENTINEL_ENABLED,
  "deps_agent_enabled": $DEPS_AGENT_ENABLED,
  "state_dir": "$(json_escape "$STATE_DIR")"
}
EOF

exit 0
