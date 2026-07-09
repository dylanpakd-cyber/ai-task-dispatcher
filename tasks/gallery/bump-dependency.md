# gallery: bump a dependency safely (template)

Template — fill the brackets before dispatching; it does not run as-is.
Run it somewhere disposable (a venv or container): the verify line
installs packages, and verify should never mutate an environment you
care about.

goal: bump [package] from [old version] to [new version] and fix whatever the upgrade breaks
context: [requirements.txt or pyproject.toml], [the modules that import package]
allowed: [requirements.txt], [src/ paths that may need updating]
forbidden: tests/*
verify: [python3 -m pip install -r requirements.txt --quiet && python3 -m pip check && python3 -m pytest]
done: [package] pinned at [new version], install clean, full suite green
budget: 15
retries: 2
