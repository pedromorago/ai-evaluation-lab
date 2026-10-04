from aievals.runs import gate


def result(run, validity, score, s2):
    agg = {"validity": validity, "mutation_score": score, "criteria_verified": 20, "criteria": 21, "invalid": 0}
    return {
        "run": run,
        "aggregate": {k: {"mean": v, "min": v, "max": v} for k, v in agg.items()},
        "per_story": {"S2": {"mutation_score": s2}},
    }


CONFIG = {"min": {"validity": 0.9, "criteria_verified": 0.9}, "max_drop": {"mutation_score": 0.05}, "max_story_drop": 0.1}


def test_a_run_as_good_as_the_baseline_passes():
    assert gate(result("new", 0.95, 0.80, 0.9), result("old", 0.95, 0.80, 0.9), CONFIG) == []


def test_a_drop_in_mutation_score_fails():
    problems = gate(result("new", 0.95, 0.70, 0.9), result("old", 0.95, 0.80, 0.9), CONFIG)
    assert any("mutation_score dropped" in p for p in problems)


def test_a_drop_in_one_story_fails_even_when_the_total_holds():
    problems = gate(result("new", 0.95, 0.80, 0.7), result("old", 0.95, 0.80, 0.9), CONFIG)
    assert problems == ["S2 mutation score dropped from 0.90 to 0.70"]


def test_floors_apply_without_a_baseline():
    assert gate(result("new", 0.85, 0.80, 0.9), None, CONFIG) == ["validity is 0.850, below the floor of 0.9"]
