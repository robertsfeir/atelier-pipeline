# Step Sizing Gate

<!-- Part of atelier-pipeline. Referenced by Cal during ADR production. -->
<!-- CONFIGURE: No placeholders to update. -->

After drafting the implementation plan, apply these five tests to each step.
Steps touching 10+ files (files_to_create + files_to_modify) MUST pass all
five. Steps under 10 files are reviewed at Cal's judgment but should still
pass.

| # | Test | Question | Fail Action |
|---|------|----------|-------------|
| S1 | Demoable | Can you state what this step enables in one user-facing sentence? ("After this step, I can ___") | Split along demo boundaries -- each demoable behavior becomes its own step |
| S2 | Context-bounded | Does Colby need <= 8 files (create + modify) to implement it? | Extract excess files into a prerequisite or follow-up step |
| S3 | Independently verifiable | Can Roz test this step without the next one existing? | Split so each verifiable behavior is its own step |
| S4 | Revert-cheap | If Roz fails it, can Colby redo it in one fresh invocation? | Split until each piece is one-invocation sized |
| S5 | Already small | Is this step <= 6 files with one clear behavior? | Do NOT split -- over-splitting wastes orchestration overhead |

## Evidence

Sub-slicing from ~15 files/step to ~8 files/step improved first-pass QA from
57% to 93% and reduced rework findings by 90% (same model, same pipeline,
same project -- only variable was step granularity). Context window research
shows LLM accuracy degrades above ~32k tokens of effective context.

## Split Heuristics

When a step fails the gate, look for these seams:

| Seam | Example |
|------|---------|
| CRUD separate from lifecycle/state machine | Firm create/list vs suspend/archive |
| Read-only separate from mutations | User search/list vs suspend/grant-PM |
| Foundation separate from first consumer | Auth guard + layout vs audit log page |
| Security separate from config CRUD | AI settings vs key encryption/rotation |
| Data pipeline separate from dashboard | Cost event logging vs cost trend UI |
| Schema/job separate from UI | Analytics aggregation vs metrics page |

Use alphabetical sub-numbering (1a, 1b, 2a, 2b, 2c) for sub-sliced steps.
Dependencies within a parent flow forward (2a before 2b before 2c).

## Step Count

Step count is not a quality signal. 15 well-sized steps is better than 8
over-packed steps. The goal is reliable execution, not minimal step count.

## Darwin Review Trigger

This gate reflects current model capabilities (2026). If Darwin telemetry
shows first-pass QA >= 90% on steps exceeding the file threshold, revisit
the trigger.
