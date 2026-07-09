# example: implement fizzbuzz, real model

Same task as example-fizzbuzz.md but dispatched to a real worker through
the codex CLI. Set `model:` to whatever your codex install serves
(gpt-5.6 tiers included), or delete the line to use its default.

goal: implement fizzbuzz(n) in calc.py so the test suite passes
context: calc.py, tests/test_calc.py
allowed: calc.py
forbidden: tests/*
verify: python3 -m unittest discover -s tests -t . -v
done: tests/test_calc.py passes, calc.py exports add and fizzbuzz
budget: 10
retries: 2
agent: codex
