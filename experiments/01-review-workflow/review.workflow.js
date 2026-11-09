export const meta = {
  name: 'review-app',
  description: 'Read-only review of an app folder: finders per lens, one skeptic per finding',
  phases: [
    { title: 'Find', detail: 'one finder per lens' },
    { title: 'Verify', detail: 'one skeptic per finding, told to refute' },
  ],
}

// Config comes from args so the same script serves different apps and lenses.
// args: { app, lenses: [{ key, prompt }], maxPerLens, finderModel, skepticModel }
const app = args?.app ?? 'apps/todo-cli'
const maxPerLens = args?.maxPerLens ?? 3
const finderModel = args?.finderModel ?? 'haiku'
const skepticModel = args?.skepticModel ?? 'haiku'
const lenses = args?.lenses ?? [
  {
    key: 'correctness',
    prompt: 'Bugs, behaviour that differs from SPEC.md, and places where the Python and TypeScript versions behave differently for the same input.',
  },
  {
    key: 'simplification',
    prompt: 'Code that is more complex than the spec needs: duplicated logic, dead branches, awkward structure that would slow down the next story.',
  },
]

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'integer' },
          detail: { type: 'string', description: 'What is wrong and how to see it' },
        },
        required: ['title', 'file', 'line', 'detail'],
      },
    },
  },
  required: ['findings'],
}

const VERDICT = {
  type: 'object',
  properties: {
    confirmed: { type: 'boolean' },
    reason: { type: 'string' },
  },
  required: ['confirmed', 'reason'],
}

const finderPrompt = (lens) => `You are reviewing the folder ${app} in this repo. Read-only: do not create or change any file.
Read SPEC.md, check.sh, check-compat.sh, and every source and test file under python/ and typescript/.
Lens: ${lens.key}. Look for: ${lens.prompt}
Report at most ${maxPerLens} findings. Each must point at a real file and line and say how to observe the problem. Skip style preferences. If you find nothing, return an empty list.`

const skepticPrompt = (f, lens) => `You are a skeptic checking one review finding about ${app} in this repo. Read-only: do not change any file.
Finding (${lens.key}): ${f.title}
File: ${f.file} line ${f.line}
Claim: ${f.detail}
Read the file and SPEC.md. Run commands if that settles it (./check.sh in ${app} is fine). Try hard to refute the claim. Set confirmed=false when the claim is wrong, not observable, or already covered by the spec or tests. Default to confirmed=false if uncertain.`

const results = await pipeline(
  lenses,
  (lens) => agent(finderPrompt(lens), { label: `find:${lens.key}`, phase: 'Find', schema: FINDINGS, model: finderModel }),
  (found, lens) => {
    const all = found?.findings ?? []
    const kept = all.slice(0, maxPerLens)
    if (all.length > kept.length) log(`${lens.key}: dropped ${all.length - kept.length} findings over the cap`)
    log(`${lens.key}: ${kept.length} findings to verify`)
    return parallel(kept.map((f) => () =>
      agent(skepticPrompt(f, lens), { label: `verify:${f.file}:${f.line}`, phase: 'Verify', schema: VERDICT, model: skepticModel })
        .then((v) => ({ lens: lens.key, ...f, verdict: v }))
    ))
  },
)

const flat = results.flat().filter(Boolean)
return {
  confirmed: flat.filter((f) => f.verdict?.confirmed),
  refuted: flat.filter((f) => f.verdict && !f.verdict.confirmed),
  unverified: flat.filter((f) => !f.verdict),
}
