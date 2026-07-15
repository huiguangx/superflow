---
name: superflow
description: "Run an evidence-gated software delivery workflow when the user explicitly asks for Superflow, audited delivery, contract-first implementation, independent plan/review/verification, or a high-risk multi-step change. Inspect the codebase, write an auditable contract, obtain one user approval, then implement vertical slices with review, bounded repair loops, persistent state, and fresh verification. Do not auto-trigger for routine small fixes."
---

# Superflow

Own the workflow from request through `VERIFIED_COMPLETE`. The user approves one audited plan; after approval, continue without routine prompts until verified, safely blocked, or locally complete.

## Laws

1. Do not edit production code before an audited plan is explicitly approved.
2. Do not fix a bug before reproducing it or gathering root-cause evidence.
3. Do not let a planner or worker approve its own output.
4. Do not claim success without fresh verification evidence.
5. Do not silently reduce scope, weaken tests, or bypass a failed gate.
6. Do not migrate data, rotate secrets, call external services, or perform destructive cleanup without explicit authority recorded in the approved contract.

## Load The Harness

Read [artifacts.md](references/artifacts.md) before creating or resuming state. Read [risk-routing.md](references/risk-routing.md) before planning verification or selecting specialist checks.

Use these internal skills as role contracts:

- Planner: `../superflow-plan/SKILL.md`
- Worker or fixer: `../superflow-worker/SKILL.md`
- Plan, task, or branch reviewer: `../superflow-review/SKILL.md`
- Phase or milestone verifier: `../superflow-verify/SKILL.md`

Dispatch a fresh isolated agent for every planner, worker, reviewer, and verifier assignment when the runtime supports it, and instruct it to load the matching skill. If isolation is unavailable, continue with an inline fallback only after recording `assurance: reduced-no-isolation` in `STATE.md`; inline review may report implementation and local verification evidence, but it cannot produce final `VERIFIED_COMPLETE`.

## Enforced Gates

Run `python3 <this-skill>/scripts/superflow_gate.py --root <repo> --gate <name>` before every status promotion. A nonzero exit is a blocker: record it in `STATE.md`; do not manually waive or copy a stale digest.

- Before plan review: `--gate plan`.
- Before a worker: `--gate execute`.
- Before task or branch review: increment `review_attempt`, then `--gate review-dispatch`.
- Before accepting a clean review: `--gate review-clear --report <REVIEW.md>`.
- Before phase or milestone verification: increment `verification_attempt`, then `--gate verify-dispatch --review <REVIEW.md>`.
- Before accepting verification: `--gate verify-passed --report <VERIFICATION.md>`.
- Before setting `verified_complete`: `--gate complete --review <FINAL-REVIEW.md> --report <FINAL-VERIFICATION.md>`.

For a non-Git repository, pass every reviewed product path as `--product-file <path>`. The gate tool is the sole implementation of artifact digests and product-tree fingerprints; role skills consume its output instead of reimplementing the rules.

Before writing a review or verification report, obtain its two bindings with `--bindings`; after milestone verification, copy those same values to `STATE.md`'s `verified_contract_digest` and `verified_tree_fingerprint` before the final gate.

## Start Or Resume

1. Find the repository root and read project instructions, package/build files, relevant docs, recent commits, current diff, and existing tests.
2. Preserve unrelated user changes. Never clean, reset, or overwrite a dirty worktree.
3. Read `.planning/STATE.md` when present. Resume from its `next_action` only after its request, approved-contract, and product-tree bindings still match the artifacts and repository. Invalidate stale approval or verification instead of trusting status text.
4. If no state exists, create the minimal artifacts from `artifacts.md` and set `status: planning`.
5. Treat a pure prose typo as a fast path: inspect, change, and verify without the full phase loop. Any code or behavior change uses the full contract gate.

## Stage A: Plan With The User

This is the only routine interactive stage.

