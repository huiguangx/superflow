# Artifact Contract

Use `.planning/` as the durable handoff layer. Keep artifacts concise and update them atomically when possible. Do not create duplicate documents for information already present in an existing project format.

## Layout

```text
.planning/
  PROJECT.md
  REQUIREMENTS.md
  ROADMAP.md
  STATE.md
  FINAL-REVIEW.md
  FINAL-VERIFICATION.md
  phases/
    01-<slug>/
      01-CONTEXT.md
      01-PLAN.md
      01-VALIDATION.md
      01-SUMMARY.md
      01-REVIEW.md
      01-VERIFICATION.md
```

Create the two `FINAL-*` files only during branch review and milestone verification. For a small one-phase change, keep this layout but use one phase and one or a few vertical slices. Do not invent more files.

## PROJECT.md

Preserve the authority from which the contract was derived:

```markdown
# Project Source

## Source Request
The user's request, constraints, and referenced inputs, preserved without dropping details.

## Planning Clarifications
- Exact user decisions made before approval.

## Repository Baseline
- Root, branch, revision, dirty paths, and governing instruction files.
```

Do not replace the source request with the planner's interpretation. The plan reviewer uses this file to detect omissions.

## STATE.md

Place YAML frontmatter first:

```yaml
---
superflow_state_version: 1
workflow_id: null
status: planning
autonomy: supervised
active_phase: null
active_task: null
next_action: plan
assurance: full
request_digest: null
approved_contract_digest: null
baseline_revision: null
reviewed_tree_fingerprint: null
verified_contract_digest: null
verified_tree_fingerprint: null
plan_revision: 0
review_attempt: 0
verification_attempt: 0
---
```

Allowed `status` values:

- `planning`
- `awaiting_approval`
- `approved`
- `running`
- `blocked`
- `verified_complete`

Machine status values are lowercase. Human-facing summaries may say `VERIFIED_COMPLETE` or `BLOCKED`, but `STATE.md` and artifact frontmatter use the lowercase values above.

Allowed `assurance` values:

- `full`
- `reduced-no-isolation`
- `reduced-external-checks`
- `reduced-local-only`

Allowed `next_action` values:

- `plan`
- `approve`
- `execute-phase`
- `review-task`
- `verify-phase`
- `gap-close`
- `review-branch`
- `verify-milestone`
- `complete`
- `none`

Binding rules:

- `request_digest` covers the source request and planning clarifications in `PROJECT.md`.
- `approved_contract_digest` covers `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, and every approved `CONTEXT.md`; these behavior, scope, decision, and permission records are immutable after approval.
- A product-tree fingerprint identifies the current commit plus content hashes for changed and relevant untracked product files. Exclude `.planning/` and other Superflow evidence artifacts so recording evidence cannot invalidate itself. On a non-git project, hash the reviewed product file set with paths in stable order.
- Recompute bindings on resume and before every worker, review, and verification handoff. A contract mismatch requires approval again. A product-tree change invalidates prior review or verification evidence.

Use this deterministic hash rule:

```text
sha256:<hash>
```

For artifact digests, concatenate each covered file in stable path order as:

```text
--- path/to/file
<file bytes>
```

Hash that byte stream with SHA-256. Missing covered files are a blocker after approval.

For product-tree fingerprints, concatenate `HEAD:<rev-or-none>` plus the same stable-path stream for changed and relevant untracked product files, excluding `.planning/`, `.git/`, build outputs, dependency directories, and Superflow evidence artifacts. If git is unavailable, use `HEAD:none`.

The body contains:

```markdown
# Superflow State

## Position
- Phase: 1/3
- Task: 01-02

## Phase Ledger
| Phase | Status | Evidence |
|---|---|---|
| 01 | pending | - |

## Slice Ledger
| Slice | Depends on | Status | Review | Evidence |
|---|---|---|---|---|
| 01-01 | - | pending | pending | - |

## Decisions Since Approval
- D-07: Followed existing repository transaction pattern.

