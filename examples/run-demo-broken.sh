#!/bin/sh
# red path: a worker tries to weaken the tests to get green. it gets bounced.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
demo="${TMPDIR:-/tmp}/ngnm-demo-broken-$$"
mkdir -p "$demo"
cp -R "$here/target-repo/." "$demo"
git -C "$demo" init -q
git -C "$demo" add -A
git -C "$demo" -c user.email=demo@ngnm -c user.name=ngnm commit -qm "seed target repo"
echo "target repo: $demo"
if python3 "$here/../dispatch.py" "$here/../tasks/example-forbidden.md" --repo "$demo"; then
    echo "ERROR: the forbidden run should have bounced" >&2
    exit 1
else
    echo "bounced as designed. no green, no merge."
fi
