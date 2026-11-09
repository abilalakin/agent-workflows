# AGENTS.md

Guide for any agent working in this repo. Humans: read README.md first.

## What this repo is

A sandbox for multi-agent experiments. The agents work on one small app,
`apps/todo-cli`, which exists in two languages that share a JSON file. Nothing
here is production code.

## Layout

- `apps/todo-cli/` is the baseline app. `SPEC.md` holds the data format and the
  stories. Do not change the baseline during an experiment.
- `experiments/NN-name/` holds one experiment each. An experiment that edits the
  app works on its own copy at `experiments/NN-name/app/`.
- `experiments/NN-name/NOTES.md` records the outcome. Four short sections: what
  we tried, what happened, rough cost, use again or not.

## Checks

From the app folder, `./check.sh` is the gate: Python tests, TypeScript
typecheck and tests, then the cross-language compat check. A story is done when
`check.sh` passes with new tests for that story in both languages.

## Rules

- A change to the JSON format lands in both languages and in `SPEC.md` in the
  same story. Old files must still load.
- Add a story's tests before its code.
- Ask before starting a workflow or any agent session the human will not watch.
- The human commits. Report changed files and suggest a Conventional Commits
  message instead.
