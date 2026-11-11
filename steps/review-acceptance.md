# Review: acceptance

You review one story. Change no project file. Your only output is the review
file named in the Context.

1. Look at the change for this story.
2. Run the check command yourself.
3. Test each acceptance criterion yourself. Trust what you run, not what the
   builder wrote.
4. Check that things that worked before the story still work.

Write the review file in this shape:

```
VERDICT: pass
```
or `VERDICT: fail` as the first line, then one section per finding with
a severity, the file, what is wrong, and how to see it.

Severity:

- **blocking**: an acceptance criterion is not met, the check fails, or
  something that worked before the story is now broken.
- **follow-up**: real, but outside this story's criteria.

The verdict is `fail` only when there is a blocking finding. Follow-ups never
fail a story.
