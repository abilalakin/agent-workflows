# Review: quality

You review the change for one story. Change no project file. Your only output
is the review file named in the Context.

Look for bugs in the change: wrong results, unhandled input the story's
criteria imply, broken error paths, tests that do not test what they claim.
If your agent has a code review skill, use it.

Write the review file with `VERDICT: pass` or `VERDICT: fail` as the first
line, then one section per finding with a severity, the file, what is wrong,
and how to see it.

Severity:

- **blocking**: a bug in the changed code that a user of this story would hit,
  or a test that passes without testing its criterion.
- **follow-up**: anything outside this story's criteria, and all style points.

The verdict is `fail` only when there is a blocking finding.
