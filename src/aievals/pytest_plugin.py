"""Loaded into the pytest run of a suite under evaluation (-p aievals.pytest_plugin).

Records, for every test, its outcome and the acceptance criteria it is tagged
with (@pytest.mark.ac("S2-AC1")), and which files failed to collect. Writes
them as JSON to the path in AIEVALS_OUT."""

from __future__ import annotations

import json
import os
import re

_tests: dict[str, dict] = {}
_broken: dict[str, str] = {}


def pytest_configure(config):
    config.addinivalue_line("markers", "ac(*ids): the acceptance criteria a test checks")


def pytest_collectreport(report):
    if report.failed:
        _broken[report.nodeid] = str(report.longrepr)[-2000:]


def pytest_collection_modifyitems(items):
    for item in items:
        ac = []
        for mark in item.iter_markers("ac"):
            ac.extend(str(a) for a in mark.args)
        _tests[item.nodeid] = {"outcome": "not run", "ac": sorted(set(ac))}


def pytest_runtest_logreport(report):
    entry = _tests.setdefault(report.nodeid, {"outcome": "not run", "ac": []})
    if report.when == "setup" and report.failed:
        entry["outcome"] = "error"
    elif report.when == "setup" and report.skipped:
        entry["outcome"] = "skipped"
    elif report.when == "call":
        entry["outcome"] = "passed" if report.passed else "skipped" if report.skipped else "failed"
        if report.failed:
            errors = [l[1:].strip() for l in report.longreprtext.splitlines() if l.startswith("E ")]
            # Memory addresses change from run to run; results.json must not.
            entry["message"] = re.sub(r"0x[0-9a-f]+", "0x…", " ".join(errors[:2]))[:300]
    elif report.when == "teardown" and report.failed and entry["outcome"] == "passed":
        entry["outcome"] = "error"


def pytest_sessionfinish(session):
    path = os.environ.get("AIEVALS_OUT")
    if path:
        with open(path, "w") as f:
            json.dump({"tests": _tests, "broken": _broken}, f)
