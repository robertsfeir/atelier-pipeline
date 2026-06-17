## DoR: Diff Metadata
**Files:** 6 | **Added:** ~300 | **Removed:** ~80
**Functions modified:** `_roster_check` (enforce-brain-capture-pending.sh, both source and installed copies)
**New dependencies:** none

## Exercised

Hook invoked with `{"agent_type":"sable"}` via bash -x. Trace confirmed: `sable` hits the `robert-spec|sable|sable-ux` bypass in `_roster_check` (returns 0), passes the gate, then exits early because `.brain-unavailable` is present. The bypass itself is confirmed reachable. Hook invoked again with `{"agent_type":"robert-spec"}` -- same bypass path confirmed. Both exit 0 with correct behavior.

Pipeline-config files verified: `robert-spec: { enabled: true, firing: "core" }` present in both `.claude/pipeline-config.json` and `source/shared/pipeline/pipeline-config.json`. `sable` absent from both roster configs, as specified.

Diff of source template vs installed pipeline-config: differences are project-local customizations (project_name, sentinel/teams/ellis enabled) -- not regressions.

## DoD: Verification
**Findings:** 2 | **Categories:** logic, resources | **Grep verified:** `_roster_check`, `robert-spec`, `sable`, `agatha`, `atomically`, `json.dump` | **Exercised:** `enforce-brain-capture-pending.sh` with `sable` and `robert-spec` agent_type inputs; `pipeline-config.json` diff across source/installed targets

## Findings
| # | Location | Severity | Category | Description | Suggested Fix |
|---|----------|----------|----------|-------------|---------------|
| 1 | `skills/pipeline-setup/SKILL.md` line 927, `.cursor-plugin/skills/pipeline-setup/SKILL.md` line 927 | FIX-REQUIRED | Logic | The "Write the roster" instruction says "include it with the chosen firing position" for each selected agent, but Agatha has no firing-position prompt (hardcoded to `pipeline-end`). The example JSON only shows Agatha disabled. An executor following the write instruction literally could write `firing: "on-demand"` for an enabled Agatha, copying the disabled-state pattern. Ellis has the same implicit-firing pattern but appears as `"ellis": { "enabled": true, "firing": "pipeline-end" }` in the example -- Agatha's enabled counterpart is missing. | Add an enabled-Agatha example to the "Example roster JSON" block, e.g. `"agatha": { "enabled": true, "firing": "pipeline-end" }`, and update the write instruction to say "for Agatha, always write `firing: pipeline-end`" explicitly. |
| 2 | `skills/pipeline-setup/SKILL.md` line 498, `.cursor-plugin/skills/pipeline-setup/SKILL.md` line 498 | NIT | Resources | Step 0g describes the `dashboard_mode` removal as happening "atomically" but the python snippet uses `json.dump(d, open(p, 'w'), indent=2)` -- which truncates the file before the write completes, so a mid-write failure leaves `pipeline-config.json` corrupt. Step 0h (settings.json) uses `with open(p, 'w') as f:` which at least ensures the file is closed on exception. The claim of atomicity is inaccurate. | Either drop the word "atomically" from the Step 0g description, or replace the one-liner with a write-to-tempfile + `os.replace()` pattern (which is truly atomic on POSIX). |
