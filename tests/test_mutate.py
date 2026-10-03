"""The mutation engine: stable, every mutant is real Python, and mutants know their criterion."""

import ast

from aievals import SUT
from aievals.mutate import ac_by_line, mutants


def test_mutants_are_stable_and_numbered():
    first, second = mutants(), mutants()
    assert [m.id for m in first] == [m.id for m in second] == [f"M{k:03d}" for k in range(1, len(first) + 1)]
    assert [m.source for m in first] == [m.source for m in second]


def test_every_mutant_parses_and_changes_the_code():
    original = ast.dump(ast.parse((SUT / "pricing.py").read_text()))
    for m in mutants():
        assert ast.dump(ast.parse(m.source)) != original, m.id


def test_no_two_mutants_are_the_same_program():
    sources = [m.source for m in mutants()]
    assert len(set(sources)) == len(sources)


def test_mutants_carry_the_criterion_of_their_line():
    tags = ac_by_line((SUT / "pricing.py").read_text())
    for m in mutants():
        assert m.ac == tags.get(m.line), m.id


def test_criterion_of_known_rules():
    lines = (SUT / "pricing.py").read_text().splitlines()
    by_text = {}
    for m in mutants():
        by_text.setdefault(lines[m.line - 1].split("#")[0].strip(), []).append(m.ac)
    assert by_text['if shipping == "express":'] == ["S5-AC2"]
    assert set(by_text['return Decimal("0")']) == {"S2-AC1", "S2-AC3"}  # the books rule and the rate below 10 units
    assert set(by_text["return Quote(_cents(subtotal), _cents(discount), _cents(ship), tax, _cents(total), tuple(applied))"]) == {None}


def test_every_criterion_has_mutants():
    from aievals.stories import all_criteria

    covered = {m.ac for m in mutants()}
    assert set(all_criteria()) <= covered
