"""Runs a test suite against the checkout package, or against a mutant of it,
in a throwaway directory and a separate Python process."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from . import ROOT, SUT, faults


@dataclass
class Run:
    tests: dict[str, dict] = field(default_factory=dict)  # nodeid -> {"outcome", "ac"}
    broken: dict[str, str] = field(default_factory=dict)  # files that failed to collect
    timed_out: bool = False

    def outcome(self, nodeid: str) -> str:
        return self.tests.get(nodeid, {}).get("outcome", "not run")


def run(files: dict[str, str], pricing_source: str | None = None, timeout: float = 60) -> Run:
    """files maps a file name (test_s1.py) to its source. pricing_source replaces
    sut/checkout/pricing.py; None runs the original."""
    with tempfile.TemporaryDirectory(prefix="aievals-") as tmp:
        tmp = Path(tmp)
        impl = tmp / "impl" / "checkout"
        shutil.copytree(SUT, impl, ignore=shutil.ignore_patterns("__pycache__"))
        if pricing_source is not None and not faults.active("mutant-not-applied"):
            (impl / "pricing.py").write_text(pricing_source)
        tests = tmp / "tests"
        tests.mkdir()
        for name, source in files.items():
            (tests / name).write_text(source)
        (tmp / "pytest.ini").write_text("[pytest]\n")
        out = tmp / "out.json"
        env = {
            **os.environ,
            "PYTHONPATH": os.pathsep.join([str(tmp / "impl"), str(ROOT / "src")]),
            "AIEVALS_OUT": str(out),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
        }
        cmd = [
            sys.executable, "-m", "pytest", "tests", "-q", "-p", "aievals.pytest_plugin",
            "-p", "no:cacheprovider", "--continue-on-collection-errors", "-c", "pytest.ini",
            "--rootdir", str(tmp), "-o", "console_output_style=classic",
        ]
        try:
            subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return Run(timed_out=True)
        if not out.exists():
            return Run(timed_out=True)
        data = json.loads(out.read_text())
        return Run(tests=data["tests"], broken=data["broken"])


def run_many(files: dict[str, str], sources: list[str], timeout: float = 60) -> list[Run]:
    workers = max(1, min(len(sources), os.cpu_count() or 2))
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(lambda s: run(files, s, timeout), sources))
