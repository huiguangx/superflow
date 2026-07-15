#!/usr/bin/env python3
"""Deterministic gates for Superflow planning artifacts. Uses Python's stdlib only."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EXCLUDED_PARTS = {".git", ".planning", "node_modules", "vendor", "dist", "build", "coverage"}
CONTRACT_FILES = ("PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md")
STATE_FIELDS = {"status", "assurance", "request_digest", "approved_contract_digest", "baseline_revision", "review_attempt", "verification_attempt", "verified_contract_digest", "verified_tree_fingerprint"}


class GateError(Exception):
    pass


def fail(message: str) -> None:
    raise GateError(message)


def read(path: Path) -> bytes:
    if not path.is_file():
        fail(f"missing required artifact: {path}")
    return path.read_bytes()


def frontmatter(path: Path) -> dict[str, str]:
    text = read(path).decode("utf-8", "replace")
    if not text.startswith("---\n"):
        fail(f"frontmatter missing: {path}")
    end = text.find("\n---\n", 4)
    if end < 0:
        fail(f"frontmatter not terminated: {path}")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip('"\'')
    return fields


def planning(root: Path) -> Path:
    path = root / ".planning"
    if not path.is_dir():
        fail(f".planning directory not found under {root}")
    return path


def phase_files(base: Path, pattern: str) -> list[Path]:
    return sorted((base / "phases").glob(f"*/{pattern}"))


def digest(paths: list[Path], root: Path) -> str:
    stream = bytearray()
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        stream.extend(f"--- {path.relative_to(root).as_posix()}\n".encode())
        stream.extend(read(path))
    return "sha256:" + hashlib.sha256(stream).hexdigest()


def contract_paths(root: Path) -> list[Path]:
    base = planning(root)
    contexts = phase_files(base, "*-CONTEXT.md")
    if not contexts:
        fail("no phase CONTEXT.md artifacts found")
    paths = [base / name for name in CONTRACT_FILES] + contexts
    for path in paths:
        read(path)
    return paths


def run_git(root: Path, *args: str) -> str | None:
    result = subprocess.run(["git", *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return result.stdout if result.returncode == 0 else None


def product_fingerprint(root: Path, explicit_files: list[str]) -> str:
    head = run_git(root, "rev-parse", "HEAD")
    names: set[str] = set(explicit_files)
    if head is not None:
        for args in (("diff", "--name-only", "HEAD"), ("diff", "--cached", "--name-only"), ("ls-files", "--others", "--exclude-standard")):
            names.update(line for line in (run_git(root, *args) or "").splitlines() if line)
    elif not names:
        fail("repository has no Git HEAD; pass --product-file for the reviewed product surface")
    paths: list[Path] = []
    for name in names:
        path = (root / name).resolve()
        try:
            relative = path.relative_to(root.resolve())
        except ValueError:
            fail(f"product file escapes repository: {name}")
        if any(part in EXCLUDED_PARTS for part in relative.parts) or not path.is_file():
            continue
        paths.append(path)
    stream = bytearray(f"HEAD:{head.strip() if head else 'none'}\n".encode())
    for path in sorted(set(paths), key=lambda item: item.relative_to(root).as_posix()):
        stream.extend(f"--- {path.relative_to(root).as_posix()}\n".encode())
        stream.extend(read(path))
    return "sha256:" + hashlib.sha256(stream).hexdigest()


def state(root: Path) -> dict[str, str]:
    values = frontmatter(planning(root) / "STATE.md")
    missing = STATE_FIELDS - values.keys()
    if missing:
        fail("STATE.md missing fields: " + ", ".join(sorted(missing)))
    if values["status"] not in {"planning", "awaiting_approval", "approved", "running", "blocked", "verified_complete"}:
        fail(f"invalid STATE.md status: {values['status']}")
    return values


def require_contract(root: Path, values: dict[str, str], approved: bool) -> str:
    actual = digest(contract_paths(root), root)
    if approved and values["approved_contract_digest"] != actual:
        fail(f"approved contract digest mismatch: state={values['approved_contract_digest'] or 'missing'}, actual={actual}")
    return actual


def validate_plan(root: Path) -> None:
    base = planning(root)
    ids = sorted(set(re.findall(r"\b(?:REQ|Q)-\d+\b", read(base / "REQUIREMENTS.md").decode("utf-8", "replace"))))
    if not ids:
        fail("REQUIREMENTS.md contains no REQ-* or Q-* IDs")
    plans = phase_files(base, "*-PLAN.md")
    validations = phase_files(base, "*-VALIDATION.md")
    if not plans or not validations:
        fail("every contract needs phase PLAN.md and VALIDATION.md artifacts")
    plan_text = "\n".join(read(path).decode("utf-8", "replace") for path in plans)
    validation_text = "\n".join(read(path).decode("utf-8", "replace") for path in validations)
    def covers(text: str, item: str) -> bool:
        return re.search(rf"(?<![A-Z0-9-]){re.escape(item)}(?![A-Z0-9-])", text) is not None

    missing_plan = [item for item in ids if not covers(plan_text, item)]
    missing_validation = [item for item in ids if not covers(validation_text, item)]
    if missing_plan:
        fail("requirements absent from plans: " + ", ".join(missing_plan))
    if missing_validation:
        fail("requirements absent from validation: " + ", ".join(missing_validation))


def report(root: Path, path_arg: str, expected_status: str, values: dict[str, str], files: list[str]) -> None:
    path = Path(path_arg)
    if not path.is_absolute():
        path = root / path
    fields = frontmatter(path)
    if fields.get("status") != expected_status:
        fail(f"{path} status must be {expected_status}, got {fields.get('status', 'missing')}")
    contract = fields.get("contract_digest") or fields.get("subject_contract_digest")
    tree = fields.get("tree_fingerprint") or fields.get("subject_tree_fingerprint")
    if contract != values["approved_contract_digest"]:
        fail(f"{path} is not bound to the approved contract")
    actual_tree = product_fingerprint(root, files)
    if tree != actual_tree:
        fail(f"{path} tree fingerprint is stale: report={tree or 'missing'}, actual={actual_tree}")


def gate(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    values = state(root)
    current_contract = require_contract(root, values, approved=False)
    if args.gate == "plan":
        validate_plan(root)
    elif args.gate == "execute":
        if values["status"] not in {"approved", "running"}:
            fail("execution requires STATE.md status approved or running")
        require_contract(root, values, approved=True)
    elif args.gate == "review-dispatch":
        if int(values["review_attempt"] or "0") >= 3:
            fail("review/fix attempt cap reached")
        require_contract(root, values, approved=True)
    elif args.gate == "review-clear":
        require_contract(root, values, approved=True)
        report(root, args.report, "clean", values, args.product_file)
    elif args.gate == "verify-dispatch":
        require_contract(root, values, approved=True)
        report(root, args.review, "clean", values, args.product_file)
        if int(values["verification_attempt"] or "0") >= 3:
            fail("verification/gap-closure attempt cap reached")
    elif args.gate == "verify-passed":
        require_contract(root, values, approved=True)
        report(root, args.report, "passed", values, args.product_file)
    elif args.gate == "complete":
        require_contract(root, values, approved=True)
        if values["assurance"] != "full":
            fail("verified_complete requires full assurance")
        report(root, args.review, "clean", values, args.product_file)
        report(root, args.report, "passed", values, args.product_file)
        actual_tree = product_fingerprint(root, args.product_file)
        if values["verified_contract_digest"] != values["approved_contract_digest"]:
            fail("STATE.md verified contract digest is missing or stale")
        if values["verified_tree_fingerprint"] != actual_tree:
            fail("STATE.md verified tree fingerprint is missing or stale")
    print(f"PASS {args.gate} contract={current_contract}")


def bindings(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    values = state(root)
    contract = require_contract(root, values, approved=values["status"] in {"approved", "running", "verified_complete"})
    print(json.dumps({"contract_digest": contract, "tree_fingerprint": product_fingerprint(root, args.product_file)}, sort_keys=True))


class GateTests(unittest.TestCase):
    def make_contract(self, root: Path) -> str:
        base = root / ".planning"
        phase = base / "phases" / "01-test"
        phase.mkdir(parents=True)
        (base / "PROJECT.md").write_text("# Project\n")
        (base / "REQUIREMENTS.md").write_text("# Requirements\n- REQ-01: Works\n- Q-01: Safe\n")
        (base / "ROADMAP.md").write_text("# Roadmap\n")
        (phase / "01-CONTEXT.md").write_text("# Context\n")
        (phase / "01-PLAN.md").write_text("REQ-01\nQ-01\n")
        (phase / "01-VALIDATION.md").write_text("REQ-01\nQ-01\n")
        return digest(contract_paths(root), root)

    def test_digest_is_path_ordered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "b").write_text("two")
            (root / "a").write_text("one")
            self.assertEqual(digest([root / "b", root / "a"], root), digest([root / "a", root / "b"], root))

    def test_frontmatter_requires_delimiters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.md"
            path.write_text("status: passed")
            with self.assertRaises(GateError):
                frontmatter(path)

    def test_plan_gate_rejects_unvalidated_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = self.make_contract(root)
            (root / ".planning" / "STATE.md").write_text(
                "---\nstatus: planning\nassurance: full\nrequest_digest: x\napproved_contract_digest: " + contract +
                "\nbaseline_revision: null\nreview_attempt: 0\nverification_attempt: 0\nverified_contract_digest: null\nverified_tree_fingerprint: null\n---\n")
            (root / ".planning" / "phases" / "01-test" / "01-VALIDATION.md").write_text("REQ-01\n")
            with self.assertRaises(GateError):
                gate(argparse.Namespace(root=str(root), gate="plan", report=None, review=None, product_file=[]))

    def test_clean_report_cannot_bind_a_stale_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = self.make_contract(root)
            (root / "product.txt").write_text("current")
            (root / ".planning" / "STATE.md").write_text(
                "---\nstatus: running\nassurance: full\nrequest_digest: x\napproved_contract_digest: " + contract +
                "\nbaseline_revision: null\nreview_attempt: 1\nverification_attempt: 0\nverified_contract_digest: null\nverified_tree_fingerprint: null\n---\n")
            (root / ".planning" / "review.md").write_text(
                "---\nstatus: clean\nsubject_contract_digest: " + contract +
                "\nsubject_tree_fingerprint: sha256:stale\n---\n")
            with self.assertRaises(GateError):
                gate(argparse.Namespace(root=str(root), gate="review-clear", report=".planning/review.md", review=None, product_file=["product.txt"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--gate", choices=("plan", "execute", "review-dispatch", "review-clear", "verify-dispatch", "verify-passed", "complete"))
    parser.add_argument("--report")
    parser.add_argument("--review")
    parser.add_argument("--product-file", action="append", default=[])
    parser.add_argument("--bindings", action="store_true", help="print current contract and tree bindings as JSON")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = unittest.main(argv=[sys.argv[0]], exit=False)
        return 0 if result.result.wasSuccessful() else 1
    if args.bindings:
        try:
            bindings(args)
        except (GateError, ValueError) as error:
            print(f"BLOCKED: {error}", file=sys.stderr)
            return 2
        return 0
    if not args.gate:
        parser.error("--gate is required unless --self-test is used")
    if args.gate in {"review-clear", "verify-passed"} and not args.report:
        parser.error(f"--report is required for {args.gate}")
    if args.gate in {"verify-dispatch", "complete"} and not args.review:
        parser.error(f"--review is required for {args.gate}")
    if args.gate == "complete" and not args.report:
        parser.error("--report is required for complete")
    try:
        gate(args)
    except (GateError, ValueError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
