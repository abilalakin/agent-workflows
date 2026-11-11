# The process

Two phases. The human leads the first. Agents run the second.

## Phase 1: plan, with the human

The human runs each plan stage in an interactive agent session. `loop.py plan
<task>` lists the stages and `loop.py plan <task> <stage>` prints the prompt.

1. **Interview.** The agent questions the human until the goal is clear.
   Output: `notes.md`.
2. **PRD.** Requirements that can be checked. Output: `prd.md`.
3. **Architecture.** Where the change goes and why. Output: `architecture.md`.
4. **Stories.** Small, ordered stories with acceptance criteria, added to
   `task.json`.

Small tasks and bugfixes skip to stage 4. The human then reads `BOARD.md` and
runs `loop.py approve <task>`. The loop does not start before that.

## Phase 2: implement, by agents

`loop.py run <task>` does this. To do it by hand inside an agent session,
follow the same steps. The files under `.loop/<task>/` are the state.

For the first story in `task.json` that is not `done`:

1. Set its status to `building` and add one to `attempts`. Note the current
   commit as the story's base.
2. Build it by following `steps/<build step>.md` with the story as context.
   Use a fresh subagent, so each story starts with a clean context.
   `loop.py prompt <task>` prints the full prompt.
3. Run the task's check command. If it fails, go to step 6.
4. Set the status to `reviewing`. For each entry in `reviews`, follow that step
   file in a fresh subagent. Each writes
   `reviews/<story>-a<attempt>-<step>.md` starting with `VERDICT: pass` or
   `VERDICT: fail`.
5. If every blocking review passed, set the status to `done`, commit the story
   on the task branch, push if the task says so, and take the next story.
6. Otherwise go back to step 1 with the failed check output or the review files
   as input. When `attempts` reaches `maxAttempts`, set the status to `blocked`
   and stop. Tell the human what blocks it.

After every status change, run `loop.py status <task>` to refresh `BOARD.md`,
and add a line to the log in `progress.md`.

Rules:

- One story at a time, in order.
- The builder never reviews its own work.
- Only the human widens the scope. New ideas go under "Follow-ups" in
  `progress.md`.
- Agents commit only passed stories, and only on the task branch.
