# gallery: add a small endpoint

Feature work with the contract already written down: the scenario ships a
red test (`tests/test_app.py::test_version`) that defines the endpoint,
and the task is green when the suite is. The worker may only touch the
app module; the tests that define the contract are forbidden.

Runs as-is against `examples/scenario-http-api` with a deterministic mock
worker: `sh examples/run-gallery.sh`. To use it on your own repo, delete
the `mock:` line, set `agent: codex` or `agent: claude`, and swap in your
framework's paths and test command.

goal: add GET /version to app.py returning {"version": "1.0.0"} so the test suite passes
context: app.py, tests/test_app.py
allowed: app.py
forbidden: tests/*
verify: python3 -m unittest discover -s tests -t . -v
done: GET /version returns 200 with {"version": "1.0.0"} and every test passes
budget: 5
retries: 2
mock: printf '\n\n@route("/version")\ndef version():\n    return {"version": "1.0.0"}\n' >> app.py
