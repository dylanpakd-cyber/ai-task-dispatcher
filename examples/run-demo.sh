#!/bin/sh
# green path: seed a throwaway repo, dispatch the fizzbuzz task, watch it merge-ready.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
demo="${TMPDIR:-/tmp}/ngnm-demo-$$"
mkdir -p "$demo"
cp -R "$here/target-repo/." "$demo"
git -C "$demo" init -q
git -C "$demo" add -A
git -C "$demo" -c user.email=demo@ngnm -c user.name=ngnm commit -qm "seed target repo"
echo "target repo: $demo"
python3 "$here/../dispatch.py" "$here/../tasks/example-fizzbuzz.md" --repo "$demo"
