# Fix one bug

You are one step of a loop. A fresh agent runs each step, so the files are your
only memory. Fix the one bug in the Context below, then stop.

1. Read the progress log, mainly "Lessons".
2. Reproduce the bug with a failing test. If you cannot reproduce it, write
   what you tried under "Follow-ups" in the progress log and stop.
3. Find the root cause. Say it in one or two sentences in the progress log.
4. Fix the cause with the smallest change. The new test passes and the check
   command exits 0.
5. Add any lesson for later steps under "Lessons".

Scope rules:

- Fix this bug only. Other problems you see go under "Follow-ups".
- Leave `task.json` and `BOARD.md` alone. The loop updates them.
