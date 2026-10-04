# AI Evaluation Lab

How good are the tests an AI writes?

A model can write a hundred tests in a minute. That says nothing about whether they are right, or whether they would catch a bug. This lab asks models to write pytest suites from user stories, the way a QA engineer gets a ticket, without seeing the code. Then it scores every suite against a reference implementation:

1. **Is each test valid?** It must pass on the correct code, twice. A test that fails there asserts something the stories never said.
2. **Which bugs does the suite catch?** The code is mutated 87 ways, one small bug at a time, and a mutant is caught when at least one valid test fails on it.
3. **Is every acceptance criterion really checked?** A test tagged with a criterion only counts when it catches a bug in the code that implements that criterion.
4. **What is dead weight?** Tests that catch nothing, and tests that catch exactly what another test already catches.

No model is called to evaluate. The generated suites are recorded in `runs/`, and CI re-scores them on every push and checks the numbers come out the same.

![CI](https://github.com/pedromorago/ai-evaluation-lab/actions/workflows/ci.yml/badge.svg)

## Results

Two models, two prompts, two samples each. `v1` asks for tests of the story. `v2` adds test-design guidance: cover every criterion, test both sides of every limit, compute expected values by hand, assert only what the story states.

| Run | Tests per suite | Valid | Mutants caught | Criteria verified | Invalid tests | Redundant tests |
|---|---|---|---|---|---|---|
| Haiku 4.5, v1 | 115 | 94% | 93% (91–94%) | 21 of 21 | 7.0 | 34.0 |
| Haiku 4.5, v2 | 138 | 95% | 95% (94–95%) | 21 of 21 | 7.5 | 46.5 |
| Sonnet 5.5, v1 | 181 | 99% | 99% (99–99%) | 21 of 21 | 1.0 | 50.0 |
| Sonnet 5.5, v2 | 170 | 99% | 99% (99–99%) | 21 of 21 | 2.5 | 56.0 |

Averages over the two samples, ranges in brackets. "Mutants caught" counts the 82 mutants the hand-written reference suite catches; the other five behave exactly like the original (see below).

Mutants caught by each story's own test file:

| Story | Haiku v1 | Haiku v2 | Sonnet v1 | Sonnet v2 |
|---|---|---|---|---|
| S1 Cart lines | 95% | 95% | 100% | 100% |
| S2 Volume discount | 100% | 96% | 100% | 100% |
| S3 Coupons | 77% | 88% | 96% | 96% |
| S4 Loyalty | 71% | 71% | 86% | 86% |
| S5 Shipping | 100% | 100% | 100% | 100% |
| S6 Tax and rounding | 83% | 92% | 92% | 92% |

### What the numbers show

- **Sonnet's invalid tests are arithmetic slips.** Every step is right in a comment and the last addition is wrong: `total = 0.00 + 4.99 + 1.05 = 5.04`. Haiku's are mostly rules applied in the wrong place: it forgets the volume discount when it tests 99 units, charges VAT on shipping that is free in that cart, or counts the volume discount as part of `discount`, which the API says it isn't.
- **An invalid test can hide a gap.** In one Haiku suite, the only tests at the 99-unit limit were the ones with the wrong expected total. Being invalid, they don't count, so nothing checked the limit, and the mutant that rejects 99 units survived. The suite looked like it covered S1-AC2.
- **The test-design prompt helped the smaller model a little and the larger one not at all.** Haiku caught 93% with v1 and 95% with v2. Sonnet caught 99% either way, and one of its v2 samples had five invalid tests, all the same slip (4.99 + 1.05 written as 5.04).
- **Rounding order is the blind spot.** No suite from any model catches M016, which skips rounding the subtotal before the coupon minimum is checked. It only shows when the unrounded subtotal ends in half a cent and the minimum sits exactly at the rounded value. The reference suite has that test; no model wrote it.
- **About a third of every suite is redundant.** Between 34 and 56 tests per suite catch exactly the same mutants as another test in it. Some of that is a parametrized boundary; most of it is the same check with different numbers.
- **The smaller model was the slower one.** Haiku's calls added up to 1,181 and 1,595 seconds for its two runs, with 213k and 276k output tokens; Sonnet's to 390 and 531 seconds, with 62k and 88k.

### The regression gate

`gate.json` sets floors (97% valid, 95% of mutants caught, every criterion verified) and the largest drop allowed against a baseline run, overall and per story. CI passes Sonnet v2 against Sonnet v1, and runs one gate that has to fail: switching to the smaller model.

```
$ aievals gate runs/haiku-4.5-v2 --baseline runs/sonnet-5.5-v1
FAIL  validity is 0.948, below the floor of 0.97
FAIL  mutation_score is 0.945, below the floor of 0.95
FAIL  validity dropped by 0.046 against sonnet-5.5-v1 (allowed 0.02)
FAIL  mutation_score dropped by 0.043 against sonnet-5.5-v1 (allowed 0.02)
FAIL  S4 mutation score dropped from 0.86 to 0.71
gate failed: 5 problem(s)
```

## How it works

### The system under test

`sut/checkout` prices a shopping cart: line totals, volume discounts, coupons, a loyalty tier, shipping and VAT, in `Decimal`. Six user stories in `stories/` describe it, with 21 acceptance criteria, and `stories/API.md` gives the public API. The model sees the stories and the API, never the code.

Every rule in `pricing.py` carries the criterion it implements in a trailing comment, `# S3-AC4`. That is what lets a mutant say which criterion it breaks.

### Mutants

`src/aievals/mutate.py` walks the syntax tree and makes one change at a time: a comparison (`<` to `<=`), an operator, a constant one unit off (`Decimal("50.00")` to `Decimal("50.01")`), `min` for `max`, the rounding mode, a dropped rounding, a deleted `raise` or call. 87 mutants, numbered in a stable order.

The reference suite in `reference/`, written by hand from the same stories, catches 82 of them. The five it doesn't can't be caught by any test, and `tests/test_reference.py` pins them: four drop a rounding that is applied to amounts already in whole cents, and one lets a quantity of 100 through a check that a later check rejects anyway. The mutation score only counts the 82.

### Running untrusted code

Generated tests are code nobody has read. Before anything runs them, `static.py` rejects a file that imports anything beyond pytest, `decimal`, `datetime` and `checkout`, or calls `open`, `eval`, `exec` and the like. The rest run in a throwaway directory, in a separate process, against a fresh copy of the package with the mutant swapped in, under a timeout. A small pytest plugin records each test's outcome and its criterion tags.

### Seeded bugs in the evaluator

An evaluator that is wrong hands out scores nobody earned, and the numbers still look like numbers. `src/aievals/faults.py` holds ten mistakes that are easy to make in a harness like this one, each behind a switch, and `scripts/run_seeded_bugs.py` turns them on one at a time and runs the lab's own tests. Every one is caught:

| Seeded bug | Caught by |
|---|---|
| Kills counted for tests that already fail on the correct code | `test_a_test_failing_on_the_reference_is_invalid_and_kills_nothing` |
| A criterion counted as covered because a test is tagged with it | `test_a_tag_is_verified_only_by_a_kill_in_that_criterion` |
| Mutation score divided by every mutant, including uncatchable ones | `test_mutation_score_counts_only_killable_mutants` |
| A test whose only check is `pytest.raises` reported as asserting nothing | `test_pytest_raises_is_an_assertion` and one more |
| A test that passes once and fails once counted as valid | `test_a_test_that_passes_once_and_fails_once_is_flaky` |
| The runner copies the original module instead of the mutant | `test_a_mutant_is_really_applied`, `test_reference_suite_kills_every_mutant_that_can_be_killed` |
| The gate compares the candidate against itself | `test_a_drop_in_mutation_score_fails` and one more |
| Redundant tests found by name instead of by what they catch | `test_redundant_tests_are_found_by_what_they_kill` |
| Mutants mapped to the criterion on the next line | four tests in `test_mutate.py` and `test_reference.py` |
| A test file that writes to disk or starts processes is run | `test_file_and_process_access_is_not_run` |

## Running it

```bash
pip install -e .
pytest                          # the evaluator's tests, and the reference suite on the checkout code
aievals reference               # score the reference suite, list the mutants it can't catch
aievals evaluate runs/*/        # re-score the recorded runs
aievals report runs/*/          # the comparison table
aievals gate runs/sonnet-5.5-v2 --baseline runs/sonnet-5.5-v1
python scripts/run_seeded_bugs.py
```

Generating new suites needs a model. Two backends turn it into a plain call (a fixed system prompt, no tools, one message in, one out):

```bash
# Claude Code in print mode, on a Claude subscription
aievals generate runs/my-run --backend claude-code --model claude-sonnet-5-5 --prompt v2 --samples 2

# The Anthropic API
pip install -e ".[api]"
ANTHROPIC_API_KEY=... aievals generate runs/my-run --backend anthropic-api --model claude-sonnet-5-5
```

Each run directory keeps the manifest (backend, the model that answered, the prompt version and its hash), the raw responses and one suite per sample. The runs here were generated with the Claude Code backend.

## Limits

- One small domain. Pricing rules are precise and easy to check, which suits mutation testing; a fuzzier spec would make "valid" harder to define.
- Two samples per configuration show the spread, but are not enough for confidence intervals.
- Mutation testing measures what a suite would catch among the bugs the operators can make. A bug outside those operators, like a misread requirement implemented consistently, is invisible to it, and so is a test that checks the right thing for the wrong reason.
- The models write one story at a time, with the other stories as context. Generating the whole suite at once would be a different experiment.
