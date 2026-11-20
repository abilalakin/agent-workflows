# agent-workflows

A loop for building things with coding agents. Work in progress.

1. **You plan** the work with an agent: what to build, how, and in which stories.
2. **The loop builds** the stories one by one. Each story is built, checked,
   reviewed and delivered before the next one starts.

The script does the mechanics: order, counting, checks, gates. Markdown files
hold everything that needs judgment: how to plan, build, review and deliver.
It works with any agent CLI, and all state is in plain files in your project.

**Using an agent?** Tell it: "Read AGENTS.md in agent-workflows and set up a
task for X." It can run every command below for you.

## Setup

`loop.py` is one Python file with no dependencies. Run it from the root of the
project you are working on.

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
| `--check` | A command that must succeed after every build. Repeat it for more. |
| `--context` | A file every agent should read, such as a spec. Repeat it for more. |
| `--model` | Which model to use where. See "Models". |
| `--deliver` | How finished stories are handed over. See "Delivery". |

## 2. Plan

```sh
loop plan csv-export                              # lists the plan stages
claude "$(loop plan csv-export plan-interview)"   # runs one stage in a chat
```

A feature has four stages: interview, PRD, architecture, stories. The last
stage adds the stories. To let the loop open the chat for you, with the
planning model, set `LOOP_PLAN_AGENT` once and add `--start`:

```sh
export LOOP_PLAN_AGENT="claude --model {model} {prompt}"
loop plan csv-export plan-interview --start
```
 You can also add them yourself:

```sh
loop add csv-export "Export button" -c "Button shows on the reports page"
loop add csv-export "Export button" --criteria-file criteria.txt
loop add csv-export --from stories.md     # a heading per story, a bullet per criterion
```

## 3. Approve

```sh
loop status csv-export
loop approve csv-export
```

Nothing is built before you approve.

## 4. Run the loop

```sh
export LOOP_AGENT="claude -p"     # any command that reads a prompt and runs without a chat
loop run csv-export
```

For each story:

1. A fresh agent builds it.
2. The loop runs your checks.
3. Fresh agents review the change.
4. On a pass, the story is delivered and the next one starts.
5. On a fail, a new agent gets the findings and tries again. After two failed
   attempts the story is blocked and the loop stops.

## Delivery

| Setting | What happens when a story passes |
|---|---|
| default | The loop commits it on the branch `loop/<task>`. Add `--push` to push. |
| `--deliver deliver-pr` | A fresh agent follows `steps/deliver-pr.md`: a branch and a PR per story, each on top of the story before. |

After a deliver step, another fresh agent reviews the delivery with
`steps/review-delivery.md`: the branch, its base, the commit, and the PR. A
failed review sends the findings back to a new delivery agent. If it fails
again, the loop stops.

Delivery rules differ per project, so they live in step files. To use your
own, copy both files to `.loop/steps/` in your project and edit them.

Files that were already changed when the task first ran stay out of the
commits. The loop never merges.

## Models

Put `{model}` in the agent command, then say which model goes where:

```sh
export LOOP_AGENT="claude -p --model {model}"
loop init csv-export --model sonnet --model plan=fable --model build=opus --model review=opus
loop add csv-export "Tricky parser" -c "Handles quoted commas" --model fable
```

A model can be the default, or belong to a phase (`plan`, `build`, `review`,
`deliver`), to one step (`review-simplicity=haiku`), or to one story. The most
specific one wins.

## See the progress

Everything is in your project under `.loop/<task>/`:

| File | What it is |
|---|---|
| `BOARD.md` | The stories and their status. |
| `progress.md` | A log, plus lessons and follow-ups from the agents. |
| `notes.md`, `prd.md`, `architecture.md` | The plan. |
| `reviews/` | Why a story passed or failed. |
| `logs/` | What each agent was told and what it answered. |
| `task.json` | The data behind the board, and the task's settings. |

Other commands: `loop status` shows all boards, `loop check <task>` runs the
checks, `loop run <task> --story S2` runs one story, and
`loop set <task> S2 todo` resets a story.

## Make it yours

- **Steps** are markdown prompts in `steps/`. A file at `.loop/steps/<name>.md`
  in your project replaces the one from this repo.
- **Profiles** in `profiles/` say which plan stages, reviews and skills a type
  of work gets.
- **Skills** are names in a list. An agent loads the ones it has and skips the
  rest. The defaults come from Addy Osmani's agent-skills and superpowers.

`LOOP.md` describes the process. `docs/lessons.md` says why it is built this way.
