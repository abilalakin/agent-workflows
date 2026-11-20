# The process

Two phases. The human leads the first. The loop runs the second.

## Phase 1: plan, with the human

Run each plan stage in a chat with the human. `loop.py plan <task>` lists the
stages, and `loop.py plan <task> <stage>` prints the prompt for one.

1. **Interview.** Question the human until the goal is clear. Output: `notes.md`.
2. **PRD.** Requirements that can be checked. Output: `prd.md`.
3. **Architecture.** Where the change goes and why. Output: `architecture.md`.
4. **Stories.** Small, ordered stories with acceptance criteria, added with
   `loop.py add`.

Small tasks and bugfixes skip to stage 4. The human then reads `BOARD.md` and
runs `loop.py approve <task>`. Nothing is built before that.

## Phase 2: build, by the loop

`loop.py run <task>` takes the stories in order. For each one:

1. **Build.** A fresh agent follows the build step for this story.
2. **Check.** The loop runs every check. A failure goes to step 5.
3. **Review.** A fresh agent per review step writes a review file that starts
   with `VERDICT: pass` or `VERDICT: fail`.
4. **Deliver.** If every blocking review passed, the story is `done`. The loop
   commits it, or a fresh agent follows the task's deliver step. After a
   deliver step, another fresh agent reviews the branch, the commit and the
   PR. A failed delivery review goes back to a new delivery agent once. If the
   delivery still fails, the loop stops and retries it on the next run.
5. **Retry.** Otherwise a new builder gets the failed check output or the
   review files. After `maxAttempts` the story is `blocked` and the loop stops.

The loop writes every status change to `task.json`, `BOARD.md` and
`progress.md`.

## Rules

- One story at a time, in order.
- The builder never reviews or delivers its own work.
- Only the human approves a plan, widens the scope, or resets a blocked story.
  New ideas go under "Follow-ups" in `progress.md`.
- Only passed stories are delivered. Files that were changed before the task
  stay out of the commits. Nothing is merged.

## Without `loop.py run`

If the loop cannot be started, do phase 2 by hand and keep the same rules. Use
a fresh subagent for each step. `loop.py prompt <task> [step]` prints the
prompt, `loop.py check <task>` runs the checks, and
`loop.py set <task> <story> <status>` records each change.
