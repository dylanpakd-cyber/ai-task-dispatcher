# receipts: real codex runs, 2026-07-09

Two runnable gallery specs dispatched to the real codex CLI
(codex-cli 0.144.0, default model), one run each (n=1 per spec), macOS,
Python 3.14. Every number in the table below comes from these logs.

| spec | worker | result | attempts | wall clock |
|---|---|---|---|---|
| tasks/gallery/fix-failing-test.md | codex CLI | GREEN, branch returned | 1 | 71s |
| tasks/gallery/add-endpoint.md | codex CLI | GREEN, branch returned | 1 | 81s |

Per run, this directory holds:

- `attempt-1-agent.log` — the worker's full transcript, straight from
  `.ngnm/logs/<run_id>/`.
- `attempt-1-verify.log` — the verify command's output (the exit-0 proof).
- `branch.diff` — what actually landed on the `ngnm/` branch
  (`__pycache__` binary noise excluded for readability; scenario repos
  now ship a `.gitignore` so fresh runs don't commit it at all).

## Reproduce

```bash
# seed a throwaway copy of the scenario, then dispatch for real:
cp -R examples/scenario-failing-test /tmp/scenario && cd /tmp/scenario
git init -q && git add -A && git commit -qm seed
# in the spec: delete the `mock:` line, add `agent: codex`
python3 /path/to/dispatch.py tasks/gallery/fix-failing-test.md --repo /tmp/scenario
```

Caveats: n=1 per spec, one machine, one day, default codex model. This is
a receipt that the loop works end to end with a real worker, not a
benchmark. The benchmark (many specs x many models, completion rate and
attempts-to-green) is the next roadmap item.
