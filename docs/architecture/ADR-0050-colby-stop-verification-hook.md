# ADR-0050: Colby Stop Verification Hook

## Status
Accepted.

## Context
Colby ships work that compiles in her head but not always on disk. Type errors and formatting drift are the two failure modes that survive Colby's own Feedback Loop most often: tests pass at the unit level she touched, but a sibling file no longer typechecks, or an import was renamed and three call sites still reference the old name. Poirot catches these by reading the diff, but Poirot reads — Poirot does not run the compiler. Running `tsc --noEmit` (or `mypy`, or `go vet`) is the unique mechanical signal Poirot cannot replicate from a static read.

Lint is in scope for Poirot's read. Tests are in scope for Eva's mechanical test gate. Typecheck and auto-format sit in a hole between them: cheap, deterministic, project-stack-specific, and currently unenforced. Issue #44, narrowed by the user, asks for a SubagentStop hook that closes that hole and re-engages Colby on failure with zero reasoning required from her — the compiler's exit code is the entire signal.

The relevant integration points: `source/claude/hooks/log-agent-stop.sh` is the existing SubagentStop pattern (type: command, internal field parsing, exit 0 telemetry-only); `source/claude/hooks/enforce-colby-paths.sh` is the agent-scoped enforcement pattern (jq parse, exit 2 with stderr message); `.claude/settings.json` registers SubagentStop hooks without `if` clauses on `type: command` entries — agent-type gating must live inside the script. Per `feedback_no_background_agents.md`, this hook MUST be `type: command`, not `type: agent`.

## Options Considered

**1. Per-stop verification with auto-format and exit-2 re-engagement (chosen).** Add `enforce-colby-stop-verify.sh` to `source/claude/hooks/`, register it on SubagentStop alongside `log-agent-stop.sh`. Script gates on `agent_type == "colby"` (exits 0 immediately otherwise), runs the configured formatter in-place, then runs the configured typechecker. On typecheck failure, exit 2 with the compiler's last ~40 lines on stderr — Claude Code surfaces stderr to the agent and re-engages. On success, exit 0 silently. Cost: one tsc invocation per Colby stop (seconds on incremental, tens of seconds cold). Tradeoff worth it: the failure mode it catches (silent type breakage shipped to Poirot) costs a full review cycle.

**2. Pre-Ellis aggregate verification only.** Run typecheck once at the gate before Ellis commits, not per Colby stop. Cheaper (one run per pipeline, not per wave). Worse signal locality: by the time we discover the type error, three Colby stops are stacked behind it and the diff is harder to attribute. Rejected — the cost of a per-stop tsc run is small relative to a Colby re-spawn, and locality of the error to the wave that caused it is the whole point.

**3. Behavioral note in Colby persona ("run tsc before stopping").** Zero infrastructure. Per `feedback_mechanical_enforcement.md`, behavioral constraints are ignored — this option is a non-starter on this codebase by explicit user policy. Listed only to be honest about the alternative.

## Decision

Add `source/claude/hooks/enforce-colby-stop-verify.sh`, registered as a `type: command` SubagentStop hook without an `if` clause. The script gates internally: parses `agent_type` from stdin, exits 0 immediately for any value other than `colby`. For Colby stops, it loads `verify_commands` from `pipeline-config.json` (explicit config, not auto-detection — see Rationale), runs the configured formatter in-place, then the configured typechecker. Auto-format failures are logged but never block (formatting is a courtesy, not a gate). Typecheck failure exits 2 with the compiler's tail output on stderr; success exits 0 silently. Missing or empty `verify_commands` exits 0 cleanly — projects that haven't opted in see no behavior change.

A loop cap is enforced via a per-session counter file at `docs/pipeline/.colby-verify-attempts-${session_id}` — the script increments on each invocation and exits 0 (with a stderr warning) once the count exceeds `verify_max_attempts` (default 3). This prevents an infinite Colby<->hook loop when the type error is genuinely outside Colby's reach (e.g., a third-party dependency mismatch). Counter files are cleaned up by the existing `pre-compact.sh` hook (Colby will add this) and are session-scoped, so leakage is bounded.

Wave-execution mode (Colby Teammates in parallel) runs the hook once per teammate stop. The aggregate-at-wave-end alternative was considered and rejected: per-stop locality matters more than the small cost of N parallel tsc runs, and Teammates already operate on disjoint files within a wave.

Colby writes a behavioral test for the hook because regressing it silently re-introduces the failure class this ADR exists to close.

