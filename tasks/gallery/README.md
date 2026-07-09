# task spec gallery

Copy-paste specs for common daily dev work. Two kinds:

- **Runnable**: bound to a tiny scenario repo under `examples/`, verified
  with a deterministic mock worker on every CI run (`sh
  examples/run-gallery.sh`, no keys needed). Delete the `mock:` line and
  set `agent:` to dispatch a real model at the same task.
- **Template**: bracketed, for your own repo. Fill every `[bracket]`,
  then check it parses with `python3 dispatch.py tasks/gallery/<spec>.md --check`.

| spec | task | kind | verified |
|---|---|---|---|
| [fix-failing-test.md](fix-failing-test.md) | fix the bug the red suite points at | runnable | mock in CI + real codex run (see `receipts/`) |
| [add-endpoint.md](add-endpoint.md) | add a small endpoint a red test defines | runnable | mock in CI + real codex run (see `receipts/`) |
| [refactor-extract-helper.md](refactor-extract-helper.md) | dedupe logic, keep tests green | runnable | mock in CI |
| [bump-dependency.md](bump-dependency.md) | bump a pin, fix the fallout | template | template only |
| [fix-lint.md](fix-lint.md) | linter to 0 without behavior change | template | template only |
| [write-regression-test.md](write-regression-test.md) | lock in a fix (inverted gate: tests allowed, source forbidden) | template | template only |
| [rename-symbol.md](rename-symbol.md) | rename everywhere, executably "everywhere" | template | template only |

## Writing your own

Start from [`tasks/TEMPLATE.md`](../TEMPLATE.md), keep the spec-writing
rules from the README in mind, and read
[`docs/spec-format.md`](../../docs/spec-format.md) for exactly how each
line is parsed. The short version: one goal sentence, allowed is a
whitelist, tests go in forbidden, and verify must be a command that exits
0 only when the work is really done.
