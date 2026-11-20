#!/usr/bin/env python3
"""loop.py: a build, check, review loop over the stories of a task.

Works with any agent CLI. State lives in the project you run it from, under
.loop/<task>/. See LOOP.md for the process and README.md for the commands.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path(__file__).resolve().parent
STATUSES = ["todo", "building", "reviewing", "done", "blocked"]
PLAN_DOCS = ["prd.md", "architecture.md"]


class AgentFailed(Exception):
    pass


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
        last = ((r.stderr or r.stdout).strip().splitlines() or [""])[-1]
        log(name, f"git {' '.join(args[:2])} failed: {re.sub(r'://[^/@ ]+@', '://***@', last)}")
    return r.returncode == 0


def dirty_paths():
    """Every file git sees as changed or untracked right now."""
    out = subprocess.run(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], capture_output=True, text=True).stdout
    entries, paths, i = out.split("\0"), set(), 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) > 3:
            paths.add(entry[3:])
            if entry[0] in "RC":
                i += 1  # a rename or copy lists the old path next
    return paths


def step_text(step):
    if not re.fullmatch(r"[a-z0-9-]+", step):
        die(f"bad step name '{step}'. Use lower case letters, digits and dashes.")
    for base in (Path(".loop") / "steps", HOME / "steps"):
        path = base / f"{step}.md"
        if path.exists():
            return path.read_text().strip()
    die(f"no step file '{step}.md' in .loop/steps or {HOME / 'steps'}")


def review_path(name, story, step):
    return tdir(name) / "reviews" / f"{story['id']}-a{story['attempts']}-{step}.md"


def make_prompt(name, task, step, story=None, kind="build", feedback="", extra=()):
    d = tdir(name)
    ctx = [f"- Task: {name}. {task.get('description', '')}", f"- Task folder: `{d}`"]
    for doc in PLAN_DOCS:
        if (d / doc).exists():
            ctx.append(f"- Read the plan: `{d / doc}`")
    for path in task.get("context", []):
        ctx.append(f"- Read this too: `{path}`")
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
        checks = task.get("checks", [])
        ctx.append("- Checks, all must exit 0: " + ", ".join(f"`{c}`" for c in checks) if checks else "- No checks are set.")
    ctx.append(f"- Progress log: `{d / 'progress.md'}`")
    if kind == "review":
        ctx.append(f"- Write your review to: `{review_path(name, story, step)}`")
    ctx += extra
    skills = task.get("skills", {}).get(step, [])
    if skills:
        ctx.append(f"- Skills: if your agent has any of these, load and follow them: {', '.join(skills)}. Skip the ones you do not have.")
    if feedback:
        ctx.append(f"- The last attempt was rejected. Fix this first:\n{feedback}")
    return f"{step_text(step)}\n\n## Context\n\n" + "\n".join(ctx) + "\n"


def model_for(task, step, kind, story=None):
    """Most specific wins: the story, then the step, then the phase, then the default."""
    models = task.get("models", {})
    return (story or {}).get("model") or models.get(step) or models.get(kind) or models.get("default", "")


def with_model(cmd, model):
    if "{model}" not in cmd:
        return cmd
    if not model:
        die("the agent command has {model} but no model is set. Add one: loop.py init --model NAME, or 'models' in task.json")
    return cmd.replace("{model}", shlex.quote(model))


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
    if r.returncode != 0:
        raise AgentFailed(f"the agent command exited with {r.returncode} in step {step}. See {logs / f'{stem}.log'}")


def run_checks(task, log_file=None):
    """Run each check in order. Returns '' when all pass, else feedback about the first failure."""
    output, feedback = [], ""
    for check in task.get("checks", []):
        r = subprocess.run(check, shell=True, capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip()
        output.append(f"$ {check}\n{out}\nexit {r.returncode}\n")
        if r.returncode != 0:
            tail = "\n".join(out.splitlines()[-30:])
            feedback = f"`{check}` failed. Last lines:\n```\n{tail}\n```"
            break
    if log_file:
        log_file.write_text("\n".join(output))
    return feedback


def verdict(path):
    if not path.exists():
        return False
    for line in path.read_text().splitlines():
        if line.strip().upper().startswith("VERDICT:"):
            return re.fullmatch(r"VERDICT:\s*PASS", line.strip().upper()) is not None
    return False


def attempt(name, task, story, cmd, feedback):
    """One build, check, review round. Returns '' on success, else feedback."""
    story["attempts"] += 1
    story["status"] = "building"
    story.setdefault("base", git("stash", "create") or git("rev-parse", "HEAD"))
    save(name, task)
    model = model_for(task, task["build"], "build", story)
    log(name, f"{story['id']} attempt {story['attempts']}: build" + (f" ({model})" if model else ""))
    run_agent(with_model(cmd, model), make_prompt(name, task, task["build"], story, "build", feedback), name, story, task["build"])

    failed_check = run_checks(task, tdir(name) / "logs" / f"{story['id']}-a{story['attempts']}-check.log")
    if failed_check:
        log(name, f"{story['id']} attempt {story['attempts']}: check failed")
        return failed_check

    story["status"] = "reviewing"
    save(name, task)
    (tdir(name) / "reviews").mkdir(exist_ok=True)
    failed = []
    for review in task["reviews"]:
        step = review["step"]
        review_path(name, story, step).unlink(missing_ok=True)
        run_agent(with_model(cmd, model_for(task, step, "review", story)), make_prompt(name, task, step, story, "review"), name, story, step)
        passed = verdict(review_path(name, story, step))
        log(name, f"{story['id']} attempt {story['attempts']}: {step} {'pass' if passed else 'fail'}")
        if not passed and review.get("blocking", True):
            failed.append(f"  - Read `{review_path(name, story, step)}` and fix every blocking finding.")
    return "\n".join(failed)


def deliver(name, task, story, cmd):
    """Hand over a passed story. Returns False when the delivery did not happen."""
    title = f"{task.get('commitType', 'feat')}({name}): {story['title']} ({story['id']})"
    step = task.get("deliver")
    if not step:
        # The built-in way: one commit on the task branch.
        if not task.get("commit"):
            return True
        if not git_ok(name, "add", "-A"):
            return False
        if task.get("leaveOut"):
            subprocess.run(["git", "reset", "-q", "--", *task["leaveOut"]], capture_output=True)
        if not git_ok(name, "commit", "-m", title):
            return False
        if task.get("push") and git_ok(name, "push", "-u", "origin", "HEAD"):
            print(f"{story['id']} pushed", flush=True)
        return True

    # The project's own way: a fresh agent follows the deliver step file,
    # and a second fresh agent reviews the branch, the commit and the PR.
    result = tdir(name) / "logs" / f"{story['id']}-delivered.txt"
    check = task.get("deliverReview", "review-delivery")
    extra = [
        f"- Title for the commit and the PR: `{title}`",
        f"- Reviews of this story: `{tdir(name) / 'reviews'}/{story['id']}-a{story['attempts']}-*.md`",
        f"- Delivery result file: `{result}`. One line: the PR link, or the branch name if there is no PR.",
    ]
    if task.get("leaveOut"):
        extra.append("- These files were changed before the task. They must stay uncommitted: " + ", ".join(f"`{p}`" for p in task["leaveOut"]))
    story["delivered"] = False
    save(name, task)
    before, feedback = git("rev-parse", "HEAD"), ""
    for _ in range(task["maxAttempts"]):
        run_agent(with_model(cmd, model_for(task, step, "deliver", story)),
                  make_prompt(name, task, step, story, "deliver", feedback, extra), name, story, step)
        if git("rev-parse", "HEAD") == before:
            log(name, f"{story['id']} not delivered: the deliver step made no commit")
            return False
        if not check:
            break
        review_path(name, story, check).unlink(missing_ok=True)
        run_agent(with_model(cmd, model_for(task, check, "review", story)),
                  make_prompt(name, task, check, story, "review", extra=extra), name, story, check)
        passed = verdict(review_path(name, story, check))
        log(name, f"{story['id']} {check} {'pass' if passed else 'fail'}")
        if passed:
            break
        feedback = f"  - Read `{review_path(name, story, check)}` and fix every blocking finding."
    else:
        return False
    story["delivered"] = True
    where = result.read_text().strip().splitlines()[0] if result.exists() and result.read_text().strip() else ""
    story["notes"] += f", delivered {where}".rstrip()
    save(name, task)
    log(name, f"{story['id']} delivered {where}".rstrip())
    return True


def parse_models(pairs):
    models = {}
    for pair in pairs:
        key, _, value = pair.rpartition("=")
        models[key or "default"] = value
    return models


def cmd_init(a):
    d = tdir(a.task)
    if (d / "task.json").exists():
        die(f"task '{a.task}' already exists")
    profile = HOME / "profiles" / f"{a.profile}.json"
    if not profile.exists():
        die(f"no profile '{a.profile}'. Have: {', '.join(p.stem for p in (HOME / 'profiles').glob('*.json'))}")
    for path in a.context:
        if not Path(path).exists():
            die(f"no such context file: {path}")
    d.mkdir(parents=True)
    task = {
        "description": a.description,
        "checks": a.check,
        "context": a.context,
        "approved": False,
        "branch": f"loop/{a.task}",
        **json.loads(profile.read_text()),
        "stories": [],
    }
    if a.push:
        task["push"] = True
    if a.deliver:
        step_text(a.deliver)
        task["deliver"] = a.deliver
    if a.model:
        task["models"] = parse_models(a.model)
    (d / ".gitignore").write_text("logs/\n")
    (d / "progress.md").write_text(f"# Progress: {a.task}\n\n## Lessons\n\n## Follow-ups\n\n## Log\n\n")
    save(a.task, task)
    print(f"created {d}. Next: loop.py plan {a.task}")


def read_bullets(path):
    """Lines of a file as criteria. Bullet marks and checkboxes are dropped."""
    out = []
    for line in Path(path).read_text().splitlines():
        line = line.strip().lstrip("-*").strip()
        for box in ("[ ]", "[x]", "[X]"):
            line = line.removeprefix(box).strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def read_stories(path):
    """A markdown file as stories: each heading is a title, each bullet under it a criterion."""
    stories = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line.startswith("#"):
            stories.append((line.lstrip("#").strip(), []))
        elif line[:1] in ("-", "*") and stories:
            text = line.lstrip("-*").strip()
            for box in ("[ ]", "[x]", "[X]"):
                text = text.removeprefix(box).strip()
            stories[-1][1].append(text)
    return [st for st in stories if st[1]]


def cmd_add(a):
    task = load(a.task)
    for path in filter(None, [a.criteria_file, a.from_file]):
        if not Path(path).exists():
            die(f"no such file: {path}")
    if a.from_file:
        new = read_stories(a.from_file)
        if not new:
            die(f"no stories in {a.from_file}. Use a heading per story and a bullet per criterion.")
    elif a.title:
        new = [(a.title, a.criterion + (read_bullets(a.criteria_file) if a.criteria_file else []))]
    else:
        die('give a title, or --from FILE. Example: loop.py add mytask "Title" -c "criterion"')
    for title, criteria in new:
        sid = f"S{len(task['stories']) + 1}"
        story = {"id": sid, "title": title, "criteria": criteria, "status": "todo", "attempts": 0, "notes": ""}
        if a.model:
            story["model"] = a.model
        task["stories"].append(story)
        print(f"added {sid}: {title} ({len(criteria)} criteria)")
    save(a.task, task)


def cmd_check(a):
    task = load(a.task)
    if not task.get("checks"):
        die("this task has no checks. Add them under 'checks' in task.json")
    feedback = run_checks(task)
    print(feedback or f"all {len(task['checks'])} checks pass")
    sys.exit(1 if feedback else 0)


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
        prompt = make_prompt(a.task, task, a.stage, kind="plan")
        if not a.start:
            print(prompt)
            return
        cmd = a.agent or os.environ.get("LOOP_PLAN_AGENT")
        if not cmd or "{prompt}" not in cmd:
            die('no chat command. Set LOOP_PLAN_AGENT with {prompt} in it, for example: LOOP_PLAN_AGENT="claude --model {model} {prompt}"')
        cmd = with_model(cmd, model_for(task, a.stage, "plan")).replace("{prompt}", shlex.quote(prompt))
        sys.exit(subprocess.run(cmd, shell=True).returncode)
    d = tdir(a.task)
    print(f"Plan stages for {a.task}. Run each one in an interactive agent session, in order:")
    for st in stages:
        print(f"  loop.py plan {a.task} {st}")
    print("Have: " + ", ".join(f"{doc} {'yes' if (d / doc).exists() else 'no'}" for doc in PLAN_DOCS)
          + f", {len(task['stories'])} stories, approved {'yes' if task.get('approved') else 'no'}.")
    if model_for(task, "", "plan"):
        print(f"Model for planning: {model_for(task, '', 'plan')}")
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
    cmd = a.agent or os.environ.get("LOOP_AGENT")
    if not cmd:
        die('no agent command. Set LOOP_AGENT, for example: LOOP_AGENT="claude -p" or "codex exec -"')
    if not task.get("approved"):
        die(f"the plan is not approved. Review .loop/{a.task}/BOARD.md, then: loop.py approve {a.task}")
    own_git = task.get("commit") and not task.get("deliver")
    if own_git and task.get("branch") and git("rev-parse", "--abbrev-ref", "HEAD") != task["branch"]:
        exists = git("rev-parse", "--verify", "--quiet", f"refs/heads/{task['branch']}")
        if not git_ok(a.task, "switch", *([] if exists else ["-c"]), task["branch"]):
            die(f"cannot switch to branch {task['branch']}")
    if (own_git or task.get("deliver")) and "leaveOut" not in task:
        # Files that were already changed before the first run are not the loop's to commit.
        task["leaveOut"] = sorted(p for p in dirty_paths() if not p.startswith(f".loop/{a.task}/"))
        save(a.task, task)
    if task.get("leaveOut"):
        print(f"{len(task['leaveOut'])} files were changed before this task started. The loop leaves them out of its commits.")
    print(f"agent: {cmd}")
    if "{model}" not in cmd and (task.get("models") or any(s.get("model") for s in task["stories"])):
        print("note: models are set, but the agent command has no {model} in it, so they are not used")
    for check in task.get("checks", []):
        print(f"check: {check}")
    for path in sorted((Path(".loop") / "steps").glob("*.md")):
        print(f"step override from this project: {path}")

    def hand_over(story):
        try:
            ok = deliver(a.task, task, story, cmd)
        except AgentFailed as e:
            ok = False
            print(e)
        if not ok:
            die(f"{story['id']} passed but was not delivered. Fix the problem and run again. The loop will retry the delivery.")

    for story in task["stories"]:
        if story["status"] == "done" and story.get("delivered") is False:
            hand_over(story)

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
            try:
                feedback = attempt(a.task, task, story, cmd, feedback)
            except AgentFailed as e:
                story["attempts"] -= 1
                story["status"] = "todo"
                save(a.task, task)
                die(f"{e}\nThe attempt was not counted. Fix the agent command and run again.")
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
        hand_over(story)
        if a.story:
            break


def main():
    p = argparse.ArgumentParser(prog="loop.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create a task in .loop/<task>")
    s.add_argument("task")
    s.add_argument("--profile", default="feature")
    s.add_argument("--check", action="append", default=[], help="command that must exit 0 after each build, repeatable")
    s.add_argument("--context", action="append", default=[], help="file every agent should read, repeatable")
    s.add_argument("--description", default="")
    s.add_argument("--push", action="store_true", help="push the task branch after each passed story")
    s.add_argument("--deliver", metavar="STEP", help="step file that hands over each passed story, for example deliver-pr")
    s.add_argument("--model", action="append", default=[], metavar="[WHERE=]NAME",
                   help="model for plan, build, review or one step, for example build=opus. No WHERE sets the default. Repeatable")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("plan", help="list the plan stages, or print the prompt for one")
    s.add_argument("task")
    s.add_argument("stage", nargs="?")
    s.add_argument("--start", action="store_true", help="start the chat agent with this stage's prompt")
    s.add_argument("--agent", help="chat command with {prompt} in it. Default: LOOP_PLAN_AGENT")
    s.set_defaults(fn=cmd_plan)

    s = sub.add_parser("approve", help="approve the plan so the loop may run")
    s.add_argument("task")
    s.set_defaults(fn=cmd_approve)

    s = sub.add_parser("add", help="add a story")
    s.add_argument("task")
    s.add_argument("title", nargs="?")
    s.add_argument("-c", "--criterion", action="append", default=[], help="acceptance criterion, repeatable")
    s.add_argument("--criteria-file", help="file with one criterion per line")
    s.add_argument("--model", help="model for this story. It wins over the task's models")
    s.add_argument("--from", dest="from_file", help="markdown file with many stories: a heading per story, a bullet per criterion")
    s.set_defaults(fn=cmd_add)

    s = sub.add_parser("check", help="run the task's checks now")
    s.add_argument("task")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("status", help="print the board and rewrite BOARD.md")
    s.add_argument("task", nargs="?")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("run", help="run the loop with an agent command")
    s.add_argument("task")
    s.add_argument("--agent", help="agent command. Prompt goes to stdin, or to {prompt_file}. {model} becomes the model name")
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
