# agent-workflows

A small workflow for building things with coding agents. Work in progress.

1. **You plan** the work with an agent: what to build, how, and in which steps.
2. **Agents build** it one story at a time. Each story is built, checked,
   reviewed and committed before the next one starts.

It works with any agent that runs from the command line. All state is in plain
files inside your project, so you can read the progress at any time.

## Setup

`loop.py` is one Python file with no dependencies. Make an alias for it, and
run it from the root of the project you are working on:

```sh
alias loop=~/path/to/agent-workflows/loop.py
```

## 1. Create a task

```sh
loop init csv-export --profile feature --check "pytest" --description "Export reports as CSV"
```

| Part | Meaning |
|---|---|
| `csv-export` | A name you make up, with no spaces. |
| `--profile` | The type of work: `feature`, `bugfix` or `quick`. |
| `--check` | A command that must succeed after every build. Repeat it for more checks. |
| `--context` | A file every agent should read, such as a spec. Repeat it for more files. |
| `--description` | One line about the task. |
| `--model` | Which model to use. See "Models" below. |
| `--pr` | Give each story its own branch and PR. See "Git" below. |

Checks run in order and all must pass. A typical set:

```sh
loop init csv-export --check "ruff check ." --check "mypy src" --check "pytest" --context docs/spec.md
```

## 2. Plan

```sh
loop plan csv-export                              # lists the plan stages
claude "$(loop plan csv-export plan-interview)"   # runs one stage with an agent
```

A feature has four stages: interview, PRD, architecture, stories. Run each in
a chat session with your agent. To let the loop start the chat for you, set
`LOOP_PLAN_AGENT` and add `--start`:

```sh
export LOOP_PLAN_AGENT="claude --model {model} {prompt}"
loop plan csv-export plan-interview --start
```
 The last stage adds the stories. You can also
add them yourself:

```sh
loop add csv-export "Export button" -c "Button shows on the reports page"
loop add csv-export "Export button" --criteria-file criteria.txt
loop add csv-export --from stories.md
```

- `-c` is one acceptance criterion. Repeat it for more.
- `--criteria-file` reads one criterion per line.
- `--from` reads many stories from one markdown file. Each heading is a story
  and each bullet under it is a criterion.

## 3. Approve

```sh
loop status csv-export
loop approve csv-export
```

Nothing is built before you approve.

## 4. Build

```sh
export LOOP_AGENT="claude -p"
loop run csv-export
```

`LOOP_AGENT` is the command that starts your agent without a chat window. For
each story the loop does this:

1. A fresh agent builds the story.
2. The loop runs your checks.
3. Fresh agents review the change.
4. On a pass, the story is committed.
5. On a fail, a new agent gets the findings and tries again. After two failed
   attempts the story is blocked and the loop stops.

## Git

The loop has two ways to hand over the work. Pick one at `init`.

| Mode | What you get |
|---|---|
| default | One branch, `loop/<task>`, with one commit per story. Add `--push` to push it. |
| `--pr` | One branch and one PR per story. Each branch starts from the story before it, and its PR targets that branch. |

In `--pr` mode the first story starts from the branch you are on when you run
the loop. PRs are opened with `gh pr create`. To use another tool, set
`prCommand` in `task.json`. It can use `{base}`, `{branch}`, `{title}` and
`{body_file}`.

Files that were already changed or untracked when the task first ran stay out
of the loop's commits. The loop never merges anything.

## Models

Put `{model}` in the agent command, then say which model to use where:

```sh
export LOOP_AGENT="claude -p --model {model}"
loop init csv-export --model sonnet --model plan=fable --model build=opus --model review=opus
loop add csv-export "Tricky parser" -c "Handles quoted commas" --model fable
```

| You write | It applies to |
|---|---|
| `--model sonnet` | Everything, unless something below says otherwise. |
| `--model plan=fable` | A whole phase: `plan`, `build` or `review`. |
| `--model review-quality=haiku` | One step, by its file name in `steps/`. |
| `--model` on `loop add` | Every step of that one story. |

The most specific one wins: story, then step, then phase, then the default.
The loop only passes the name along, so use the names your agent knows.

## See the progress

Everything is in your project under `.loop/<task>/`:

| File | What it is |
|---|---|
| `BOARD.md` | The stories and their status. |
| `progress.md` | A log of what happened, plus lessons and follow-ups from the agents. |
| `notes.md`, `prd.md`, `architecture.md` | The plan. |
| `reviews/` | Why a story passed or failed. |
| `logs/` | What each agent was told and what it answered. |
| `task.json` | The data behind all of it, and the task's settings. |

## Other commands

| Command | What it does |
|---|---|
| `loop status` | Prints the boards of all tasks. |
| `loop check <task>` | Runs the checks now. |
| `loop run <task> --story S2` | Runs one story. |
| `loop prompt <task> [step]` | Prints a prompt to paste into an agent. |
| `loop set <task> <story> todo` | Resets a story so it runs again. |

## Make it yours

- **Steps** are markdown prompts in `steps/`. Edit them or add your own. A file
  at `.loop/steps/<name>.md` in a project replaces the one from this repo.
- **Profiles** in `profiles/` say which plan stages and reviews a type of work
  gets, and which skills each step should load.
- **Skills** are only names in a list. An agent loads the ones it has and skips
  the rest. The defaults come from Addy Osmani's agent-skills and superpowers.
- **One task** can differ from its profile. Edit `task.json` in the task folder.
  The agent command is never read from there, only from `LOOP_AGENT` or `--agent`.

`LOOP.md` describes the process in full. `docs/lessons.md` says why the steps
are written the way they are.
