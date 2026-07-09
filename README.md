# ai-task-dispatcher

Dispatch a coding task to an AI agent (codex, claude, or any model with a
terminal) from one markdown spec, behind an enforced test gate. One spec
in, a verified branch out. The house rule: no green, no merge.

## The one rule

If the verify command does not exit 0, you do not get a branch. That's it.
That's the whole harness. Models are good at almost finishing work; the
verify gate is what turns almost-finished into finished.

`dispatch.py` is about 200 lines of stdlib Python. No framework, no queue,
no yaml. You can read the entire thing in one sitting, and you should.

## Quickstart

No API key needed for the demo. The mock worker stands in for the model so
you can watch the loop and the gate work on a fresh clone:

```bash
git clone https://github.com/dylanpakd-cyber/ai-task-dispatcher
cd ai-task-dispatcher
sh examples/run-demo.sh          # green path: task done, branch returned
sh examples/run-demo-broken.sh   # red path: worker cheats, gets bounced
```

To dispatch a real model, point it at any git repo with a spec:

```bash
python3 dispatch.py tasks/example-fizzbuzz-codex.md --repo /path/to/your/repo
```

Auth is whatever your `codex` or `claude` CLI already carries. There is no
`.env` in this repo on purpose.

## The task spec format

Every task is one markdown file. Fill the brackets, point any model with a
terminal at it:

```
goal: [one sentence outcome]
context: [files the worker reads first]
allowed: [paths it may touch]
forbidden: [paths it must not touch]
verify: [command that must exit 0]
done: [observable end state]
budget: [max minutes before kill]
```

Optional extras: `agent: codex | claude | mock`, `model: <model-name>`,
`retries: <n>` (default 2), `mock: <shell command>` for deterministic tests.

The verify line is the whole trick. If you cannot write a command that
exits 0 when the work is done, the task is not specified yet, and no model
tier will save you.

## How the dispatcher works

1. Parse the spec. `goal:` and `verify:` are mandatory, everything else has defaults.
2. Create a fresh git worktree on a new `ngnm/` branch, so the worker never touches your checkout.
3. Dispatch the worker (codex, claude, or mock) with the spec as its prompt.
4. Diff check: any change to a `forbidden` path, or outside the `allowed` list, is reverted and counted as a failed attempt. Weakened tests never reach verify.
5. Run `verify`. Exit 0: commit, print the branch, done. Nonzero: feed the failure output back to the worker and retry, until retries or the minute budget run out.
6. Red at the end means no branch. The worktree is kept so you can inspect what it tried.

The dispatcher never pushes and never merges. Reviewing the diff and
running `git merge` stays your job, which is the point.

## Adapters

- **codex**: `codex exec` with a workspace-write sandbox. Set `model:` to any tier your install serves (the gpt-5.6 family included).
- **claude**: headless `claude --print` with edit permissions scoped to the worktree.
- **mock**: runs a shell command in place of the model. Exists so the gate itself is testable, and so the demo runs on a clone with zero keys.

The harness does not care which model tier does the typing. The spec plus
the gate is the contract; sol, fable, and codex are all held to the same
exit code.

## Writing specs workers can't drift on

- One goal sentence. If you need two sentences, it's two tasks.
- `allowed` is a whitelist. Everything a worker legitimately needs to touch, nothing else.
- Put the test files in `forbidden`. The first thing a cornered model does is edit the test.
- `verify` must be executable and side-effect-free. `python3 -m unittest`, `npm test`, `make check`. Not "looks right".
- `done` is for the human reviewing the diff: what observable state should exist.
- Keep `budget` honest. A task that needs 90 minutes is not one task.

## Measured results

Real runs of the example task, fresh clone, 2026-07-09:

| worker | task | result | attempts |
|---|---|---|---|
| codex CLI (default model) | implement fizzbuzz to spec | GREEN, branch returned | 1 |
| mock (deterministic demo) | implement fizzbuzz to spec | GREEN, branch returned | 1 |
| mock (cheating worker) | weaken tests to force green | BOUNCED: forbidden path touched | capped at 1 |

The third row is the reason this exists: the gate reverts and bounces a
worker that edits tests instead of code, before verify ever runs.

## What this is not

Not an orchestrator, not a swarm, not a framework. It dispatches one task
to one worker and holds it to one exit code. If you need fan-out, run it
N times. The value is the contract, not the plumbing.

## License

MIT. Built by [Dylan Pak](https://opentrade.live).
