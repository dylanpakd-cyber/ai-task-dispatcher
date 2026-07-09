# example: implement fizzbuzz

A deterministic demo that runs with no API key: the `mock:` line stands in
for the model, so you can watch the dispatch loop and the verify gate work
on a fresh clone. Delete the `mock:` line and set `agent: codex` (or
`agent: claude`) to run it with a real model.

goal: implement fizzbuzz(n) in calc.py so the test suite passes
context: calc.py, tests/test_calc.py
allowed: calc.py
forbidden: tests/*
verify: python3 -m unittest discover -s tests -t . -v
done: tests/test_calc.py passes, calc.py exports add and fizzbuzz
budget: 5
retries: 2
mock: printf 'def add(a, b):\n    return a + b\n\n\ndef fizzbuzz(n):\n    if n %% 15 == 0:\n        return "fizzbuzz"\n    if n %% 3 == 0:\n        return "fizz"\n    if n %% 5 == 0:\n        return "buzz"\n    return str(n)\n' > calc.py