### Factual Claims
- `source/claude/hooks/log-agent-stop.sh` is registered on SubagentStop and exits 0 always (telemetry only).
- `.claude/settings.json` SubagentStop hooks use `type: command` without `if` clauses; agent-type gating is internal to scripts.
- `source/claude/hooks/enforce-colby-paths.sh` is the canonical pattern for jq-parsing stdin and exiting 2 with a stderr message.
- `.claude/pipeline-config.json` is the project-level config consumed by hooks (precedence: `.cursor/pipeline-config.json` then `.claude/pipeline-config.json`, per `enforce-sequencing.sh` lines 95-99).
- `feedback_no_background_agents.md` bans `type: agent` SubagentStop hooks.
- The brain-extractor `type: agent` SubagentStop hook in current settings.json predates that policy and is not the pattern to follow.

### LOC Estimate
~180 lines added across 4 files (new hook script ~120 lines, settings.json registration ~8 lines, pipeline-config.json schema additions ~8 lines, pytest ~50 lines). No existing files modified beyond config additions.

## Rationale

Explicit config (`verify_commands`) beats auto-detection because monorepos, polyglot repos, and projects with non-standard build setups make tsconfig.json/pyproject.toml/go.mod presence a poor proxy for "this is the command to run." Auto-detection looks zero-config until it picks the wrong tsconfig in a workspaces repo and Colby gets re-engaged on errors from a package she didn't touch. Explicit config makes opt-in obvious and skips cleanly when absent. The cost is a one-line addition to pipeline-config.json per project; the benefit is no false positives.

The new `pipeline-config.json` keys:

```json
{
  "verify_commands": {
    "format": "prettier --write .",
    "typecheck": "tsc --noEmit"
  },
  "verify_max_attempts": 3
}
```

Both keys are optional. Missing `verify_commands` skips the hook (exit 0). Missing `format` or `typecheck` skips that specific step. Missing `verify_max_attempts` defaults to 3.

The stateful loop-cap (option a from the constraints) was chosen over Colby's `maxTurns` because `maxTurns` is a Colby-side concern that fires after the loop has already wasted turns, and behavioral notes (option c) don't survive context resets. Temp-file hygiene is the cost: counter files in `docs/pipeline/.colby-verify-attempts-*` accumulate if `pre-compact.sh` doesn't clean them. If we see counter files older than a day surviving in CI, revisit.

If the chosen tsc command is too slow on a given project (cold runs >30s), the per-stop cost dominates and the hook becomes the bottleneck. Mitigation: projects can set `verify_commands.typecheck` to an incremental variant (`tsc --noEmit --incremental`) or disable typecheck and keep auto-format. The hook never fails closed on missing config — opt-in is the safety valve.

Out of scope: lint (Poirot reads it from the diff), test execution (Eva's mechanical test gate owns this), security scanning (Sentinel owns this).

Rollback sketch: remove the SubagentStop registration in `source/claude/hooks/hooks.json` (and Cursor equivalent), delete `enforce-colby-stop-verify.sh`, remove the two pipeline-config.json keys. No data migration; counter files are session-scoped temp state and self-expire.

## Falsifiability

The behavioral test at `tests/hooks/test_adr_0050_stop_verification.py` stubs the configured typecheck command with a script that exits 1, invokes `enforce-colby-stop-verify.sh` with a synthesized SubagentStop stdin payload (agent_type=colby), and asserts exit code 2 plus non-empty stderr. A second test case with agent_type=sarah asserts exit code 0 with no command invocation. A third test case with `verify_commands` absent from pipeline-config.json asserts exit code 0.

We'd know this decision was wrong if: (a) Colby's re-engagement on typecheck failure does not actually fix the error and we hit `verify_max_attempts` more than 10% of the time across a month of pipelines — meaning the hook is reporting errors Colby cannot resolve and the loop cap is doing all the work; or (b) per-stop verification cost adds more than 20% to wave duration on the median project, in which case option 2 (aggregate-at-wave-end) becomes the better tradeoff. Revisit at either threshold.

## Sources
- `source/claude/hooks/log-agent-stop.sh` — SubagentStop hook pattern.
- `source/claude/hooks/enforce-colby-paths.sh` — agent-scoped enforcement, exit-2 pattern.
- `source/claude/hooks/enforce-sequencing.sh:95-99` — pipeline-config.json precedence.
- `.claude/settings.json:86-106` — SubagentStop registration.
- `feedback_no_background_agents.md` — `type: agent` SubagentStop ban.
- `feedback_mechanical_enforcement.md` — behavioral constraints insufficient.
