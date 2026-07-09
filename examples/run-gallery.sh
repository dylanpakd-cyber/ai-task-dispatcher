#!/bin/sh
# dispatch every runnable gallery spec against its bundled scenario repo,
# using the deterministic mock worker. no keys needed. exits nonzero if
# any spec fails to go green. CI runs this on every push.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
root="$here/.."

run() {
    spec="$1"
    scenario="$2"
    demo="${TMPDIR:-/tmp}/ngnm-gallery-$$-$scenario"
    mkdir -p "$demo"
    cp -R "$here/$scenario/." "$demo"
    git -C "$demo" init -q
    git -C "$demo" add -A
    git -C "$demo" -c user.email=demo@ngnm -c user.name=ngnm commit -qm "seed $scenario"
    echo ""
    echo "=== gallery: $spec vs $scenario ==="
    python3 "$root/dispatch.py" "$root/tasks/gallery/$spec" --repo "$demo"
}

run fix-failing-test.md scenario-failing-test
run add-endpoint.md scenario-http-api
run refactor-extract-helper.md scenario-refactor

echo ""
echo "gallery: every runnable spec went green."
