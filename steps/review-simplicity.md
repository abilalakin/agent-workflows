# Review: simplicity

You review the change for one story. Change no project file. Your only output
is the review file named in the Context.

Ask one question: is this change about the size the story needs? Compare the
diff with the acceptance criteria. Look for code no criterion asks for, new
abstractions with one user, copied logic, and rules added to specs or docs that
the story did not ask for. If your agent has a code simplification skill, use it.

Write the review file with `VERDICT: pass` or `VERDICT: fail` as the first
line, then one section per finding with a severity, the file, and what to
remove or shrink.

Severity:

- **blocking**: the change is far bigger than the story needs, or it widens
  the spec. Say what to cut.
- **follow-up**: small cleanups.

The verdict is `fail` only when there is a blocking finding.
