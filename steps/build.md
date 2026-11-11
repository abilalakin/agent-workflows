# Build one story

You are one step of a loop. A fresh agent runs each step, so the files are your
only memory. Do the one story in the Context below, then stop.

1. Read the progress log, mainly "Lessons". Read the project's own agent guide
   if it has one (AGENTS.md, CLAUDE.md or similar).
2. Write a test for each acceptance criterion. Run the tests and see the new
   ones fail.
3. Write the smallest change that makes them pass. Run the check command until
   it exits 0.
4. Append to the progress log:
   - under "Lessons": anything a later step needs to know about this codebase.
   - under "Follow-ups": problems you saw that this story does not cover.

Scope rules:

- Do only what the acceptance criteria ask. A new rule, feature or spec change
  that the criteria do not name is a follow-up, not part of this story.
- Keep what worked before working.
- Leave `task.json` and `BOARD.md` alone. The loop updates them.
