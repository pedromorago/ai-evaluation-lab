"""Seeded bugs in the evaluator itself.

An evaluator that is wrong gives a model a score it didn't earn, and nobody
notices: the numbers still look like numbers. Each fault below is a mistake
that is easy to make when writing a harness like this one. Setting
AIEVALS_FAULT=<name> switches one on, and scripts/run_seeded_bugs.py checks
that the lab's own tests catch every one of them."""

from __future__ import annotations

import os

FAULTS = {
    "invalid-tests-kill": "kills are counted for tests that already fail on the reference implementation",
    "trust-ac-tags": "a criterion counts as covered because a test is tagged with it, without checking the test detects a bug there",
    "score-over-all-mutants": "the mutation score divides by every mutant, including the ones no test can kill",
    "no-assert-ignores-raises": "a test whose only check is pytest.raises is reported as having no assertion",
    "flaky-counted-valid": "a test that passes once and fails once on the same code counts as valid",
    "mutant-not-applied": "the runner copies the original module instead of the mutant",
    "gate-ignores-regression": "the gate compares the candidate against itself instead of against the baseline",
    "duplicates-by-name": "redundant tests are found by name instead of by what they detect",
    "ac-map-off-by-one": "mutants are mapped to the criterion on the line after them",
    "unsafe-code-runs": "the static check lets a test file that writes to disk or starts processes run",
}


def active(name: str) -> bool:
    if name not in FAULTS:
        raise KeyError(name)
    return os.environ.get("AIEVALS_FAULT") == name
