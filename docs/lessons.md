# Lessons behind the design

These come from two experiments run on a toy app before this tool existed. The
experiment code is in the git history.

- **Reviews need a scope rule.** With no rule, reviewers marked every
  difference as high, and the retry grew a 51-line file to 240 lines for two
  small stories. So a finding blocks only when it breaks an acceptance
  criterion or something that worked before.
- **Simplicity needs a veto.** A reviewer that only suggests cleanups loses to
  one that can block. So the simplicity step can fail a story that is far
  bigger than it needs to be.
- **Builders must not widen the spec.** One builder wrote a broad new rule into
  the spec, and the reviewers then enforced it. New rules are follow-ups.
- **Do not trust the builder's report.** The loop runs the check command
  itself, and the acceptance reviewer tests each criterion again. This caught a
  real regression that the builder's own tests missed.
- **Retry with the review text works.** A fresh builder fixed a rejected story
  from the review file alone.
- **Cost follows agent count, not work done.** Each agent paid about the same
  fixed cost to load context. Two reviewers per story made review two thirds of
  the bill. So profiles differ in how many reviews they run.
- **A small model finds real problems on small code.** A cheap model was
  enough for review on a 60-line app. Try the cheap one first.
