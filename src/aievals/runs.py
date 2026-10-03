"""Evaluating recorded runs, gating one against another, and the comparison table."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from . import evaluate, mutate

HEADLINE = ["validity", "mutation_score", "criteria_verified", "invalid", "flaky", "inert", "redundant", "no_assertion"]


def evaluate_run(run: Path, killable: set[str] | None = None) -> dict:
    ms = mutate.mutants()
    killable = evaluate.killable() if killable is None else killable
    samples = {}
    for suite in sorted(run.glob("sample-*")):
        samples[suite.name] = evaluate.evaluate(evaluate.read_suite(suite), ms, killable)
    if not samples:
        raise FileNotFoundError(f"no samples in {run}")
    summaries = [s["summary"] for s in samples.values()]
    aggregate = {}
    for key in summaries[0]:
        values = [s[key] for s in summaries]
        aggregate[key] = {"mean": round(mean(values), 4), "min": min(values), "max": max(values)}
    stories = {}
    for sid in next(iter(samples.values()))["per_story"]:
        scores = [s["per_story"][sid]["mutation_score"] for s in samples.values()]
        scores = [x for x in scores if x is not None]
        stories[sid] = {"mutation_score": round(mean(scores), 4) if scores else None}
    manifest = json.loads((run / "manifest.json").read_text()) if (run / "manifest.json").exists() else {}
    result = {"run": run.name, "manifest": manifest, "aggregate": aggregate, "per_story": stories, "samples": samples}
    (run / "results.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    return result


def load(run: Path) -> dict:
    return json.loads((run / "results.json").read_text())


def gate(candidate: dict, baseline: dict | None, config: dict) -> list[str]:
    """Returns the reasons the candidate fails; an empty list means it passes."""
    from . import faults

    problems = []
    agg = candidate["aggregate"]
    for metric, floor in config.get("min", {}).items():
        value = agg[metric]["mean"]
        if metric == "criteria_verified":
            value = value / agg["criteria"]["mean"]
        if value < floor:
            problems.append(f"{metric} is {value:.2f}, below the floor of {floor}")
    for metric, ceiling in config.get("max", {}).items():
        if agg[metric]["mean"] > ceiling:
            problems.append(f"{metric} is {agg[metric]['mean']}, above the ceiling of {ceiling}")
    if baseline is not None:
        reference = candidate if faults.active("gate-ignores-regression") else baseline
        for metric, allowed in config.get("max_drop", {}).items():
            drop = reference["aggregate"][metric]["mean"] - agg[metric]["mean"]
            if drop > allowed:
                problems.append(f"{metric} dropped by {drop:.3f} against {baseline['run']} (allowed {allowed})")
        allowed = config.get("max_story_drop")
        if allowed is not None:
            for sid, base in reference["per_story"].items():
                now = candidate["per_story"].get(sid, {}).get("mutation_score")
                if base["mutation_score"] is not None and now is not None and base["mutation_score"] - now > allowed:
                    problems.append(f"{sid} mutation score dropped from {base['mutation_score']:.2f} to {now:.2f}")
    return problems


def table(results: list[dict]) -> str:
    rows = ["| Run | Model | Prompt | Samples | Tests | Valid | Mutation score | Criteria verified | Invalid | Inert | Redundant |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        a, m = r["aggregate"], r["manifest"]
        rows.append(
            f"| {r['run']} | {m.get('model', '')} | {m.get('prompt', '')} | {len(r['samples'])} "
            f"| {a['tests']['mean']:.0f} | {a['validity']['mean']:.0%} | {a['mutation_score']['mean']:.0%} "
            f"({a['mutation_score']['min']:.0%}–{a['mutation_score']['max']:.0%}) "
            f"| {a['criteria_verified']['mean']:.1f} of {a['criteria']['mean']:.0f} "
            f"| {a['invalid']['mean']:.1f} | {a['inert']['mean']:.1f} | {a['redundant']['mean']:.1f} |"
        )
    return "\n".join(rows)
