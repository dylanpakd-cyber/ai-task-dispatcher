# gallery: refactor without breaking anything

Two functions carry the same copy-pasted formatting logic. Extract it
into one helper, keep every test green. The verify line checks both
halves of the contract: the suite still passes AND the helper actually
exists — "refactored" is an observable state, not a vibe.

Runs as-is against `examples/scenario-refactor` with a deterministic mock
worker: `sh examples/run-gallery.sh`. To use it on your own repo, delete
the `mock:` line, set `agent: codex` or `agent: claude`, and name the
duplication you want gone.

goal: extract the duplicated cents-to-dollars formatting in report.py into a format_cents() helper both functions use
context: report.py, tests/test_report.py
allowed: report.py
forbidden: tests/*
verify: python3 -m unittest discover -s tests -t . -v && grep -q "def format_cents" report.py
done: report.py has one format_cents() helper, line_item and total_line both call it, tests untouched and green
budget: 5
retries: 2
mock: printf 'def format_cents(cents):\n    return f"${cents // 100}.{cents %% 100:02d}"\n\n\ndef line_item(name, cents):\n    return f"{name}: {format_cents(cents)}"\n\n\ndef total_line(items):\n    return f"TOTAL: {format_cents(sum(c for _, c in items))}"\n' > report.py
