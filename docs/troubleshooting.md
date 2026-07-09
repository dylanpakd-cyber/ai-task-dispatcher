# troubleshooting

Short answers first, then the sharp edges worth knowing about.

## "spec error: budget and retries must be numbers. still holding [brackets]?"

You dispatched a template without filling the `[brackets]`. Run
`python3 dispatch.py <spec> --check` after editing — it validates and
prints what the parser understood without dispatching anything.

## "agent exited 1" (or any nonzero) on every attempt

Read the transcript: `<repo>/.ngnm/logs/<run_id>/attempt-N-agent.log`.
The usual cause is the worker CLI itself — not installed, not
authenticated, or not on PATH. Check `codex --version` / `claude
--version` and their login state. The dispatcher has no keys of its own
and no fallback; if the CLI can't run, the attempt fails.

## GREEN never commits / "Author identity unknown"

`dispatch.py` commits inside the worktree with your ambient git
identity. On a machine without one (CI runners, fresh containers), set
it first:

```bash
git config --global user.email "you@example.com"
git config --global user.name "you"
```

This repo's own CI does exactly that before running the demos.

## The worker touched a forbidden path

Working as intended: the attempt was reverted before verify ran, the
violation was fed back as evidence, and the worker got another try. If
it happens on every attempt, your `allowed` list is probably too narrow
for the task — the worker legitimately needs a path you didn't grant.

## Budget ran out mid-attempt

The minute budget is a hard wall-clock timeout across all attempts. When
it fires, the run bounces and the worktree is kept for inspection.
Budgets are per-task honesty checks: if a task genuinely needs more than
~15 minutes, split it before raising the number.

## Stale worktrees and ngnm/ branches piling up

Red runs keep their worktrees on purpose. Clean up per-run with the
commands the bounce message printed, or wholesale:

```bash
git worktree list
git worktree remove --force <repo>/.ngnm/worktrees/<run_id>
git branch -D ngnm/<run_id>
git worktree prune
```

Deleting `.ngnm/` entirely is safe once you've merged what you want.

## Sharp edges (for people modifying dispatch.py)

- **Porcelain parsing is positional.** `changed_paths()` reads
  `git status --porcelain` v1, where a line is `XY path` and a
  modified-unstaged file starts with a *space*. Lines must never be
  stripped before slicing `line[3:]`. The test suite pins this against
  a real git repo — if your change breaks `tests/test_dispatch.py`,
  believe the test.
- **`__pycache__` / `*.pyc` / `.ngnm/` are filtered from the diff gate
  on purpose.** Workers run test suites; test suites generate bytecode.
  Treating that as a path violation would bounce honest work.
- **Verify runs with the shell, in the worktree, every attempt.** Give
  it no side effects beyond the worktree (no deploys, no DB writes, no
  `pip install` into an environment you care about).
- **The evidence window is 2000 characters.** Verify output and worker
  stderr are truncated from the left before being fed back. Design your
  verify command so the useful failure is at the end (most test runners
  already do this).
