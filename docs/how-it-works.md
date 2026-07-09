# how the dispatcher works, in detail

The README gives the six steps; this is the same loop with every moving
part named. `dispatch.py` is ~220 lines of stdlib Python — reading it
alongside this page takes ten minutes and is worth it.

## The run, start to finish

1. **Parse the spec** (`parse_spec`). `goal:` and `verify:` are
   mandatory; everything else has defaults. See
   [spec-format.md](spec-format.md).

2. **Make a worktree** (`make_worktree`). The dispatcher never works in
   your checkout. It creates:

   - branch `ngnm/<slug>-<epoch>` from the target repo's `HEAD`
   - worktree `<repo>/.ngnm/worktrees/<slug>-<epoch>`

   `ngnm` stands for *no green, no merge* — the project's original name.
   The prefix stayed because it makes dispatcher branches unmistakable
   in `git branch` output.

3. **Build the prompt** (`build_prompt`). The worker sees exactly this:

   ```
   You are a worker dispatched by no-green-no-merge.
   Attempt N of M.
   Do the task in the spec below, inside the current repo.
   Only touch paths on the allowed list. Never touch forbidden paths.
   You are done when the verify command exits 0 and the done state is observable.
   Do not weaken, delete, or rewrite tests to get to green.

   TASK SPEC:
   <your spec file, verbatim>
   ```

   On retries, the failure evidence is appended:

   ```
   YOUR PREVIOUS ATTEMPT FAILED. Evidence:
   <violation list, or the last 2000 chars of the failing verify output>
   ```

4. **Dispatch the worker** (`run_agent`) with the remaining budget as a
   hard timeout. Adapter commands are in [adapters.md](adapters.md). A
   nonzero worker exit is a failed attempt; its stderr becomes the
   evidence for the next one.

5. **Gate the diff** (`changed_paths` + `violations`) — before verify
   ever runs. Any change to a forbidden path, or outside a non-empty
   allowed list, reverts the attempt (`git reset --hard && git clean
   -fd`) and feeds the violation back. This ordering is the point of the
   tool: a weakened test never gets the chance to make verify pass.

6. **Run verify** (`run_verify`) with the shell, in the worktree.
   - **Exit 0**: `git add -A`, commit as `ngnm: <goal>`, print the
     branch, exit 0. Done.
   - **Nonzero**: the last 2000 characters of output become the
     evidence, and the loop continues until attempts or the minute
     budget run out.

7. **Red at the end** (`bounce`): no branch. The worktree is kept so you
   can inspect what the worker tried; the bounce message prints the
   exact cleanup commands. Exit code 1.

## What lands where

| thing | where |
|---|---|
| the worker's changes | worktree `<repo>/.ngnm/worktrees/<run_id>/` |
| the branch (green runs only get committed work) | `ngnm/<run_id>` |
| worker transcript per attempt | `<repo>/.ngnm/logs/<run_id>/attempt-N-agent.log` |
| verify output per attempt | `<repo>/.ngnm/logs/<run_id>/attempt-N-verify.log` |

Logs live in the target repo's `.ngnm/`, never inside the worktree — so
the worker can't read or rewrite its own report card, and the diff gate
ignores them.

## Cleanup

After a green run you merge and delete like any branch. After a red run,
the bounce message prints the exact commands; the general form:

```bash
git worktree list                       # see what's stacked up
git worktree remove --force <path>      # drop one attempt
git branch -D ngnm/<run_id>             # and its branch
git worktree prune                      # tidy the bookkeeping
```

`.ngnm/` is safe to delete wholesale once you've merged what you want —
it holds only worktrees and logs.

## What it deliberately does not do

- **Never pushes, never merges.** Reviewing the diff and running
  `git merge` stays your job. That's the design, not a missing feature.
- **No parallelism, no queue, no daemon.** One spec, one worker, one
  exit code. If you need fan-out, run it N times.
- **No API calls of its own.** Model auth lives in the codex/claude
  CLIs; the dispatcher only ever shells out to them.
