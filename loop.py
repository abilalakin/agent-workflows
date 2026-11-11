#!/usr/bin/env python3
"""loop.py: a build, check, review loop over the stories of a task.

Works with any agent CLI. State lives in the project you run it from, under
.loop/<task>/. See LOOP.md for the process and README.md for the commands.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path(__file__).resolve().parent
STATUSES = ["todo", "building", "reviewing", "done", "blocked"]
PLAN_DOCS = ["prd.md", "architecture.md"]


def die(msg):
    sys.exit(f"loop: {msg}")


def tdir(name):
    return Path(".loop") / name


def load(name):
    path = tdir(name) / "task.json"
    if not path.exists():
        die(f"no task '{name}' here. Run: loop.py init {name}")
    return json.loads(path.read_text())


def save(name, task):
    (tdir(name) / "task.json").write_text(json.dumps(task, indent=2) + "\n")
    (tdir(name) / "BOARD.md").write_text(board(name, task))


def board(name, task):
    stories = task["stories"]
    done = sum(s["status"] == "done" for s in stories)
    lines = [
        f"# {name}",
        "",
        task.get("description", ""),
        "",
        f"**{done} of {len(stories)} done.** Updated {now()}.",
        "",
        "Plan: " + ", ".join(f"{d} {'yes' if (tdir(name) / d).exists() else 'no'}" for d in PLAN_DOCS)
        + f", approved {'yes' if task.get('approved') else 'no'}.",
        "",
        "| ID | Story | Status | Attempts | Notes |",
        "|---|---|---|---|---|",
    ]
    for s in stories:
        notes = s.get("notes", "").replace("|", "/").replace("\n", " ")
        lines.append(f"| {s['id']} | {s['title']} | {s['status']} | {s['attempts']} | {notes} |")
    return "\n".join(lines) + "\n"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def log(name, text):
    with open(tdir(name) / "progress.md", "a") as f:
        f.write(f"- {now()} {text}\n")
    print(text, flush=True)


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def git_ok(name, *args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode != 0:
        log(name, f"git {' '.join(args[:2])} failed: {(r.stderr or r.stdout).strip().splitlines()[-1:]}")
    return r.returncode == 0


def step_text(step):
    for base in (Path(".loop") / "steps", HOME / "steps"):
        path = base / f"{step}.md"
        if path.exists():
            return path.read_text().strip()
    die(f"no step file '{step}.md' in .loop/steps or {HOME / 'steps'}")


def review_path(name, story, step):
    return tdir(name) / "reviews" / f"{story['id']}-a{story['attempts']}-{step}.md"


def make_prompt(name, task, step, story=None, kind="build", feedback=""):
    d = tdir(name)
    ctx = [f"- Task: {name}. {task.get('description', '')}", f"- Task folder: `{d}`"]
    for doc in PLAN_DOCS:
        if (d / doc).exists():
            ctx.append(f"- Read the plan: `{d / doc}`")
    if kind == "plan":
        ctx.append(f"- Write plan documents into the task folder: {', '.join(PLAN_DOCS)}")
        ctx.append(f'- Add a story with: `{Path(__file__).resolve()} add {name} "title" -c "criterion" -c "criterion"`')
    if story:
        ctx += [
            f"- Story {story['id']}: {story['title']}",
            "- Acceptance criteria:",
            *[f"  - {c}" for c in story["criteria"]],
            f"- Attempt {story['attempts']} of {task['maxAttempts']}",
        ]
        if story.get("base"):
            ctx.append(f"- See the change for this story: `git diff {story['base']}` and `git status --short` for new files.")
    if kind != "plan":
        ctx.append(f"- Check command: `{task['check']}`" if task.get("check") else "- No check command is set.")
    ctx.append(f"- Progress log: `{d / 'progress.md'}`")
    if kind == "review":
        ctx.append(f"- Write your review to: `{review_path(name, story, step)}`")
    skills = task.get("skills", {}).get(step, [])
    if skills:
        ctx.append(f"- Skills: if your agent has any of these, load and follow them: {', '.join(skills)}. Skip the ones you do not have.")
    if feedback:
        ctx.append(f"- The last attempt was rejected. Fix this first:\n{feedback}")
    return f"{step_text(step)}\n\n## Context\n\n" + "\n".join(ctx) + "\n"


def run_agent(cmd, prompt, name, story, step):
    logs = tdir(name) / "logs"
    logs.mkdir(exist_ok=True)
    stem = f"{story['id']}-a{story['attempts']}-{step}"
    prompt_file = logs / f"{stem}.prompt.md"
    prompt_file.write_text(prompt)
    with open(logs / f"{stem}.log", "w") as out:
        if "{prompt_file}" in cmd:
            r = subprocess.run(cmd.replace("{prompt_file}", str(prompt_file)), shell=True, stdout=out, stderr=out)
        else:
            r = subprocess.run(cmd, shell=True, input=prompt, text=True, stdout=out, stderr=out)
    return r.returncode


def run_check(name, task, story):
    if not task.get("check"):
        return True, ""
    r = subprocess.run(task["check"], shell=True, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    (tdir(name) / "logs" / f"{story['id']}-a{story['attempts']}-check.log").write_text(out + "\n")
    return r.returncode == 0, "\n".join(out.splitlines()[-30:])


def verdict(path):
    if not path.exists():
        return False
    for line in path.read_text().splitlines():
        if line.strip().upper().startswith("VERDICT:"):
            return "PASS" in line.upper()
    return False


def attempt(name, task, story, cmd, feedback):
    """One build, check, review round. Returns '' on success, else feedback."""
    story["attempts"] += 1
    story["status"] = "building"
    story.setdefault("base", git("stash", "create") or git("rev-parse", "HEAD"))
    save(name, task)
    log(name, f"{story['id']} attempt {story['attempts']}: build")
    run_agent(cmd, make_prompt(name, task, task["build"], story, "build", feedback), name, story, task["build"])

    ok, tail = run_check(name, task, story)
    if not ok:
        log(name, f"{story['id']} attempt {story['attempts']}: check failed")
        return f"`{task['check']}` failed. Last lines:\n```\n{tail}\n```"

    story["status"] = "reviewing"
    save(name, task)
    (tdir(name) / "reviews").mkdir(exist_ok=True)
    failed = []
    for review in task["reviews"]:
        step = review["step"]
        run_agent(cmd, make_prompt(name, task, step, story, "review"), name, story, step)
        passed = verdict(review_path(name, story, step))
        log(name, f"{story['id']} attempt {story['attempts']}: {step} {'pass' if passed else 'fail'}")
        if not passed and review.get("blocking", True):
            failed.append(f"  - Read `{review_path(name, story, step)}` and fix every blocking finding.")
    return "\n".join(failed)


def cmd_init(a):
    d = tdir(a.task)
    if (d / "task.json").exists():
        die(f"task '{a.task}' already exists")
    profile = HOME / "profiles" / f"{a.profile}.json"
    if not profile.exists():
        die(f"no profile '{a.profile}'. Have: {', '.join(p.stem for p in (HOME / 'profiles').glob('*.json'))}")
    d.mkdir(parents=True)
    task = {
        "description": a.description,
        "check": a.check,
        "agent": "",
        "approved": False,
        "branch": f"loop/{a.task}",
        **json.loads(profile.read_text()),
        "stories": [],
    }
    if a.push:
        task["push"] = True
    (d / ".gitignore").write_text("logs/\n")
    (d / "progress.md").write_text(f"# Progress: {a.task}\n\n## Lessons\n\n## Follow-ups\n\n## Log\n\n")
    save(a.task, task)
    print(f"created {d}. Next: loop.py plan {a.task}")


def cmd_add(a):
    task = load(a.task)
    sid = f"S{len(task['stories']) + 1}"
    task["stories"].append({"id": sid, "title": a.title, "criteria": a.criterion, "status": "todo", "attempts": 0, "notes": ""})
    save(a.task, task)
    print(f"added {sid}: {a.title}")


def cmd_status(a):
    names = [a.task] if a.task else sorted(p.parent.name for p in Path(".loop").glob("*/task.json"))
    if not names:
        die("no tasks here. Run: loop.py init <task>")
    for name in names:
        task = load(name)
        save(name, task)
        print(board(name, task))


def next_story(task, story_id=None):
    for s in task["stories"]:
        if story_id and s["id"] == story_id:
            return s
        if not story_id and s["status"] != "done":
            return s
    return None


def cmd_set(a):
    task = load(a.task)
    story = next_story(task, a.story) or die(f"no story {a.story}")
    story["status"] = a.status
    if a.status == "todo":
        story["attempts"] = 0
    if a.note:
        story["notes"] = a.note
    save(a.task, task)
    log(a.task, f"{story['id']} set to {a.status} by hand")


def cmd_prompt(a):
    task = load(a.task)
    story = next_story(task, a.story) or die("no open story")
    step = a.step or task["build"]
    print(make_prompt(a.task, task, step, story, "build" if step == task["build"] else "review"))


def cmd_plan(a):
    task = load(a.task)
    stages = task.get("plan", [])
    if a.stage:
        if a.stage not in stages:
            die(f"no plan stage '{a.stage}'. Have: {', '.join(stages)}")
        print(make_prompt(a.task, task, a.stage, kind="plan"))
        return
    d = tdir(a.task)
    print(f"Plan stages for {a.task}. Run each one in an interactive agent session, in order:")
    for st in stages:
        print(f"  loop.py plan {a.task} {st}")
    print("Have: " + ", ".join(f"{doc} {'yes' if (d / doc).exists() else 'no'}" for doc in PLAN_DOCS)
          + f", {len(task['stories'])} stories, approved {'yes' if task.get('approved') else 'no'}.")
    print(f"When the plan is right: loop.py approve {a.task}")


def cmd_approve(a):
    task = load(a.task)
    if not task["stories"]:
        die("no stories yet. Plan first, or add stories with: loop.py add")
    task["approved"] = True
    save(a.task, task)
    log(a.task, f"plan approved with {len(task['stories'])} stories")


def cmd_run(a):
    task = load(a.task)
    cmd = a.agent or os.environ.get("LOOP_AGENT") or task.get("agent")
    if not cmd:
        die('no agent command. Set LOOP_AGENT, for example: LOOP_AGENT="claude -p" or "codex exec -"')
    if not task.get("approved"):
        die(f"the plan is not approved. Review .loop/{a.task}/BOARD.md, then: loop.py approve {a.task}")
    if task.get("commit") and task.get("branch") and git("rev-parse", "--abbrev-ref", "HEAD") != task["branch"]:
        exists = git("rev-parse", "--verify", "--quiet", f"refs/heads/{task['branch']}")
        if not git_ok(a.task, "switch", *([] if exists else ["-c"]), task["branch"]):
            die(f"cannot switch to branch {task['branch']}")
    rounds = 0
    while True:
        story = next_story(task, a.story)
        if not story or story["status"] == "done":
            print("all stories done" if not story else f"{story['id']} is already done")
            break
        feedback = ""
        while story["attempts"] < task["maxAttempts"]:
            if a.max_rounds and rounds >= a.max_rounds:
                story["status"] = "todo"
                save(a.task, task)
                log(a.task, f"stopped after {rounds} rounds")
                return
            rounds += 1
            feedback = attempt(a.task, task, story, cmd, feedback)
            if not feedback:
                story["status"] = "done"
                story["notes"] = f"passed on attempt {story['attempts']}"
                break
        if story["status"] != "done":
            story["status"] = "blocked"
            story["notes"] = f"rejected {story['attempts']} times, see reviews/ and logs/"
            save(a.task, task)
            log(a.task, f"{story['id']} blocked. Stopping. Fix it, then: loop.py set {a.task} {story['id']} todo")
            sys.exit(1)
        save(a.task, task)
        log(a.task, f"{story['id']} done")
        if task.get("commit"):
            msg = f"{task.get('commitType', 'feat')}({a.task}): {story['title']} ({story['id']})"
            if git_ok(a.task, "add", "-A") and git_ok(a.task, "commit", "-m", msg) and task.get("push"):
                if git_ok(a.task, "push", "-u", "origin", "HEAD"):
                    print(f"{story['id']} pushed", flush=True)
        if a.story:
            break


def main():
    p = argparse.ArgumentParser(prog="loop.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create a task in .loop/<task>")
    s.add_argument("task")
    s.add_argument("--profile", default="feature")
    s.add_argument("--check", default="", help="command that must exit 0 after each build")
    s.add_argument("--description", default="")
    s.add_argument("--push", action="store_true", help="push the task branch after each passed story")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("plan", help="list the plan stages, or print the prompt for one")
    s.add_argument("task")
    s.add_argument("stage", nargs="?")
    s.set_defaults(fn=cmd_plan)

    s = sub.add_parser("approve", help="approve the plan so the loop may run")
    s.add_argument("task")
    s.set_defaults(fn=cmd_approve)

    s = sub.add_parser("add", help="add a story")
    s.add_argument("task")
    s.add_argument("title")
    s.add_argument("-c", "--criterion", action="append", default=[], help="acceptance criterion, repeatable")
    s.set_defaults(fn=cmd_add)

    s = sub.add_parser("status", help="print the board and rewrite BOARD.md")
    s.add_argument("task", nargs="?")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("run", help="run the loop with an agent command")
    s.add_argument("task")
    s.add_argument("--agent", help="agent command. Prompt goes to stdin, or to {prompt_file} if the command has it")
    s.add_argument("--story", help="run only this story")
    s.add_argument("--max-rounds", type=int, default=0, help="stop after this many build rounds")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("prompt", help="print the prompt for a step, to paste into any agent")
    s.add_argument("task")
    s.add_argument("step", nargs="?")
    s.add_argument("--story")
    s.set_defaults(fn=cmd_prompt)

    s = sub.add_parser("set", help="set a story's status by hand")
    s.add_argument("task")
    s.add_argument("story")
    s.add_argument("status", choices=STATUSES)
    s.add_argument("--note", default="")
    s.set_defaults(fn=cmd_set)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
