"""Evaluating AI-generated test suites against a reference implementation."""

from pathlib import Path
import os

# The repository root: the stories, the system under test and the recorded runs live there.
ROOT = Path(os.environ.get("AIEVALS_ROOT", Path(__file__).resolve().parents[2]))
SUT = ROOT / "sut" / "checkout"
STORIES = ROOT / "stories"
RUNS = ROOT / "runs"
REFERENCE = ROOT / "reference"
