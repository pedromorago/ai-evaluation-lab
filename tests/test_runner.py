"""The runner against the real checkout package and real mutants."""

from aievals import REFERENCE, runner
from aievals.mutate import mutants


def test_reference_suite_passes_on_the_original():
    files = {"test_s5.py": (REFERENCE / "test_s5.py").read_text()}
    r = runner.run(files)
    assert r.tests and all(t["outcome"] == "passed" for t in r.tests.values())
    assert r.tests["tests/test_s5.py::test_express_costs_the_same_and_is_never_free"]["ac"] == ["S5-AC2"]


def test_a_mutant_is_really_applied():
    files = {"test_s5.py": (REFERENCE / "test_s5.py").read_text()}
    express = next(m for m in mutants() if m.ac == "S5-AC2" and "`==` → `!=`" in m.change)
    r = runner.run(files, express.source)
    assert r.outcome("tests/test_s5.py::test_express_costs_the_same_and_is_never_free") == "failed"


def test_a_broken_file_does_not_stop_the_others():
    files = {"test_ok.py": "def test_ok():\n    assert True\n", "test_bad.py": "import nothing_here\n"}
    r = runner.run(files)
    assert r.outcome("tests/test_ok.py::test_ok") == "passed"
    assert any("test_bad.py" in k for k in r.broken)


def test_the_suite_cannot_import_the_repository_copy_of_the_code():
    files = {"test_where.py": "import checkout\ndef test_where():\n    assert 'aievals-' in checkout.__file__\n"}
    assert runner.run(files).outcome("tests/test_where.py::test_where") == "passed"
