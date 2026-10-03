"""Scores a test suite.

The questions, in order:
1. Is it safe to run, and does it parse?
2. Is each test valid: does it pass on the reference implementation, twice?
   A test that fails there asserts a requirement the stories don't have.
3. Which bugs does it catch: which mutants make at least one valid test fail?
4. Does each acceptance criterion have a test that really checks it: a test
   tagged with the criterion that catches a bug in the code implementing it?
5. What is dead weight: tests that catch nothing, or exactly what another test
   already catches.

The mutation score only counts mutants the hand-written reference suite kills.
The others are listed in the reference report: they are equivalent to the
original (no test can tell them apart) or a gap in the reference suite."""

from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

from . import REFERENCE, ROOT, SUT, faults, runner, static, stories
from .mutate import Mutant, mutants as make_mutants

KILLING = {"failed", "error", "not run"}


def _story_of(nodeid: str) -> str:
    name = nodeid.split("::")[0].rsplit("/", 1)[-1]  # tests/test_s2.py -> test_s2.py
    stem = name.removeprefix("test_").removesuffix(".py")
    return stem.upper() if stem[:1] in "sS" else stem


def evaluate(files: dict[str, str], ms: list[Mutant], killable: set[str] | None = None) -> dict:
    criteria = stories.all_criteria()
    checks = {name: static.check(name, src) for name, src in files.items()}
    runnable = {name: src for name, src in files.items() if checks[name].runnable}

    first = runner.run(runnable)
    second = runner.run(runnable)
    tests = sorted(first.tests)

    status: dict[str, str] = {}
    for t in tests:
        a, b = first.outcome(t), second.outcome(t)
        if a == b == "passed":
            status[t] = "valid"
        elif "passed" in (a, b):
            status[t] = "valid" if faults.active("flaky-counted-valid") else "flaky"
        elif a == "skipped":
            status[t] = "skipped"
        else:
            status[t] = "invalid"
    counted = [t for t in tests if status[t] == "valid" or (faults.active("invalid-tests-kill") and status[t] == "invalid")]
    valid = [t for t in tests if status[t] == "valid"]

    results = runner.run_many(runnable, [m.source for m in ms]) if counted else [runner.Run() for _ in ms]
    kills: dict[str, set[str]] = {t: set() for t in counted}
    timeouts = set()
    for m, r in zip(ms, results):
        if r.timed_out:
            timeouts.add(m.id)
            continue
        for t in counted:
            if r.outcome(t) in KILLING:
                kills[t].add(m.id)

    killed = set().union(*kills.values()) | timeouts if kills else set(timeouts)
    pool = {m.id for m in ms} if killable is None or faults.active("score-over-all-mutants") else set(killable)
    by_ac: dict[str, set[str]] = defaultdict(set)
    for m in ms:
        if m.id in pool and m.ac:
            by_ac[m.ac].add(m.id)

    tags = {t: first.tests[t].get("ac", []) for t in tests}
    coverage = {}
    for ac in criteria:
        claimed = [t for t in valid if ac in tags[t]]
        verified = [t for t in claimed if kills.get(t, set()) & by_ac[ac]]
        coverage[ac] = {
            "claimed": len(claimed),
            "verified": bool(claimed) if faults.active("trust-ac-tags") else bool(verified),
            "mutants": len(by_ac[ac]),
            "killed": len(by_ac[ac] & killed),
        }

    inert = [t for t in valid if not kills.get(t)]
    if faults.active("duplicates-by-name"):
        groups: dict = defaultdict(list)
        for t in valid:
            groups[t.split("::")[-1]].append(t)
    else:
        groups = defaultdict(list)
        for t in valid:
            if kills.get(t):
                groups[frozenset(kills[t])].append(t)
    redundant = sorted(t for g in groups.values() for t in g[1:])
    # Tagged tests that catch no bug in the code of the criteria they name. Not
    # necessarily wrong (a test can check the boundary just below a rule), but
    # worth reading: a tag is a claim about what the test checks.
    unconfirmed = [
        t for t in valid
        if tags[t] and kills.get(t) and not any(kills[t] & by_ac[ac] for ac in tags[t])
    ]
    unknown_tags = sorted({a for t in tests for a in tags[t] if a not in criteria})
    no_assertion = sorted(f"tests/{c.name}::{fn}" for c in checks.values() for fn in c.no_assertion)

    per_story = {}
    for s in stories.load():
        s_tests = [t for t in tests if _story_of(t) == s.id]
        s_valid = [t for t in s_tests if status[t] == "valid"]
        s_pool = set().union(*(by_ac[ac] for ac in s.criteria)) if s.criteria else set()
        s_killed = set().union(*(kills.get(t, set()) for t in s_valid)) if s_valid else set()
        per_story[s.id] = {
            "tests": len(s_tests),
            "valid": len(s_valid),
            "mutation_score": round(len(s_killed & s_pool) / len(s_pool), 4) if s_pool else None,
            "criteria_verified": sum(coverage[ac]["verified"] for ac in s.criteria),
            "criteria": len(s.criteria),
        }

    summary = {
        "tests": len(tests),
        "valid": len(valid),
        "invalid": sum(1 for t in tests if status[t] == "invalid"),
        "flaky": sum(1 for t in tests if status[t] == "flaky"),
        "skipped": sum(1 for t in tests if status[t] == "skipped"),
        "validity": round(len(valid) / len(tests), 4) if tests else 0.0,
        "mutants": len(pool),
        "killed": len(killed & pool),
        "mutation_score": round(len(killed & pool) / len(pool), 4) if pool else 0.0,
        "criteria": len(criteria),
        "criteria_claimed": sum(1 for c in coverage.values() if c["claimed"]),
        "criteria_verified": sum(1 for c in coverage.values() if c["verified"]),
        "inert": len(inert),
        "redundant": len(redundant),
        "tag_unconfirmed": len(unconfirmed),
        "no_assertion": len(no_assertion),
        "broken_files": len(first.broken) + sum(1 for c in checks.values() if c.syntax_error),
        "unsafe_files": sum(1 for c in checks.values() if c.unsafe),
    }
    return {
        "summary": summary,
        "per_story": per_story,
        "coverage": coverage,
        "tests": {
            t: {
                "status": status[t],
                "ac": tags[t],
                "kills": sorted(kills.get(t, set())),
                "message": first.tests[t].get("message", "") if status[t] != "valid" else "",
            }
            for t in tests
        },
        "inert": inert,
        "redundant": redundant,
        "tag_unconfirmed": unconfirmed,
        "no_assertion": no_assertion,
        "unknown_tags": unknown_tags,
        "survivors": sorted(pool - killed),
        "files": {
            name: {"syntax_error": c.syntax_error, "unsafe": c.unsafe, "runnable": c.runnable}
            for name, c in checks.items()
        },
        "broken": first.broken,
    }


def read_suite(directory: Path) -> dict[str, str]:
    return {p.name: p.read_text() for p in sorted(directory.glob("test_*.py"))}


def _fingerprint(files: dict[str, str]) -> str:
    h = hashlib.sha256()
    for path in sorted(SUT.glob("*.py")):
        h.update(path.read_bytes())
    for name, src in sorted(files.items()):
        h.update(name.encode() + src.encode())
    return h.hexdigest()[:16]


def reference(use_cache: bool = True) -> dict:
    """The hand-written suite's result over every mutant. Its kills define which mutants count.
    Cached by the code and the suite, but never while a seeded evaluator bug is switched on."""
    files = read_suite(REFERENCE)
    use_cache = use_cache and not os.environ.get("AIEVALS_FAULT")
    cache = ROOT / ".cache" / f"reference-{_fingerprint(files)}.json"
    if use_cache and cache.exists():
        return json.loads(cache.read_text())
    result = evaluate(files, make_mutants())
    if use_cache:
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps(result))
    return result


def killable() -> set[str]:
    """Every mutant the reference suite kills."""
    return {m.id for m in make_mutants()} - set(reference()["survivors"])
