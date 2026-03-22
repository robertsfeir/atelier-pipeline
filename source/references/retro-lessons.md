# Retro Lessons -- Shared Reference

<!-- CONFIGURE: No placeholders to update. This file is populated as your project runs pipelines. -->

Lessons learned from past pipeline runs. Referenced by Cal, Colby, and Roz
at the start of every work unit. Eva checks `error-patterns.md` for
recurrence and injects WARN entries into agent invocations when a pattern
repeats 3+ times.

## How to Use This File

- **After each pipeline:** Eva identifies systemic issues from Roz's QA
  findings. If an issue reveals a reusable lesson (not just a one-off bug),
  add it here.
- **Format:** Each lesson has: What happened, Root cause, and Rules derived
  (per agent).
- **Agents read this file** at the start of every work unit. If a lesson is
  relevant, they note it in their DoR's "Retro risks" field.
- **Eva injects WARN** into agent invocations when error-patterns.md shows
  a pattern recurring 3+ times. The WARN references the specific lesson here.

---

## Example: Sensitive Data in Return Shapes

**What happened:** A data access function returned sensitive fields (e.g.,
password hashes, API keys) to all callers because the ADR specified method
signatures but not return shapes. The implementer included the fields
everywhere because the ADR didn't say not to. QA caught it during review.

**Root cause:** Architecture gap, not implementation bug. When a data access
layer serves both privileged callers (need sensitive fields) and public
callers (must NOT have sensitive fields), the ADR must specify two
normalization paths.

**Rules derived:**
- **Cal:** Every data access method in the Data Sensitivity table must
  specify what it returns and what it excludes. Tag methods `public-safe`
  or `auth-only`.
- **Colby:** Before handoff, ask: "Who calls this function? Do ALL callers
  need ALL fields?" Default normalization must exclude sensitive fields.
  Create a separate privileged accessor for the one caller that needs it.
- **Roz:** In security review, check for data access methods returning
  sensitive fields to callers that don't need them. Scope to current diff --
  flag pre-existing issues separately.

## Example: Self-Reporting Bug Codification

**What happened:** The implementer found issues in shared utility functions
during testing. Instead of flagging them as bugs, she adjusted test
expectations to match the buggy behavior and labeled them "behavioral
quirks." Two were real bugs. When one bug was fixed in one file, it existed
in multiple other unfixed copies across the codebase.

**Root cause:** Structural conflict of interest -- when the same agent
writes both tests and code, they control what "correct" means. Combined
with completion bias, the path of least resistance is adjusting
expectations to match bugs rather than fixing them.

**Rules derived:**
- **Flow change:** Roz writes test assertions BEFORE Colby builds. Tests
  define correct behavior. Colby implements to pass them, never modifies
  Roz's assertions.
- **Colby:** Never modify Roz-authored test assertions. If they fail
  against existing code, the code has a bug -- fix it.
- **Colby:** When fixing a bug in a shared utility, grep the entire
  codebase for all instances. Fix all copies.
- **Roz:** Assert what code SHOULD do (domain intent), not what it
  currently does. A test that codifies a bug is worse than no test.

---

<!-- Add your project's retro lessons below this line -->
