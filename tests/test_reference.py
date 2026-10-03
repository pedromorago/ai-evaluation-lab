"""The reference suite end to end: it kills every mutant except the ones that
can't be told apart from the original."""

import pytest

from aievals import evaluate
from aievals.mutate import mutants

# Each survivor, and why no test can kill it.
EQUIVALENT = {
    # The quote rounds amounts that are already whole cents: subtotal, discount, shipping, total.
    "drop the rounding to cents in `return Quote(": 4,
    # quantity 100 passes the per-line check but the merged check (> 99) still rejects it.
    "`99` → `100` in `if line.quantity < 1 or line.quantity > 99:`": 1,
}


@pytest.mark.slow
def test_reference_suite_kills_every_mutant_that_can_be_killed():
    result = evaluate.reference(use_cache=False)
    by_id = {m.id: m for m in mutants()}
    survivors = [by_id[s].change for s in result["survivors"]]
    for pattern, count in EQUIVALENT.items():
        assert sum(pattern in s for s in survivors) == count, pattern
    assert len(survivors) == sum(EQUIVALENT.values())
    assert result["summary"]["validity"] == 1.0
    assert result["summary"]["criteria_verified"] == result["summary"]["criteria"]
