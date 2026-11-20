# Review: delivery

A story was just handed over. Check that the handover is right. Change nothing:
no code, no commits, no PR edits. Your only output is the review file named in
the Context.

Look at what is really there, with the project's git and PR tools. Do not
trust the delivery result file alone.

1. **Branch.** The story is on its own branch. That branch starts from the
   story before it, or from the task's starting branch for the first story.
2. **Commit.** It holds this story's changes and the task folder, and nothing
   else. None of the files that must stay uncommitted are in it. Its title
   matches the Context.
3. **Push.** The remote has the same commit as the local branch.
4. **PR.** There is one open PR for this branch. It targets the branch from
   point 1. Its title matches, and its body lists the acceptance criteria.
5. **Working tree.** No story changes are left uncommitted.
6. **Result file.** It holds the link of that PR.

If the project's deliver step has its own rules, check against those instead.

Write the review file with `VERDICT: pass` or `VERDICT: fail` as the first
line, then one section per finding: what is wrong, how you saw it, and how to
fix it. Any point above that does not hold is blocking.
