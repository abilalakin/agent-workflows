# 01 Review workflow

## What we tried

A read-only review of `apps/todo-cli` with the `Workflow` tool. The script is
`review.workflow.js`. Two finder agents each take one lens (correctness,
simplification). Every finding then goes to one skeptic agent that is told to
refute it. Lenses, the app path, the cap per lens and the models are all
`args`, so the same script can run with other lenses later, for example a
custom code-review or code-simplification skill prompt.

Run: Haiku for every agent, 3 findings max per lens.

## What happened

- 7 agents, 40 seconds wall clock. 2 finders, 5 skeptics.
- 5 findings, 4 confirmed, 1 refuted. See `findings.md`.
- The skeptics did real work: they ran both CLIs with throwaway data files and
  reproduced the claims. The refuted one was refuted on spec grounds, with a
  clear reason.
- The best catch was a contradiction inside SPEC.md that would have blocked
  story S3. Found by the simplification finder, not the correctness one, so
  lenses leak into each other. That is fine.
- Haiku was enough for a 60-line app. Finders wrote exact file and line
  references and said how to reproduce.
- A first run with Sonnet skeptics was stopped early to switch to Haiku, so no
  comparison data.

## Rough cost

| What | Tokens |
|---|---|
| Whole run | 305k |
| Per agent | 41k to 47k |

Almost all of it is fixed per-agent overhead: system prompt, CLAUDE.md and
AGENTS.md, reading the app. The skeptic for a one-line claim cost the same as
a finder. With Haiku the run is cents, not dollars. The lesson for the Ralph
loop: cost scales with agent count, not with work done, so prefer fewer agents
that each do a full story over many tiny ones.

## Use again?

Yes, as the review stage after each Ralph story. Changes before that:

- Pass the diff or the story id in `args`, so finders review only the change.
- Add a severity field to the finding schema, so low-severity items do not
  block a story.
- Keep the skeptic step. It cut one plausible-sounding finding and added
  reproduction steps to the others.
