# gallery: fix a failing test (the bug is in the code, not the test)

The most common Tuesday task there is: the suite is red because the code
is wrong. Tests are forbidden, so a cornered worker can't "fix" the test
instead of the bug.

Runs as-is against `examples/scenario-failing-test` with a deterministic
mock worker: `sh examples/run-gallery.sh`. To use it on your own repo,
delete the `mock:` line, set `agent: codex` or `agent: claude`, and point
the paths at your code.

goal: fix latest() in versions.py so the whole test suite passes
context: versions.py, tests/test_versions.py
allowed: versions.py
forbidden: tests/*
verify: python3 -m unittest discover -s tests -t . -v
done: latest(["1.9.0", "1.10.0"]) returns "1.10.0" and every test passes
budget: 5
retries: 2
mock: printf 'def latest(versions):\n    """Return the highest version from a list of dotted version strings."""\n    return max(versions, key=lambda v: tuple(int(p) for p in v.split(".")))\n' > versions.py
