# gallery: write a regression test for a bug you just fixed (template)

Template — fill the brackets before dispatching; it does not run as-is.
The gate is inverted: tests are ALLOWED and source is FORBIDDEN. The
worker locks in behavior that already works; it can't bend the code to
make its own test pass.

goal: write a regression test pinning the fix for [bug: one-line description, issue link if any]
context: [the fixed source file], [the existing test file for that area]
allowed: tests/*
forbidden: [src/ — the entire source tree]
verify: [python3 -m pytest tests/ -v]
done: a new test exists that exercises [the exact buggy input], named so a stranger can tell what it protects
budget: 10
retries: 2