1. Dispatch or follow `superflow-plan` to map the codebase, domain language, affected call paths, runtime variants, ownership boundaries, existing patterns, tests, and rollback options.
2. Classify open decisions as mechanical, taste, or one-way. Resolve mechanical decisions automatically. Ask the user only about unresolved taste, product, security, migration, or one-way decisions.
3. Produce 2-3 viable approaches when architecture is not obvious. Recommend one with concrete tradeoffs.
4. Preserve the source request and repository baseline in `PROJECT.md`, then write `REQUIREMENTS.md`, `ROADMAP.md`, phase `CONTEXT.md`, `PLAN.md`, and `VALIDATION.md`. Plans describe behavior, interfaces, files, and commands; they do not contain speculative full implementations.
5. Run the `plan` gate, then dispatch `superflow-review` in `plan` mode with `PROJECT.md`, the plan artifacts, and repository evidence. It must independently check source-request, requirement, decision, impact-surface, validation, rollback, and scope coverage.
6. Send findings back to the planner. Repeat at most 3 times. A remaining Critical or Important finding blocks approval.
7. Present the final audited contract to the user in one review. Record permissions for dependencies, migrations, external services, and destructive actions.
8. Wait for explicit approval. On approval, bind the request digest, approved-contract digest, and repository baseline in `STATE.md`; set `status: approved`, `autonomy: active`, and `next_action: execute-phase`. Freeze requirements and decisions; implementation details may evolve only within that envelope.

## Stage B: Execute Autonomously

Do not ask "should I continue?" after approval.

For each incomplete phase in dependency order:

1. Mark the phase active. For each incomplete slice in dependency order, update the slice ledger and run steps 2-5 before selecting another slice.
2. Run the `execute` gate, then dispatch a fresh `superflow-worker` with one task brief, global constraints, relevant decisions, expected write surface, approved-contract digest, baseline revision, validation contract, and report path. Do not paste conversation history.
3. After the worker returns, inspect the actual diff and report. A success message is not evidence.
4. Increment `review_attempt`, pass the `review-dispatch` gate, then dispatch a fresh `superflow-review` in `task` mode with the task brief, worker report, actual diff, and product-tree fingerprint. It returns separate spec-compliance and code-quality verdicts. Accept a clean report only through `review-clear`.
5. For Critical or Important findings, dispatch a fresh fixer with the complete finding set, then a fresh reviewer. Limit each slice's review/fix loop to 3 attempts. Mark the slice reviewed only when blocking findings are clear.
6. Only after every planned slice is reviewed, increment `verification_attempt`, pass `verify-dispatch`, then dispatch a fresh `superflow-verify` with the full phase contract and current tree. Accept a passed report only through `verify-passed`.
7. If verification returns `failed` for an in-contract gap, dispatch a fresh planner to add one closure slice, independently review that gap plan, then run it through worker, task review, and phase verification once.
8. If the phase passes, bind and persist its evidence and advance. If it remains failed or unproven, set `status: blocked` with exact evidence and stop. Never mark a failed phase complete.

Run tasks sequentially by default. Parallelize only read-only discovery or tasks with proven disjoint write sets and no dependency edge.

## Stage C: Finish

After all phases pass:

1. Dispatch a fresh `superflow-review` in `branch` mode against the merge base and approved contract.
2. Fix and re-review blocking findings within the same 3-attempt bound.
3. Dispatch a fresh `superflow-verify` in `milestone` mode. Recheck every requirement, decision, impact variant, public interface, integration edge, and project-standard command.
4. If milestone verification returns `failed` for an in-contract integration gap, run one bounded final closure cycle: gap plan review, worker/fixer, task review, branch review, then fresh milestone verification. On another failure or any `blocked` result, persist the evidence and stop.
5. Set `status: verified_complete` only after `complete` passes, every blocking matrix row passes, and `STATE.md` binds the verified contract digest and final product-tree fingerprint.

## Decision Policy After Approval

- Reversible, in-scope, consistent with repository precedent: decide and continue.
- Missing implementation detail with a clear existing pattern: follow the pattern and record the decision.
- New scope, public contract change, irreversible data effect, security-policy conflict, or unavailable external proof: fail closed and record a blocker.
- Three failed hypotheses during debugging: stop; this signals a possible architectural problem.

## Completion Output

Report only evidence-backed status:

- changed behavior and files
- requirements proven and commands run
- review findings fixed or remaining
- assurance reductions and external checks not performed
- final state: `verified_complete` or `blocked`
