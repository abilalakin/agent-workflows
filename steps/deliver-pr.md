# Deliver: one branch and one PR per story

A story has passed its checks and reviews. Its changes are in the working tree,
not yet committed. Hand them over. Change no code.

1. Note the branch you are on. It is the base for this story.
2. Create the branch `loop/<task>/<story id>` from where you are. The changes
   come along.
3. Commit the story's changes with the title from the Context. Stage only files
   this story changed, plus the task folder.
4. Push the branch.
5. Open a PR that targets the base branch from step 1. Use the title from the
   Context. In the body, list the acceptance criteria and say that the checks
   and reviews passed. Use the project's own tool for PRs.
6. Stay on the new branch. The next story builds on top of it.
7. Write the PR link to the result file named in the Context.

If the project has its own rules for branches, commits or PRs, follow those.
If a step fails, stop and say why. Do not force anything.
