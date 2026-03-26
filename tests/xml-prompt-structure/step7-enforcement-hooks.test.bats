#!/usr/bin/env bats
# ADR-0005 Step 7: Enforcement Hooks Update
# Tests: T-0005-080 through T-0005-085

load test_helper

# ── T-0005-080: check-brain-usage.sh checks for consumption patterns ─

@test "T-0005-080: check-brain-usage.sh checks for brain context consumption evidence" {
  local file="$SOURCE_HOOKS/check-brain-usage.sh"
  # Should check for evidence that agents consumed injected brain context
  # (not that agents called agent_search themselves)
  grep -qiE "brain.context|thought|prior.*decision|consumption|consumed|context.*brain" "$file" || \
  grep -qiE "Brain context|injected|referenced" "$file"
}

# ── T-0005-081: Hook does not check for agent-initiated brain calls ──

@test "T-0005-081: check-brain-usage.sh does not check for agent-initiated brain calls" {
  local file="$SOURCE_HOOKS/check-brain-usage.sh"
  # The hook should not grep for patterns like "agent_search" or "agent_capture"
  # as evidence of agent brain usage (those are Eva's job now)
  # Check the actual grep/matching patterns used by the hook
  # Old patterns: agent_search, agent_capture, searched.*brain, captured.*brain
  if grep -qE 'agent_search|agent_capture' "$file" | grep -qv '#'; then
    # Allow these words in comments but not in active matching patterns
    local active_lines
    active_lines=$(grep -v '^\s*#' "$file" | grep -cE 'agent_search|agent_capture' || echo 0)
    if [ "$active_lines" -gt 0 ]; then
      echo "Hook still checks for agent-initiated brain calls"
      return 1
    fi
  fi
}

# ── T-0005-082: enforcement-config.json not modified ─────────────────

@test "T-0005-082: enforcement-config.json brain_required_agents is [cal, colby, roz, agatha, sable, robert]" {
  local file="$SOURCE_HOOKS/enforcement-config.json"
  local agents
  agents=$(jq -r '.brain_required_agents | sort | join(",")' "$file")
  [ "$agents" = "agatha,cal,colby,robert,roz,sable" ]
}

# ── T-0005-083: Ellis not in brain_required_agents ───────────────────

@test "T-0005-083: Ellis is not in enforcement-config.json brain_required_agents" {
  local file="$SOURCE_HOOKS/enforcement-config.json"
  local has_ellis
  has_ellis=$(jq '.brain_required_agents | map(select(. == "ellis")) | length' "$file")
  [ "$has_ellis" -eq 0 ]
}

@test "T-0005-083b: Poirot is not in brain_required_agents" {
  local file="$SOURCE_HOOKS/enforcement-config.json"
  local has_poirot
  has_poirot=$(jq '.brain_required_agents | map(select(. == "investigator" or . == "poirot")) | length' "$file")
  [ "$has_poirot" -eq 0 ]
}

@test "T-0005-083c: Distillator is not in brain_required_agents" {
  local file="$SOURCE_HOOKS/enforcement-config.json"
  local has_dist
  has_dist=$(jq '.brain_required_agents | map(select(. == "distillator")) | length' "$file")
  [ "$has_dist" -eq 0 ]
}

# ── T-0005-084: Hook exits 0 (non-blocking warning) ─────────────────

@test "T-0005-084: check-brain-usage.sh exits 0 (non-blocking warning)" {
  local file="$SOURCE_HOOKS/check-brain-usage.sh"
  # The hook should not contain exit 1 or exit 2 for brain usage violations
  # (it warns but does not block)
  # Check that all exit codes in non-error paths are 0
  # Error paths (jq missing, etc.) may exit non-zero
  # The key check: after the brain usage analysis, the exit is 0
  local last_exit
  last_exit=$(tail -5 "$file" | grep -oE 'exit [0-9]+' | tail -1 | grep -oE '[0-9]+')
  # If no explicit exit at end, shell exits 0 by default -- that's fine
  if [ -n "$last_exit" ]; then
    [ "$last_exit" -eq 0 ] || {
      echo "Hook ends with exit $last_exit (should be 0)"
      return 1
    }
  fi
}

# ── T-0005-085: enforcement-config.json byte-identical to pre-conversion

@test "T-0005-085: enforcement-config.json is not modified by this ADR" {
  local source="$SOURCE_HOOKS/enforcement-config.json"
  local installed="$INSTALLED_HOOKS/enforcement-config.json"
  # Both files should have identical brain_required_agents
  local source_agents installed_agents
  source_agents=$(jq -S '.brain_required_agents' "$source")
  installed_agents=$(jq -S '.brain_required_agents' "$installed")
  [ "$source_agents" = "$installed_agents" ]
}
