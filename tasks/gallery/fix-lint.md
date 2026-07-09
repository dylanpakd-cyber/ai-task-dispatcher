# gallery: make the linter pass without changing behavior (template)

Template — fill the brackets before dispatching; it does not run as-is.
The two-part verify is the trick: lint clean AND tests green, so the
worker can't silence a warning by changing what the code does.

goal: make [ruff check . / flake8 / eslint .] exit 0 without changing any behavior
context: [the files the linter flags — paste the current lint output here]
allowed: [src/ paths with lint errors]
forbidden: tests/*, [linter config file — no rule-muting]
verify: [ruff check . && python3 -m pytest]
done: linter exits 0, no rules disabled, full suite still green
budget: 10
retries: 2
