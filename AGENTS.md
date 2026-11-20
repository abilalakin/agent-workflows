# AGENTS.md

`loop.py` runs a plan, build, check, review, deliver loop over the stories of a
task. README.md lists the commands. LOOP.md describes the process.

## If someone asks you to use this tool

You are the operator. The loop does the building.

1. Work from the root of their project, not from this repo. Call `loop.py` by
   its full path.
2. Create the task with `init`. Ask them for the checks if you cannot find the
   project's test and lint commands.
3. Plan with them. Follow each plan stage from `loop.py plan <task>` in this
   chat. Add the stories with `add`.
4. Show them the board and wait. Only they approve. Never run `approve`
   yourself.
5. Start `loop.py run <task>` with the agent command they give you. Watch it.
   When it stops, read the board and the review files, and tell them what
   happened in plain words.
6. When a story is blocked, show them why. Reset it only when they say so.

## If you are changing this tool

- **Script for mechanics, markdown for judgment.** `loop.py` does what must
  happen the same way every time: order, counting, checks, gates. Anything
  that needs reading or differs per project goes into a step file.
- `loop.py` is one file, Python standard library only.
- `steps/*.md` are prompts. Keep them short, plain, and free of vendor-specific
  tool names. `plan-*` steps run with the human. The others run without one.
- `profiles/*.json` pick the steps and skills per type of work.
- State goes in the target project under `.loop/<task>/`, never in this repo.
- The agent command comes from the user, never from a file in the project.
- After a change, run `tests/smoke.sh` and add a case for new behaviour.
- Keep README.md and LOOP.md in line with the script.
- Ask before running the loop with a real agent.
