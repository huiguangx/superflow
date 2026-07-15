# Risk And Verification Routing

Use risk to select checks, not to create permanent personas. Run only relevant specialist passes.

## Work Size

- Small: one behavior, usually 1-2 files, no cross-system or irreversible effect. Use one phase and one worker/reviewer/verifier loop.
- Medium: several files or components with one coherent outcome. Use one phase with vertical slices.
- Large: cross-system, multiple independently releasable outcomes, or work likely to exceed one fresh context. Use multiple phases.

File counts are warning signals, not truth. Split when a worker cannot understand and verify the slice in one fresh context.

## Oracle Selection

| Change | Required first evidence | Required completion evidence |
|---|---|---|
| Bug | deterministic reproduction or diagnostic evidence | regression test plus original reproduction |
| Business logic / API / transformation | failing behavior test | focused test plus relevant suite |
| UI behavior | failing component/integration test when practical | browser interaction, console, responsive screenshots |
| Pure visual CSS | baseline screenshot | before/after screenshot at required viewports |
| Database/schema | current schema and migration baseline | dry-run/apply on disposable target, compatibility and rollback checks |
| Auth/payment/permissions | threat and trust-boundary model | negative-path tests and specialist security review |
| Concurrency/lifecycle | failing stress/reproduction or trace evidence | race/lifecycle tests and ownership audit |
| Performance claim | before benchmark | same benchmark after, with comparable conditions |
| Config/build | failing parser/build/startup baseline | parse, build, startup, and smoke check |
| Generated code | generator input or snapshot baseline | regenerate and prove clean diff |
| Documentation only | existing source of truth | link, example, or command validation |

Do not force unit-test TDD where the behavior is better proven by a compiler, migration tool, browser, benchmark, or integration harness. Always establish a feedback loop before changing production behavior.

## Specialist Triggers

- Security: auth, permissions, secrets, payments, untrusted input, shell/SQL, webhooks, cryptography, CI credentials.
- Data: schema, migration, destructive writes, retention, backfills, ownership changes.
- UI/QA: user-visible flows, responsive layout, accessibility, browser state, forms.
- Performance: explicit latency, memory, throughput, bundle-size, or cost claim.
- Integration: packaging, public API, versioning, distribution, and local runtime configuration.

Specialist findings obey the same evidence and confidence rules as normal review. A role name is not evidence.

## Decision Classes

- Mechanical: one answer follows from code, tests, or the approved contract. Decide automatically.
- Taste: several valid outcomes differ in product or design preference. Resolve before approval.
- One-way: destructive data, public API break, security posture, billing, production side effect, or hard-to-reverse architecture. Resolve before approval or block later.
- User challenge: evidence contradicts the requested direction. Surface before approval with cost and alternatives; never decide by agent vote.

After approval, follow repository precedent for reversible details. Never use majority voting between agents to replace product authority.

## Review Severity

- Critical: security/data-loss risk, wrong behavior, broken build, missing core requirement. Blocks immediately.
- Important: likely production defect, missing meaningful test, scope drift, compatibility or rollback gap. Fix before advancing.
- Minor: maintainability or polish with no current correctness impact. Record; do not churn automatically unless trivial and in-scope.

Confidence rules:

- 9-10: directly proven by quoted code, command output, or reproducible behavior.
- 7-8: strong code-path evidence; report normally.
- 5-6: plausible but unproven; verify before promoting.
- 1-4: suppress from blocking output.

## Parallelism

Parallelize read-only discovery freely. Parallelize writes only when plans declare disjoint file sets, independent interfaces, and no shared generated output, schema, lockfile, or build cache. Otherwise execute sequentially.

## Stop Conditions

Stop autonomously and write a blocker when:

- three plan or review revisions cannot satisfy the contract
- three debugging hypotheses fail
- one phase gap-closure cycle still fails
- required external evidence is unavailable
- the approved contract contradicts repository reality
- continuing would require unapproved destructive or production action
