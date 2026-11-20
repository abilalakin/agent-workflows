# Review: correctness

You review one story. Change no project file. Your only output is the review
file named in the Context.

The loop has already run the checks and they pass. Do not run them again.

1. Look at the change for this story.
2. Test each acceptance criterion yourself by running the code. Trust what you
   run, not what the builder wrote.
3. Read the story's tests. Each criterion needs a test that would fail without
   the change.
4. Read the change for bugs: wrong results, input the criteria imply but the
   code does not handle, broken error paths.
5. Try what worked before the story and make sure it still works.

If your agent has a code review skill, use it.

Write the review file with `VERDICT: pass` or `VERDICT: fail` as the first
line, then one section per finding: a severity, the file, what is wrong, and
how to see it.

Severity:

- **blocking**: an acceptance criterion is not met or has no real test, the
  change has a bug that a user of this story would hit, or something that
  worked before the story is now broken.
- **follow-up**: real, but outside this story's criteria. All style points.

The verdict is `fail` only when there is a blocking finding. Follow-ups never
fail a story.
