# the task spec format, precisely

A task spec is one markdown file. The parser scans it line by line for
known keys; everything else is prose and gets ignored, so you can write
as much explanation around the keys as you like (the bundled examples
do).

Validate any spec without dispatching:

```bash
python3 dispatch.py path/to/spec.md --check
```

## Keys

| key | required | default | meaning |
|---|---|---|---|
| `goal` | yes | — | one-sentence outcome. Goes into the worker prompt verbatim. |
| `verify` | yes | — | shell command run in the worktree. Exit 0 is the only definition of done. |
| `context` | no | empty | files the worker should read first. Prompt guidance only, not enforced. |
| `allowed` | no | empty | whitelist of paths the worker may change. Empty = anything not forbidden. |
| `forbidden` | no | empty | paths the worker must not change. Enforced on the diff, beats `allowed`. |
| `done` | no | empty | the observable end state, written for the human reviewing the diff. |
| `budget` | no | `15` | wall-clock minutes for the whole run, all attempts included. |
| `retries` | no | `2` | total attempts (floor 1). Historical name; it counts attempts, not re-tries. |
| `agent` | no | `codex` | `codex`, `claude`, or `mock`. Defaults to `mock` if a `mock:` line exists. |
| `model` | no | adapter default | passed through: `codex -m <model>` / `claude --model <model>`. |
| `mock` | no | — | shell command run in place of a model. For demos and testing the gate. |

`goal` and `verify` must be present and non-empty or the spec is
rejected. A non-numeric `budget` or `retries` (usually an unfilled
`[bracket]`) is rejected with a clear error instead of a traceback.

## Parsing rules

- A key line is `key: value` at the start of a line. Keys are
  case-insensitive (`GOAL:` works).
- An indented line (starting with a space or tab) continues the previous
  key. This is how you write multi-line values:

  ```
  allowed: src/api.py
    src/models.py
    src/migrations/
  ```

- Any other line — prose, headings, blank lines — is ignored and also
  ends a continuation.
- `allowed` and `forbidden` are lists, split on commas **and** newlines.
  Everything else is a single string.

## Path matching (`allowed` / `forbidden`)

Each changed path is compared to each pattern two ways:

1. **Glob** via Python `fnmatch`: `tests/*` matches
   `tests/test_calc.py`. Note `*` crosses directory separators in
   fnmatch, so `src/*` also matches `src/deep/nested.py`.
2. **Directory prefix**: a pattern with no glob characters matches
   everything under it — `src` (or `src/`) matches `src/deep/nested.py`.
   A trailing slash is stripped first.

Rules of engagement, checked on the actual git diff after the worker
runs and before verify:

- A change to a `forbidden` path is a violation, full stop — even if an
  `allowed` pattern also matches it.
- If `allowed` is non-empty, any change outside it is a violation.
- If `allowed` is empty, anything not forbidden is fair game.
- Violations revert the whole attempt (`git reset --hard && git clean
  -fd` in the worktree) and count as a failed attempt; the violation
  list is fed back to the worker as evidence.
- `__pycache__/`, `*.pyc`, and the dispatcher's own `.ngnm/` dir are
  filtered out before the check — running the test suite generates them
  and they are never the worker's fault.

## Writing specs that hold up

The README's rules, restated as a checklist:

- one goal sentence — two sentences is two tasks
- `allowed` is a whitelist of everything the worker legitimately needs,
  nothing else
- put the test files in `forbidden` — a cornered model edits the test
- `verify` must be executable and side-effect-free
- `done` tells the human reviewer what to look for
- keep `budget` honest — a 90-minute task is not one task
