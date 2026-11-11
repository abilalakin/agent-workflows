# agent-workflows

A small workflow for getting work done with coding agents. I make the plan with
an agent. Then agents build it one story at a time: build, check, review,
commit, repeat. It works with any agent CLI and
keeps all state in plain files, so I can track progress and change the steps.

Use it for a long feature with many stories, a short task, or a single bugfix.

## How it works

There are two phases. `LOOP.md` describes both in full.

**Plan, with me in the loop.** I run the plan stages in an interactive agent
session: interview, PRD, architecture, then stories. The agent asks, drafts and
pushes back. I decide. The result is a few short documents and a list of
stories with acceptance criteria. Nothing gets built until I approve the plan.

**Implement, by agents.** For each story the loop does this:

1. **Build.** A fresh agent gets one step file plus the story.
2. **Check.** The loop runs the project's check command itself.
3. **Review.** One fresh agent per review step writes a review file that starts
   with `VERDICT: pass` or `VERDICT: fail`.
4. **Record.** Pass marks the story done and commits it on the task branch.
   Fail sends the findings to a new builder. After `maxAttempts` the story is
   blocked and the loop stops.

## Use it

Run these from the root of the project you are working on.

```sh
loop=~/path/to/agent-workflows/loop.py

# 1. Plan
$loop init login --profile feature --check "npm test" --description "Add login"
$loop plan login                           # lists the plan stages
claude "$($loop plan login plan-interview)" # run each stage in an interactive session
$loop status login                         # read the board
$loop approve login

# 2. Implement
export LOOP_AGENT="claude -p"              # or "codex exec -", or any command that reads a prompt on stdin
$loop run login
```

If the agent wants a file instead of stdin, put `{prompt_file}` in the command.

Other commands:

- `add <task> "title" -c "criterion"` adds a story by hand.
- `run <task> --story S2` runs one story. `--max-rounds 3` stops early.
- `prompt <task> [step]` prints the prompt for the next story, to paste into an agent.
- `set <task> <story> <status>` changes a status by hand. Setting `todo` resets the attempts.

## Git

The loop works on a branch named `loop/<task>` and makes one commit per passed
story. It does not push unless the task says so: pass `--push` to `init`, or
set `push` to true in `task.json`. Set `commit` to false to leave git alone.

## What gets written

Everything lives in the project, under `.loop/<task>/`:

| File | What it is |
|---|---|
| `notes.md`, `prd.md`, `architecture.md` | The plan documents. |
| `task.json` | Stories, statuses, and this task's settings. The source of truth. |
| `BOARD.md` | The board as a table, rewritten on every change. |
| `progress.md` | Lessons, follow-ups, and a log line per event. |
| `reviews/` | One review file per story, attempt and review step. |
| `logs/` | The prompt, agent output and check output of every step. |

## Change the steps and skills

- **Profiles** in `profiles/` pick the steps for a task type. `feature` has the
  full plan and three reviews. `bugfix` reproduces the bug first and runs one
  review. `quick` builds and checks with no review.
- **Steps** in `steps/` are plain markdown prompts. Edit them, or add a new
  one and list it in a profile or in a task's `task.json`.
- **Skills** are listed per step under `skills` in the profile. The prompt
  tells the agent to load the ones it has and skip the rest, so the same task
  runs on agents with different skill sets. The defaults name skills from
  Addy Osmani's agent-skills, superpowers, and a few others.
- **Per project:** a file at `.loop/steps/<name>.md` in the project wins over
  the one in this repo.
- **Per task:** edit `reviews`, `skills`, `maxAttempts`, `check` or `agent` in
  `task.json`.

`docs/lessons.md` explains why the steps are written the way they are.
