"""The scoring logic, driven by scripted runner results so each rule is checked in isolation."""

import pytest

from aievals import evaluate, runner
from aievals.mutate import Mutant

MUTANTS = [Mutant(f"M{k}", "op", k, ac, "change", f"source {k}") for k, ac in [(1, "S2-AC1"), (2, "S2-AC1"), (3, "S5-AC1"), (4, None)]]
FILES = {"test_s2.py": "def test_a():\n    assert True\n"}


def scripted(base1, base2, per_mutant, monkeypatch):
    """base1/base2: {test: (outcome, [ac])}; per_mutant: {mutant id: {test: outcome}}."""
    def as_run(spec):
        return runner.Run(tests={t: {"outcome": o, "ac": ac} for t, (o, ac) in spec.items()})

    calls = iter([as_run(base1), as_run(base2)])
    monkeypatch.setattr(runner, "run", lambda files, source=None, timeout=60: next(calls))

    def run_many(files, sources, timeout=60):
        out = []
        for m in MUTANTS:
            spec = {t: (per_mutant.get(m.id, {}).get(t, "passed"), ac) for t, (_, ac) in base1.items()}
            out.append(as_run(spec))
        return out

    monkeypatch.setattr(runner, "run_many", run_many)


def score(monkeypatch, base1, per_mutant, base2=None, killable=None):
    scripted(base1, base2 or base1, per_mutant, monkeypatch)
    return evaluate.evaluate(FILES, MUTANTS, killable)


def test_a_test_failing_on_the_reference_is_invalid_and_kills_nothing(monkeypatch):
    r = score(monkeypatch, {"t::bad": ("failed", ["S2-AC1"]), "t::good": ("passed", ["S2-AC1"])},
              {"M1": {"t::bad": "failed"}, "M2": {"t::bad": "failed", "t::good": "failed"}})
    assert r["tests"]["t::bad"]["status"] == "invalid"
    assert r["tests"]["t::bad"]["kills"] == []
    assert r["summary"]["killed"] == 1  # M2, by the valid test only


def test_a_test_that_passes_once_and_fails_once_is_flaky(monkeypatch):
    r = score(monkeypatch, {"t::a": ("passed", [])}, {}, base2={"t::a": ("failed", [])})
    assert r["tests"]["t::a"]["status"] == "flaky"
    assert r["summary"]["valid"] == 0


def test_mutation_score_counts_only_killable_mutants(monkeypatch):
    r = score(monkeypatch, {"t::a": ("passed", ["S2-AC1"])}, {"M1": {"t::a": "failed"}}, killable={"M1", "M3"})
    assert (r["summary"]["killed"], r["summary"]["mutants"], r["summary"]["mutation_score"]) == (1, 2, 0.5)


def test_a_tag_is_verified_only_by_a_kill_in_that_criterion(monkeypatch):
    r = score(monkeypatch, {"t::tagged": ("passed", ["S2-AC1", "S5-AC1"])}, {"M1": {"t::tagged": "failed"}})
    assert r["coverage"]["S2-AC1"] == {"claimed": 1, "verified": True, "mutants": 2, "killed": 1}
    assert r["coverage"]["S5-AC1"]["claimed"] == 1
    assert r["coverage"]["S5-AC1"]["verified"] is False


def test_redundant_tests_are_found_by_what_they_kill(monkeypatch):
    r = score(monkeypatch,
              {"t::one": ("passed", []), "t::two": ("passed", []), "t::three": ("passed", [])},
              {"M1": {"t::one": "failed", "t::two": "failed"}, "M3": {"t::three": "failed"}})
    assert r["redundant"] == ["t::two"]


def test_tests_that_catch_nothing_are_inert(monkeypatch):
    r = score(monkeypatch, {"t::a": ("passed", []), "t::b": ("passed", [])}, {"M1": {"t::a": "failed"}})
    assert r["inert"] == ["t::b"]


def test_a_mutant_that_breaks_collection_counts_as_killed(monkeypatch):
    r = score(monkeypatch, {"t::a": ("passed", [])}, {"M4": {"t::a": "not run"}})
    assert r["tests"]["t::a"]["kills"] == ["M4"]
