# AGENTS.md

This repo is a small tool: `loop.py` runs a build, check, review loop over the
stories of a task, with any agent CLI. README.md explains how it is used.

- `loop.py` is one file, Python standard library only. Keep it that way.
- `steps/*.md` are prompts for agents. Keep them short, tool-neutral, and in
  plain words. No vendor-specific tool names.
- `steps/plan-*.md` run with the human in the session. The other steps run
  without one.
- `profiles/*.json` pick the steps and the skills per task type.
- State goes in the target project under `.loop/<task>/`, never in this repo.
- After changing `loop.py`, run it end to end against a throwaway project with
  a fake agent command before calling it done.
- Ask before running the loop with a real agent.
