# Findings from run wf_17aa0ce7-ca2 (2026-11-09, Haiku)

Confirmed by a skeptic agent. Each one was reproduced, not just read.

1. **TypeScript `add` ignores extra arguments and accepts flags as titles.**
   `typescript/todo.ts:37`. `add Buy milk` saves "Buy". `add --due 2026-11-10`
   saves a task titled "--due". Python rejects both with exit 2. Spec says both
   must write the same JSON for the same commands.
2. **Spec contradiction: `max(id)+1` vs "ids are never reused".** `SPEC.md`
   data-file rule vs S3 and S6. Fixed in SPEC.md after this run: S3 must add a
   stored counter.
3. **`check-compat.sh` repeats the compare block twice.** Lines 8-13 and 15-20.
   Each new command would add more copies. Low severity.
4. **TypeScript `main()` loads the data file before validating the command.**
   `typescript/todo.ts:32`. A corrupt file makes `todo bogus` throw a JSON error
   instead of printing usage. Python is fine because argparse runs first. Low
   severity.

Refuted:

- **Python and TypeScript write different bytes for non-ASCII titles.** True at
  the byte level (`ensure_ascii`), but both sides read each other's file and
  list the same text. The spec does not ask for byte-identical files. If we
  want that, say so in SPEC.md and set `ensure_ascii=False`.

Items 1, 3 and 4 are left in the code on purpose. They are input for the Ralph
loop in experiment 02.
