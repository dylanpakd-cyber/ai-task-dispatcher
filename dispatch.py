#!/usr/bin/env python3
"""no-green-no-merge. one markdown spec in, a verified branch out.

the rule: if the verify command does not exit 0, you do not get a branch.
stdlib only. auth is whatever your codex / claude CLI already carries.
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
import time
from pathlib import Path

KNOWN_KEYS = ("goal", "context", "allowed", "forbidden", "verify", "done",
              "budget", "agent", "model", "retries", "mock")
LIST_KEYS = ("allowed", "forbidden")


class SpecError(ValueError):
    pass


def parse_spec(path: Path) -> dict:
    raw = path.read_text()
    spec: dict = {"path": path, "raw": raw}
    key = None
    for line in raw.splitlines():
        match = re.match(rf"^({'|'.join(KNOWN_KEYS)}):\s*(.*)$", line, re.IGNORECASE)
        if match:
            key = match.group(1).lower()
            spec[key] = match.group(2).strip()
        elif key and line[:1] in (" ", "\t") and line.strip():
            spec[key] += "\n" + line.strip()
        else:
            key = None
    for required in ("goal", "verify"):
        if not spec.get(required):
            raise SpecError(f"spec needs a non-empty {required}: line. the verify line is the whole trick.")
    for k in LIST_KEYS:
        spec[k] = [p.strip() for p in re.split(r"[,\n]", spec.get(k, "")) if p.strip()]
    try:
        spec["budget"] = float(spec.get("budget") or 15)
        spec["retries"] = max(1, int(spec.get("retries") or 2))
    except ValueError:
        raise SpecError("budget and retries must be numbers. still holding [brackets]?") from None
    spec["agent"] = (spec.get("agent") or ("mock" if spec.get("mock") else "codex")).lower()
    if spec["agent"] not in ("codex", "claude", "mock"):
        raise SpecError("agent must be codex, claude, or mock")
    return spec


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def make_worktree(repo: Path, slug: str) -> tuple[Path, str, str]:
    run_id = f"{slug}-{int(time.time())}"
    branch = f"ngnm/{run_id}"
    worktree = repo / ".ngnm" / "worktrees" / run_id
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-B", branch, str(worktree), "HEAD")
    return worktree, branch, run_id


def changed_paths(worktree: Path) -> list[str]:
    # no strip here: porcelain lines are positional and may start with a space
    result = subprocess.run(["git", "status", "--porcelain"], cwd=worktree,
                            text=True, capture_output=True)
    paths = [line[3:].split(" -> ")[-1].strip('"')
             for line in result.stdout.splitlines() if line.strip()]
    return [p for p in paths if not p.startswith(".ngnm")
            and "__pycache__" not in p and not p.endswith(".pyc")]


def matches(path: str, pattern: str) -> bool:
    pattern = pattern.rstrip("/")
    return fnmatch.fnmatch(path, pattern) or path.startswith(pattern + "/")


def violations(paths: list[str], allowed: list[str], forbidden: list[str]) -> list[str]:
    bad = [f"forbidden path touched: {p}" for p in paths
           if any(matches(p, pat) for pat in forbidden)]
    if allowed:
        bad += [f"path outside allowed list: {p}" for p in paths
                if not any(matches(p, pat) for pat in allowed)
                and not any(matches(p, pat) for pat in forbidden)]
    return bad


def build_prompt(spec: dict, attempt: int, feedback: str) -> str:
    parts = [
        "You are a worker dispatched by no-green-no-merge.",
        f"Attempt {attempt} of {spec['retries']}.",
        "Do the task in the spec below, inside the current repo.",
        "Only touch paths on the allowed list. Never touch forbidden paths.",
        "You are done when the verify command exits 0 and the done state is observable.",
        "Do not weaken, delete, or rewrite tests to get to green.",
        "",
        "TASK SPEC:",
        spec["raw"],
    ]
    if feedback:
        parts += ["", "YOUR PREVIOUS ATTEMPT FAILED. Evidence:", feedback]
    return "\n".join(parts)


def run_agent(spec: dict, worktree: Path, prompt: str, timeout: float) -> subprocess.CompletedProcess:
    if spec["agent"] == "mock":
        return subprocess.run(spec["mock"], shell=True, cwd=worktree, text=True,
                              capture_output=True, timeout=timeout)
    if spec["agent"] == "codex":
        cmd = ["codex", "exec", "--cd", str(worktree), "--sandbox", "workspace-write"]
        if spec.get("model"):
            cmd += ["-m", spec["model"]]
        cmd.append("-")
        return subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=timeout)
    tools = "Read,Grep,Glob,Edit,Write,Bash(git *),Bash(python *),Bash(python3 *)"
    cmd = ["claude", "--print", "--add-dir", str(worktree),
           f"--allowedTools={tools}", "--permission-mode", "acceptEdits"]
    if spec.get("model"):
        cmd += ["--model", spec["model"]]
    return subprocess.run(cmd, input=prompt, cwd=worktree, text=True,
                          capture_output=True, timeout=timeout)


def run_verify(command: str, worktree: Path) -> tuple[int, str]:
    result = subprocess.run(command, shell=True, cwd=worktree, text=True, capture_output=True)
    output = (result.stdout + "\n" + result.stderr).strip()
    return result.returncode, output[-2000:]


def log(repo: Path, run_id: str, attempt: int, name: str, text: str) -> None:
    log_dir = repo / ".ngnm" / "logs" / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f"attempt-{attempt}-{name}.log").write_text(text)


def bounce(reason: str, worktree: Path, branch: str) -> None:
    print(f"\nRED  {reason}")
    print(f"no branch for you. inspect the attempt: {worktree}")
    print(f"clean up: git worktree remove --force {worktree} && git branch -D {branch}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="one markdown spec in, a verified branch out")
    parser.add_argument("spec", help="path to the task spec markdown file")
    parser.add_argument("--repo", default=".", help="target git repo (default: cwd)")
    parser.add_argument("--check", action="store_true",
                        help="parse the spec, print what was understood, dispatch nothing")
    args = parser.parse_args()

    try:
        spec = parse_spec(Path(args.spec).resolve())
    except SpecError as err:
        sys.exit(f"spec error: {err}")
    if args.check:
        for key in KNOWN_KEYS:
            value = spec.get(key)
            if value not in (None, "", []):
                print(f"{key}: {', '.join(value) if isinstance(value, list) else value}")
        if re.search(r"\[[a-z][^\]]*\]", spec["raw"]):
            print("note: this spec still has [brackets]; fill them before a real dispatch")
        print("spec parses. drop --check to dispatch it.")
        return
    repo = Path(git(Path(args.repo).resolve(), "rev-parse", "--show-toplevel"))
    slug = re.sub(r"[^a-z0-9-]+", "-", spec["path"].stem.lower()).strip("-") or "task"
    worktree, branch, run_id = make_worktree(repo, slug)
    deadline = time.time() + spec["budget"] * 60
    print(f"dispatching {spec['agent']} on {spec['path'].name} (budget {spec['budget']:.0f}m, "
          f"{spec['retries']} attempts)\nworktree {worktree}")

    feedback = ""
    reason = "all attempts exhausted"
    for attempt in range(1, spec["retries"] + 1):
        remaining = deadline - time.time()
        if remaining <= 0:
            bounce(f"budget exceeded ({spec['budget']:.0f} minutes)", worktree, branch)
        print(f"\nattempt {attempt}/{spec['retries']}: {spec['agent']} working...")
        try:
            agent = run_agent(spec, worktree, build_prompt(spec, attempt, feedback), remaining)
        except subprocess.TimeoutExpired:
            bounce(f"budget exceeded ({spec['budget']:.0f} minutes)", worktree, branch)
        log(repo, run_id, attempt, "agent", (agent.stdout or "") + "\n" + (agent.stderr or ""))
        if agent.returncode != 0:
            reason = f"agent exited {agent.returncode}"
            feedback = (agent.stderr or agent.stdout or "")[-2000:]
            continue
        bad = violations(changed_paths(worktree), spec["allowed"], spec["forbidden"])
        if bad:
            reason = bad[0]
            feedback = "\n".join(bad)
            print(f"  path violation, reverting: {bad[0]}")
            git(worktree, "reset", "--hard")
            git(worktree, "clean", "-fd")
            continue
        code, output = run_verify(spec["verify"], worktree)
        log(repo, run_id, attempt, "verify", output)
        if code == 0:
            git(worktree, "add", "-A")
            git(worktree, "commit", "-m", f"ngnm: {spec['goal'].splitlines()[0][:60]}")
            print(f"\nGREEN  verify exited 0: {spec['verify']}")
            print(f"branch: {branch}")
            print(f"review the diff, then merge it yourself: git merge {branch}")
            sys.exit(0)
        reason = f"verify exited {code}"
        feedback = f"$ {spec['verify']}\n{output}"
        print(f"  verify exited {code}, retrying with the evidence")

    bounce(reason, worktree, branch)


if __name__ == "__main__":
    main()
