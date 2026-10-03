from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ROOT, evaluate, mutate, runs


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="aievals", description="Evaluate AI-generated test suites.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("mutants", help="list the mutants of the system under test")
    sub.add_parser("reference", help="score the hand-written reference suite")

    g = sub.add_parser("generate", help="ask a model for test suites and record them")
    g.add_argument("out", type=Path)
    g.add_argument("--backend", default="claude-code", choices=["claude-code", "anthropic-api"])
    g.add_argument("--model", required=True)
    g.add_argument("--prompt", default="v2", choices=["v1", "v2"])
    g.add_argument("--samples", type=int, default=1)
    g.add_argument("--story", action="append", help="only this story (S1..S6); repeatable")

    e = sub.add_parser("evaluate", help="evaluate recorded runs and write results.json in each")
    e.add_argument("runs", type=Path, nargs="+")

    t = sub.add_parser("report", help="comparison table of evaluated runs")
    t.add_argument("runs", type=Path, nargs="+")

    gt = sub.add_parser("gate", help="fail when a run is below the floors or regresses against a baseline")
    gt.add_argument("candidate", type=Path)
    gt.add_argument("--baseline", type=Path)
    gt.add_argument("--config", type=Path, default=ROOT / "gate.json")

    a = p.parse_args(argv)

    if a.cmd == "mutants":
        for m in mutate.mutants():
            print(f"{m.id}  {m.ac or '-':8} {m.operator:10} {m.change}")
        return 0

    if a.cmd == "reference":
        ref = evaluate.reference()
        print(json.dumps(ref["summary"], indent=1))
        by_id = {m.id: m for m in mutate.mutants()}
        print("\nNot killed by the reference suite:")
        for mid in ref["survivors"]:
            print(f"  {mid}  {by_id[mid].change}")
        return 0

    if a.cmd == "generate":
        from .generate import generate

        generate(a.out, a.backend, a.model, a.prompt, a.samples, a.story)
        return 0

    if a.cmd == "evaluate":
        killable = evaluate.killable()
        for run in a.runs:
            r = runs.evaluate_run(run, killable)
            print(runs.table([r]).splitlines()[-1])
        return 0

    if a.cmd == "report":
        print(runs.table([runs.load(r) for r in a.runs]))
        return 0

    if a.cmd == "gate":
        config = json.loads(a.config.read_text())
        problems = runs.gate(runs.load(a.candidate), runs.load(a.baseline) if a.baseline else None, config)
        for problem in problems:
            print(f"FAIL  {problem}")
        print("gate passed" if not problems else f"gate failed: {len(problems)} problem(s)")
        return 1 if problems else 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
