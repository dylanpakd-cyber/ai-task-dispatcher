# contributing

Small tool, hard rules. PRs are welcome inside them.

## House rules

1. **The core stays small.** `dispatch.py` is ~220 lines and stays under
   ~250. If a feature can't fit without bloating the core, it becomes a
   separate file; if it can't be a separate file, it doesn't go in.
2. **stdlib only.** No dependencies, no framework, no yaml. A fresh
   clone with Python 3.9+ and git must run everything.
3. **No keys, ever.** There is no `.env` in this repo on purpose. Model
   auth lives in the codex/claude CLIs. Never commit, echo, or log a
   credential — including in test fixtures and example output.
4. **Every number is generated.** Any figure in the README or docs comes
   from shipped code and states n, date, and caveats (see `receipts/`).
   No estimates dressed as measurements.
5. **Adapters land with a real run.** A new agent adapter ships together
   with a receipt of a real verified dispatch, or it waits.

## Dev loop

```bash
python3 -m unittest discover -s tests -v   # dispatcher self-tests
sh examples/run-demo.sh                    # green path, keyless
sh examples/run-demo-broken.sh             # red path, must bounce
sh examples/run-gallery.sh                 # every runnable gallery spec
```

All four keyless. CI runs exactly these on every PR — no green, no
merge, literally.

Before pushing, do what CI can't:

```bash
# key sweep — must come back clean or placeholder-only
git grep -iE "api[_-]?key|sk-[a-zA-Z0-9]{10,}|secret|token"
# fresh-clone verify
git clone . /tmp/atd-verify && cd /tmp/atd-verify && sh examples/run-demo.sh
```

## Adding a gallery spec

Runnable specs need a scenario repo under `examples/` (tiny,
stdlib-only) and a line in `examples/run-gallery.sh`; they get verified
by CI forever after. Templates need brackets a stranger can fill and a
verify line that actually gates the work. Either way, add a row to
`tasks/gallery/README.md` with an honest verification status.

## Scope

One repo, one job: dispatch one task to one worker behind one gate.
Orchestration, queues, dashboards, and swarms are out of scope — ideas
that need them belong in a fork or an issue, not the core.
