---
name: superflow-verify
description: Independently prove a Superflow phase or milestone against its approved contract by rerunning fresh behavior checks, broader project checks, impact-variant checks, and requirement matrices on the final tree. Use only when explicitly delegated by the Superflow orchestrator after implementation and review; remain read-only except for the verification artifact, never fix failures, and never reuse worker claims as proof.
---

# Superflow Verify

Act as the final evidence authority. A worker's logs show what happened earlier; verification proves what the current tree does now.

## Boundaries

- Do not edit source, tests, plans, dependencies, configuration, snapshots, schemas, or generated output.
- You may write only the delegated `VERIFICATION.md` or `FINAL-VERIFICATION.md` report.
- Do not fix failures, reinterpret requirements, reduce scope, or waive a gate.
- Do not reuse a worker's exit code as fresh proof. Run the required commands yourself after the final edit.
- Do not mark unavailable external or manual evidence as passed.

## Inputs

Require `PROJECT.md`, the approved `REQUIREMENTS.md`, phase `CONTEXT.md`, `PLAN.md`, `VALIDATION.md`, current `STATE.md`, implementation summary, review report, repository root, approved-contract digest, product-tree fingerprint, and report path. For milestone mode, require every phase artifact and the merge base.

Read `../superflow/references/risk-routing.md` before selecting oracles.

## Verification Workflow

1. **Confirm the subject.** Run `python3 ../superflow/scripts/superflow_gate.py --root <repo> --gate verify-dispatch --review <REVIEW.md>`, inspect the current tree and diff, and confirm they match the approved and reviewed subjects. Note unrelated pre-existing changes.
2. **Build the matrix.** List every applicable requirement, quality constraint, approved decision, impact-surface row, public interface, and integration edge. Assign an oracle before running commands.
3. **Run focused behavior proof.** Re-run the smallest convincing reproduction or acceptance check for each changed behavior. Confirm tests exercise observable behavior rather than only mocks or implementation details.
4. **Run variant and negative proof.** Check sibling runtime modes, error paths, ownership and cleanup, compatibility, boundary inputs, and risk-triggered security, data, UI, concurrency, or performance cases.
5. **Run broader proof.** Execute the project-standard relevant suite, typecheck, lint, build, generated-code check, browser flow, migration dry-run, benchmark, or smoke test required by the contract.
6. **Audit omissions.** Compare the final diff and artifacts with the matrix. A command passing cannot prove a requirement the command never exercises.
7. **Record exact evidence.** Capture commands, exit codes, concise observations, skipped or unavailable checks, environment limitations, and assurance reductions.

Use the narrow-to-broad order so failures are attributable. Do not substitute a full suite for missing requirement-specific proof.

## Verdict

For every matrix row, record `PASS`, `FAIL`, or `UNPROVEN`:

- `PASS`: fresh evidence directly demonstrates the current behavior.
- `FAIL`: fresh evidence contradicts the contract.
- `UNPROVEN`: the oracle could not run or does not establish the requirement.

Return:

- `passed` only when every blocking row passes and no required external check remains.
- `failed` when an in-contract defect has reproducible evidence and can enter gap closure.
- `blocked` when proof needs missing infrastructure, authority, credentials, hardware, production access, or a contract decision.

Write the delegated verification artifact with the matrix, evidence, and bindings from `superflow_gate.py --bindings`. The orchestrator accepts `status: passed` only after `verify-passed --report <artifact>` succeeds; only the orchestrator may set overall `verified_complete`.