## Blocker
None.
```

Allowed slice states are `pending`, `running`, `implemented`, `reviewed`, and `verified`. Update state after every slice transition, approved plan, completed review, completed verification, and blocker. Files and git history outrank conversational memory after compaction.

Do not hand-calculate or reimplement bindings. Run `../scripts/superflow_gate.py` from the orchestrator at each gate. A review or verification report whose subject fingerprint is stale is invalid even when its prose says `clean` or `passed`.

## REQUIREMENTS.md

Assign stable IDs:

```markdown
# Requirements

## Goal
One observable outcome.

## Functional
- REQ-01: Given ..., when ..., then ...

## Quality
- Q-01: No framework-owned memory is freed by the caller.

## Non-Goals
- NG-01: Production deployment is excluded.

## Permissions
- New dependencies: disallowed unless explicitly listed
- External services: disallowed unless explicitly listed
- Destructive operations: disallowed unless explicitly authorized
```

Requirements describe behavior and constraints, not implementation guesses.

## ROADMAP.md

Keep the roadmap short and phase-oriented:

```markdown
# Roadmap

| Phase | Goal | Requirements | Status |
|---|---|---|---|
| 01 | Observable phase outcome | REQ-01, Q-01 | pending |
```

Use one phase for a small coherent change. Add phases only when outcomes are independently releasable or too large for one fresh worker context.

## CONTEXT.md

Capture shared language and decisions:

```markdown
# Phase 01 Context

## Boundary
What this phase delivers and excludes.

## Domain Language
| Term | Exact meaning | Avoid |
|---|---|---|

## Decisions
- D-01: ...

## Impact Surface
| Entry point | Call path | Runtime variant | Ownership/lifecycle | Error path | Existing test |
|---|---|---|---|---|---|

## Existing Patterns
- `path:symbol` - pattern to reuse and why.
```

Include sibling runtime modes, direct callers, public interfaces, resource ownership, migrations, and error paths. This is the main defense against hidden variants omitted from the initial request.

## PLAN.md

Use vertical slices. A slice must be independently reviewable and verifiable.

```markdown
# Phase 01 Plan

## Goal
Observable phase outcome.

## Global Constraints
- REQ-01, Q-01, D-01

### Slice 01-01: <behavior>

**Covers:** REQ-01, Q-01
**Consumes:** existing interfaces and exact symbols
**Produces:** new or changed public behavior
**Expected files:** paths, not an absolute allowlist
**Oracle:** exact command and expected observation
**Rollback:** how to reverse safely

Steps:
1. Establish RED or baseline evidence.
2. Implement the smallest complete behavior.
3. Run focused checks.
4. Run required broader checks.
```

Do not paste full production implementations into plans. Exact signatures, invariants, data shapes, commands, and acceptance criteria belong; speculative code does not.

## VALIDATION.md

Every requirement and decision needs an oracle before coding:

```markdown
# Phase 01 Validation

| ID | Behavior or constraint | Oracle | Expected result | Automated | Risk fallback |
|---|---|---|---|---|---|
| REQ-01 | ... | `test command` | pass | yes | - |
| D-01 | ... | code trace + integration test | evidence | yes | - |
```

Hard-fail planning when a requirement has no credible oracle. If only manual or external proof is possible, say so before approval.

## SUMMARY.md

The worker writes facts, not approval. For multiple slices, append a section keyed by slice and attempt instead of overwriting earlier evidence:

```markdown
# Phase 01 Summary

## Changed
- behavior and files

## Evidence
- RED/baseline: command and observed output
- GREEN: command and observed output
- Broader checks: command and exit status

## Deviations
- None, or decision ID and rationale

## Concerns
- None, or concrete unresolved risk
```

## REVIEW.md

Record scope, spec, and quality separately:

```yaml
---
status: clean
mode: task
subject_contract_digest: sha256:...
subject_tree_fingerprint: sha256:...
spec_compliance: pass
code_quality: pass
blocking_findings: 0
---
```

Each finding includes severity, confidence, quoted evidence, impact, and required action.

## VERIFICATION.md

```yaml
---
status: passed
contract_digest: sha256:...
tree_fingerprint: sha256:...
requirements_passed: 4
requirements_total: 4
external_checks_pending: 0
---
```

Include the requirement matrix, commands, exit codes, impact-variant checks, and any assurance reduction. Only the verifier writes `status: passed`.
