# gallery: rename a symbol everywhere (template)

Template — fill the brackets before dispatching; it does not run as-is.
The verify line makes "everywhere" executable: the old name must be gone
from source AND the suite must still pass.

goal: rename [old_name] to [new_name] across the codebase, including call sites and docstrings
context: [the file that defines old_name]
allowed: [src/], [docs/ if the name appears there]
forbidden: tests/* unless the tests reference [old_name] — then list the specific test files under allowed instead
verify: [sh -c '! grep -rn "old_name" src/ && python3 -m pytest']
done: no occurrence of [old_name] outside the changelog, full suite green
budget: 10
retries: 2
