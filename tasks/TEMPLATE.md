# task spec template

Copy this file, fill the brackets, point any model with a terminal at it.
The verify line is the whole trick. Works on sol, fable, codex.

goal: [one sentence outcome]
context: [files the worker reads first]
allowed: [paths it may touch]
forbidden: [paths it must not touch]
verify: [command that must exit 0]
done: [observable end state]
budget: [max minutes before kill]
