# adapters

An adapter is ~5 lines inside `run_agent()`: build a command, run it
with the prompt, return the `CompletedProcess`. The dispatcher treats
every worker identically — exit 0 means "the worker believes it's done",
and then the diff gate and the verify command decide whether that's
true. The spec plus the gate is the contract; no adapter gets a softer
deal.

## codex

```
codex exec --cd <worktree> --sandbox workspace-write [-m <model>] -
```

The prompt goes in on stdin. `--sandbox workspace-write` scopes writes
to the worktree; `model:` in the spec passes through as `-m` (any tier
your codex install serves, the gpt-5.6 family included). Auth is
whatever `codex login` already set up.

## claude

```
claude --print --add-dir <worktree> \
  --allowedTools=Read,Grep,Glob,Edit,Write,Bash(git *),Bash(python *),Bash(python3 *) \
  --permission-mode acceptEdits [--model <model>]
```

Headless one-shot mode, prompt on stdin, cwd set to the worktree. The
tool allowlist keeps it to reading, editing, git, and python — enough to
do a task and run its tests, nothing else. Auth is whatever the claude
CLI already carries.

## mock

The spec's `mock:` line runs as a shell command in the worktree, in
place of a model. It exists for two reasons:

- the gate itself stays testable (CI dispatches deterministic mock
  workers on every push, no keys)
- the demos run on a fresh clone with zero setup

A mock that "does the task" proves the loop and the verify line are
coherent. A mock that cheats (see `tasks/example-forbidden.md`) proves
the gate catches it.

## Adding one

Add an `elif` to `run_agent()`: build the command, include the worktree,
pass the prompt, return the `CompletedProcess`. Ground rules from
[CONTRIBUTING.md](../CONTRIBUTING.md):

- the core stays ~250 lines — if your adapter can't fit in a handful of
  lines, it doesn't go in `dispatch.py`
- auth stays in the underlying CLI or env; the dispatcher never handles
  keys
- an adapter lands with a real verified run, or it doesn't land —
  gemini CLI and a local-model path (ollama) are on the roadmap under
  exactly that rule
