# Superflow

Superflow is a set of Codex skills for higher-assurance coding work. It turns a
feature or bug request into a local workflow with planning, implementation,
review, verification, and evidence checks.

Use it when a task is large enough that "just edit the file" is too loose:
multi-step features, risky refactors, bugs that need proof, or work where you
want the agent to show what was reviewed and verified before calling it done.

Do not use the full flow for tiny UI tweaks, one-line bugs, or routine cleanup.

## Install

Install globally for your user:

```bash
npx github:huiguangx/superflow
```

After the npm package is published, this also works:

```bash
npx superflow-skills
```

This copies the Superflow skills into:

```text
~/.agents/skills
```

Start a new Codex session after installing.

To install into only one repo, run this from that repo:

```bash
npx github:huiguangx/superflow .agents/skills
```

## Start

Open Codex in the project you want to work on and ask:

```text
Use Superflow to plan and implement this feature end to end.
```

For a bug:

```text
Use Superflow to diagnose, fix, review, and verify this bug.
```

You can write the actual task in English or Chinese after that prompt.

## What It Does

Superflow coordinates five skills:

- `superflow`: main workflow controller
- `superflow-plan`: requirement and plan shaping
- `superflow-worker`: implementation
- `superflow-review`: independent review
- `superflow-verify`: validation and evidence check

The included gate script checks that review and verification evidence still
matches the current contract and product tree before the work is marked
`verified_complete`.

## Try It

Use a medium-sized test task, for example:

```text
Use Superflow to build a small todo app with add, complete, delete, filter, and tests.
```

Avoid testing it first on a one-line change. Superflow is meant to validate a
workflow, not make trivial edits faster.

## Local Gate Check

The gate checker has a self-test:

```bash
python3 skills/superflow/scripts/superflow_gate.py --self-test
```

It uses only the Python standard library.
