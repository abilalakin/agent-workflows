# agent-workflows

A personal sandbox for learning how to run several Claude agents together and keep them in sync.

## Goal

Try a few multi-agent patterns on small, safe projects. Keep the ones that work, so I can use them later on bigger projects.

## The app the agents work on

`apps/todo-cli` is a tiny to-do CLI written twice, in Python and in TypeScript. Both read and write the same JSON file. `apps/todo-cli/SPEC.md` lists six small stories. Story 1 is done as a template. The rest are left for the agents.

## What to try

1. **Scripted workflows** (`experiments/01-review-workflow`)
   - Use the `Workflow` tool to run agents in a fixed order with `agent()`, `pipeline()` and `parallel()`.
   - Start with a read-only job: one agent finds issues in the app, others try to prove them wrong.
   - Keep each run under 10 agents.

2. **A Ralph loop built as a workflow** (`experiments/02-ralph-workflow`)
   - A `prd.json` with a few small stories, plus a `progress.txt` for notes.
   - Each loop step is a fresh agent that does one story and runs the checks.
   - A second agent reviews each story against its acceptance criteria.
   - Stop when every story passes, or after a set number of steps.
   - Compare it with the plain bash Ralph loop.

3. **Sessions that message each other** (`experiments/03-sessions`)
   - Two or more Claude Code sessions, each with its own folder or branch.
   - They talk with `SendMessage` and find each other with `ListAgents`.
   - Try a lead session that splits the work and teammates that report back.
   - Compare agent teams with plain cross-session messages.

## How to work here

Rules for agents and humans are in `AGENTS.md`. Each experiment ends with a `NOTES.md`. I commit myself.
