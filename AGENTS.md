# AGENTS.md

This repo is a small tool: `loop.py` runs a plan, build, check, review loop
over the stories of a task, with any agent CLI. README.md explains how it is
used. Keep README.md in line with `loop.py` when a command or flag changes.

- `loop.py` is one file, Python standard library only. Keep it that way.
- `steps/*.md` are prompts for agents. Keep them short, tool-neutral, and in
  plain words. No vendor-specific tool names.
- `steps/plan-*.md` run with the human in the session. The other steps run
  without one.
- `profiles/*.json` pick the steps and the skills per task type.
- State goes in the target project under `.loop/<task>/`, never in this repo.
- After changing `loop.py`, run `tests/smoke.sh`. It runs the loop end to end
  with `tests/fake-agent.sh` in a throwaway project. Add a case for new behaviour.
- Ask before running the loop with a real agent.
